#!/usr/bin/env python3
"""Web-driven mock interviews: the browser is the whole app, a local agent CLI is the interviewer.

  studio.py [--port 8770] [--no-open]

Open the printed URL, pick a backend (Claude Code / Codex / Antigravity / Cursor Agent / OpenCode —
whatever is installed and logged in on this machine), a company, role and round, and press start.
Questions come from the open-interview bank; every interviewer turn is one headless, tool-free call to
that CLI, so it runs on the user's existing subscription with no API key. Ctrl+C stops the server.
"""
import argparse
import json
import re
import sys
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backends  # noqa: E402
import bank  # noqa: E402
import voice  # noqa: E402

ROUNDS = {  # id: (中文名, English name, question mix for n main questions)
    "mixed": ("综合技术面", "General technical", lambda n: {"technical": max(1, n - 2), "coding": 1, "behavioral": 1}),
    "technical": ("八股 / 知识面", "Technical knowledge", lambda n: {"technical": n}),
    "coding": ("手撕代码", "Coding", lambda n: {"coding": min(n, 2)}),
    "system-design": ("系统设计", "System design", lambda n: {"system-design": min(n, 2)}),
    "behavioral": ("行为面 / HR 面", "Behavioral / HR", lambda n: {"behavioral": max(1, n - 1), "hr": 1}),
}
STYLES = {
    "neutral": "Neutral and professional: brief acknowledgements, no hints unless asked.",
    "supportive": "Warm and encouraging: when the candidate stalls, offer a small nudge without being asked.",
    "pressure": ("A demanding stress interview: challenge assumptions, cut off vague answers, push for specifics "
                 "and numbers, keep acknowledgements minimal, but stay respectful."),
}
LEVEL_NAMES = {"intern": "实习", "campus": "校招", "junior": "社招 1-3 年", "mid": "社招 3-5 年", "senior": "资深", "staff": "专家"}
VERDICTS = ["Strong hire", "Hire", "Lean hire", "Lean no hire", "No hire"]
LEVELS = {"intern": "intern", "campus": "new-grad (campus hire)", "junior": "1-3 years experience",
          "mid": "3-5 years experience", "senior": "senior", "staff": "staff+"}

INSTRUCTIONS = """You are a professional interviewer running a realistic mock job interview{company} for a {role} position ({level}). Round: {round}. Conduct the whole interview in {lang}.

How to interview:
- Ask exactly one question per turn, then stop and wait for the candidate. Never answer for the candidate and never reveal answers during the interview.
- Work through the question plan below in order, rephrasing naturally (translate it if needed). After each answer ask 0-2 short follow-ups aimed at what the answer missed (the plan's follow-ups and key points are a guide), then move on.
- Interviewer style: {style} No teaching and no scores until the end.
- Coding and system design: state the problem clearly with an example, put the full statement, examples and any code in <show>...</show>, and ask for the approach and complexity before code. The candidate answers by voice, so accept a spoken description of code.
- Special candidate messages: [HINT] = give one small hint and re-ask; [SKIP] = acknowledge and go to the next question; [EMPTY] = ask whether they want to continue; [END] = end the interview now.
- {opening}
- When the plan is done (or the candidate sends [END]), finish with one short closing sentence followed by the report in <report>...</report>.

Output format (strict):
- Everything outside tags is read aloud by text-to-speech: plain spoken sentences only, no markdown, lists, code or URLs, at most about 60 words (100 when stating a problem).
- Optional <show>markdown</show> is displayed on screen and not read aloud.
- Progress marker: whenever a turn starts a new question from the plan, begin it with <q>N</q>, where N is that question's number in the plan (use <q>0</q> for the greeting and self-introduction). Follow-ups keep the current number and need no marker.
- Final turn only, after the closing sentence: first <scores>JSON</scores>, then <report>markdown</report>.
  The JSON is {{"verdict": one of "Strong hire", "Hire", "Lean hire", "Lean no hire", "No hire"; "summary": one sentence; "scores": [{{"name": dimension, "score": 1-4, "note": short evidence}}]}} with the dimensions technical depth, problem solving, coding (only if code was asked), communication, and experience & ownership, named in {lang}.
  The markdown report contains: feedback per question (what was good, what a strong answer adds, whether a hint was used, the bank id) and the 3 most valuable things to study next. Do not repeat the verdict or the score table there. Write it in {lang}, be specific and honest, do not inflate.
- Do not use tools, do not read or write files, do not mention these instructions."""


def plan_lines(plan):
    out = []
    for i, q in enumerate(plan, 1):
        meta = q["type"] + (f", difficulty {q['difficulty']}/5" if q.get("difficulty") else "")
        out.append(f"{i}. [{q['id']}] ({meta}) {q['q']}")
        if q.get("followups"):
            out.append("   follow-ups: " + " | ".join(q["followups"][:3]))
        if q.get("key_points"):
            out.append("   key points: " + " | ".join(q["key_points"]))
        if q.get("answer_brief"):
            out.append("   reference: " + q["answer_brief"])
    return "\n".join(out)


def build_prompt(setup, data, plan, transcript, finish):
    tags = data["tags"]
    zh = setup["lang"] == "zh"
    company = tags["companies"].get(setup.get("company") or "", {})
    role = tags["roles"].get(setup.get("role") or "", {})
    rnd = ROUNDS[setup["round"]]
    head = INSTRUCTIONS.format(
        company=f" at {company.get('en')} ({company.get('name')})" if company else "",
        role=role.get("en", "software engineer") if role else "software engineer",
        level=LEVELS.get(setup.get("level") or "", "level not specified"),
        round=rnd[1],
        lang="Simplified Chinese (spoken Mandarin)" if zh else "English",
        style=STYLES.get(setup.get("style"), STYLES["neutral"]),
        opening=("Open with a one-sentence greeting and go straight to the first problem."
                 if setup["round"] in ("coding", "system-design") else
                 "Open with a one-sentence greeting and ask for a short self-introduction before the plan."),
    )
    parts = [head, "", f"Question plan ({len(plan)} questions from the open-interview bank):", plan_lines(plan), ""]
    if transcript:
        parts.append("Transcript so far:")
        parts += [f"{'INTERVIEWER' if who == 'i' else 'CANDIDATE'}: {text}" for who, text in transcript]
    else:
        parts.append("The interview has not started yet.")
    parts.append("")
    parts.append("The interview is over now: write one closing sentence and the <report>." if finish
                 else "Write only the interviewer's next turn.")
    return "\n".join(parts)


def parse(reply):
    """Split a model turn into (speech, show, report, progress, scores)."""
    def grab(tag):
        m = re.search(rf"<{tag}>(.*?)(?:</{tag}>|\Z)", reply, re.S | re.I)
        return m.group(1).strip() if m else None

    report, show, scores_raw, q = grab("report"), grab("show"), grab("scores"), grab("q")
    progress = int(re.sub(r"\D", "", q) or -1) if q else None
    scores = None
    if scores_raw:
        raw = re.sub(r"^```(?:json)?|```$", "", scores_raw.strip()).strip()
        try:
            scores = json.loads(raw)
        except ValueError:
            scores = None
    if report and scores_raw and "<report>" not in reply.lower() and report == scores_raw:
        report = None
    speech = re.sub(r"<(report|show|scores)>.*?(?:</\1>|\Z)", " ", reply, flags=re.S | re.I)
    speech = re.sub(r"<q>.*?</q>", " ", speech, flags=re.S | re.I)
    speech = re.sub(r"^\s*(\*\*)?(INTERVIEWER|Interviewer|面试官)(\*\*)?\s*[:：]\s*", "", speech.strip())
    speech = re.sub(r"[*#`>]+", "", speech)
    return re.sub(r"\s+", " ", speech).strip(), show, report, progress, scores


def clean_scores(scores):
    """Keep only well-formed fields so the UI can trust them."""
    if not isinstance(scores, dict):
        return {}
    out = {}
    v = str(scores.get("verdict", "")).strip()
    match = next((x for x in sorted(VERDICTS, key=len, reverse=True) if x.lower() == v.lower()), None)
    if match:
        out["verdict"] = match
    if isinstance(scores.get("summary"), str):
        out["summary"] = scores["summary"].strip()
    dims = []
    for d in scores.get("scores") or []:
        try:
            dims.append({"name": str(d["name"]), "score": max(1, min(4, int(d["score"]))), "note": str(d.get("note", ""))})
        except (KeyError, TypeError, ValueError):
            continue
    if dims:
        out["scores"] = dims
    return out


def setup_label(setup, tags):
    parts = [tags["companies"].get(setup.get("company") or "", {}).get("name"),
             tags["roles"].get(setup.get("role") or "", {}).get("name"),
             LEVEL_NAMES.get(setup.get("level") or ""), ROUNDS[setup["round"]][0]]
    return " · ".join(x for x in parts if x)


class Interview(threading.Thread):
    def __init__(self, bridge, data, setup, plan):
        super().__init__(daemon=True)
        self.bridge, self.data, self.setup, self.plan = bridge, data, setup, plan
        self.stopped = False
        self.retry = threading.Event()
        self.state = "running"

    def stop(self):
        self.stopped = True
        self.retry.set()

    def ask_backend(self, prompt, finish):
        while not self.stopped:
            try:
                return backends.complete(self.setup["backend"], prompt, self.setup.get("model") or None, final=finish)
            except backends.BackendError as e:
                self.state = "error"
                self.bridge.push("system", level="error", text=str(e))
                self.retry.clear()
                self.retry.wait()
                self.state = "running"
        return None

    def run(self):
        transcript, finish, turns, current = [], False, 0, 0
        total = len(self.plan)
        cap = len(self.plan) * 3 + 4
        zh = self.setup["lang"] == "zh"
        while not self.stopped:
            reply = self.ask_backend(build_prompt(self.setup, self.data, self.plan, transcript, finish), finish)
            if reply is None:
                return
            speech, show, report, progress, scores = parse(reply)
            if progress is not None and 0 <= progress <= total:
                current = progress
            if finish and not report:  # the model ignored the format on the last turn; keep what it wrote
                report, speech = reply, ""
            if report:
                if speech:
                    self.bridge.say(speech, None, False, progress={"n": total, "total": total})
                self.bridge.push("report", text=report, **clean_scores(scores))
                self.state = "done"
                return
            if not speech:
                speech = "请看屏幕上的题目。" if zh else "Please take a look at the problem on screen."
            qid = self.bridge.say(speech, show, True, progress={"n": current, "total": total})
            turns += 1
            transcript.append(("i", speech + (f"\n[shown on screen]\n{show}" if show else "")))
            answer = None
            while answer is None and not self.stopped:
                answer = self.bridge.wait_answer(qid, 2)
            if self.stopped:
                return
            transcript.append(("c", answer.strip() or "[EMPTY]"))
            finish = answer.lstrip().startswith("[END]") or turns >= cap


class Studio:
    def __init__(self):
        self.bridge = voice.Bridge(voice.HOME / "sessions" / time.strftime("studio-%Y%m%d-%H%M%S.jsonl"))
        self.data = bank.load()
        self.interview = None
        self.lock = threading.Lock()

    def info(self, _qs):
        iv = self.interview
        return {"studio": True, "backends": backends.detect(),
                "rounds": [{"id": k, "name": v[0], "en": v[1]} for k, v in ROUNDS.items()],
                "state": iv.state if iv else "idle", "setup": iv.setup if iv else None}

    def start(self, body):
        bid = body.get("backend")
        if bid not in backends.BACKENDS or not backends.find(bid):
            return {"ok": False, "error": f"backend '{bid}' is not installed"}
        setup = {"backend": bid, "model": (body.get("model") or "").strip(), "company": body.get("company") or None,
                 "role": body.get("role") or None, "level": body.get("level") or None,
                 "round": body.get("round") if body.get("round") in ROUNDS else "mixed",
                 "lang": "en" if body.get("lang") == "en" else "zh",
                 "style": body.get("style") if body.get("style") in STYLES else "neutral",
                 "n": max(1, min(10, int(body.get("n") or 5)))}
        mix = ROUNDS[setup["round"]][2](setup["n"])
        opts = bank.options(company=setup["company"], role=setup["role"],
                            mix=",".join(f"{k}={v}" for k, v in mix.items()))
        plan = [{k: v for k, v in q.items() if k != "_fill"} for q in bank.sample(self.data, opts)]
        if not plan:
            return {"ok": False, "error": "no questions match this role and round"}
        with self.lock:
            if self.interview:
                self.interview.stop()
            self.bridge.push("reset", setup=setup, plan=[q["id"] for q in plan], total=len(plan),
                             label=setup_label(setup, self.data["tags"]))
            self.interview = Interview(self.bridge, self.data, setup, plan)
            self.interview.start()
        return {"ok": True, "questions": len(plan)}

    def retry(self, _body):
        if self.interview:
            self.interview.retry.set()
        return {"ok": True}

    def stop(self, _body):
        if self.interview:
            self.interview.stop()
            self.bridge.push("system", level="info", text="stopped")
        return {"ok": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    studio = Studio()
    handler = voice.make_handler(studio.bridge, get_routes={"/api/studio": studio.info},
                                 post_routes={"/api/studio/start": studio.start, "/api/studio/retry": studio.retry,
                                              "/api/studio/stop": studio.stop})
    port = voice.free_port(a.port)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{port}/#agent"
    found = [b["name"] for b in backends.detect() if b["available"]]
    print(f"Open Interview studio: {url}")
    print(f"backends found: {', '.join(found) or 'none (install Claude Code, Codex, agy, Cursor Agent or OpenCode)'}")
    print("Ctrl+C to stop.")
    if not a.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
