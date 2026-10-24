#!/usr/bin/env python3
"""allclose · 手撕: hand-code ML / LLM interview problems, judged on your own machine.

  allclose.py list [--track ml|dl|llm] [--difficulty easy|medium|hard] [--json]
  allclose.py show ID [--lang en]          print the problem statement (ID = slug or number)
  allclose.py pull ID [--force]            write the starter code to ~/allclose/ID.py
  allclose.py test ID [FILE] [--run] [--json] [--lang en]
                                           judge FILE (default ~/allclose/ID.py); --run = sample cases only.
                                           Exit 0 = accepted, 1 = not yet, 2 = could not judge.
  allclose.py hint ID [--all]              next hint (or all of them)
  allclose.py followups ID                 interviewer follow-up questions to ask once it passes
  allclose.py solution ID                  the reference solution
  allclose.py progress                     what you have passed so far
  allclose.py check [ID ...]               maintainers: reference passes; starter and every wrong.py variant fail

Your code runs in a separate local process, never on a server. Judging needs numpy: the current
python if it has it, else `uv run --with numpy`, else set ALLCLOSE_PYTHON=/path/to/python.
Files live in ~/allclose (override with ALLCLOSE_HOME).
"""
import argparse
import ast
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PROBLEMS = SKILL / "problems"
INDEX = SKILL / "data" / "problems.json"
RUNNER = HERE / "runner.py"
TRACKS = {"ml": ("机器学习基础", "ML basics"), "dl": ("深度学习", "Deep learning"), "llm": ("大模型", "LLM")}
LEVELS = {"easy": ("简单", "Easy"), "medium": ("中等", "Medium"), "hard": ("困难", "Hard")}
STATUS = {
    "accepted": ("通过", "Accepted"),
    "wrong_answer": ("答案错误", "Wrong Answer"),
    "runtime_error": ("运行出错", "Runtime Error"),
    "time_limit": ("超时", "Time Limit Exceeded"),
    "compile_error": ("没通过检查", "Compile Error"),
    "internal_error": ("评测器出错", "Judge Error"),
    "env_error": ("缺少 numpy", "numpy missing"),
}
_lock = threading.Lock()
_cache = {}


# ---------------- problems ----------------

def load():
    mtime = INDEX.stat().st_mtime
    if _cache.get("mtime") != mtime:
        _cache.update(mtime=mtime, data=json.loads(INDEX.read_text(encoding="utf-8")))
    return _cache["data"]


def get(pid):
    pid = str(pid).strip()
    for p in load()["problems"]:
        if p["id"] == pid or str(p["no"]) == pid:
            return p
    raise KeyError(pid)


def tr(pair, lang):
    return pair[1] if lang == "en" else pair[0]


def pad(text, width):
    """ljust by terminal columns: CJK characters take two."""
    cols = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)
    return text + " " * max(0, width - cols)


# ---------------- workspace & progress ----------------

def home():
    return Path(os.environ.get("ALLCLOSE_HOME", Path.home() / "allclose"))


def draft_path(pid):
    return home() / f"{pid}.py"


def read_draft(pid):
    path = draft_path(pid)
    return path.read_text(encoding="utf-8") if path.is_file() else None


def save_draft(pid, code):
    path = draft_path(pid)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".py.tmp")
    tmp.write_text(code, encoding="utf-8")
    tmp.replace(path)
    return path


def progress():
    path = home() / ".progress.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def record(pid, res):
    with _lock:
        prog = progress()
        p = prog.setdefault(pid, {"submits": 0, "passed": False})
        p["submits"] += 1
        p["last"] = time.strftime("%Y-%m-%d %H:%M")
        p["last_status"] = res["status"]
        if res["status"] == "accepted":
            p.setdefault("first_passed", p["last"])
            p["passed"] = True
            p["best_ms"] = min(res.get("ms") or 0, p.get("best_ms", float("inf")))
        path = home() / ".progress.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(prog, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)


# ---------------- judging ----------------

def python_cmd():
    """The command that runs runner.py with numpy importable, or None."""
    if "py" in _cache:
        return _cache["py"]
    cmd = None
    if os.environ.get("ALLCLOSE_PYTHON"):
        cmd = shlex.split(os.environ["ALLCLOSE_PYTHON"])
    elif importlib.util.find_spec("numpy"):
        cmd = [sys.executable]
    elif shutil.which("uv"):
        cmd = [shutil.which("uv"), "run", "--no-project", "--quiet", "--with", "numpy", "python"]
    _cache["py"] = cmd
    return cmd


def env_note(lang="zh"):
    cmd = python_cmd()
    if cmd is None:
        return None
    return "uv + numpy" if "uv" in Path(cmd[0]).name else Path(cmd[0]).name


def judge(pid, code, mode="submit", lang="zh", fn=None, save=False, keep_record=True):
    """Judge `code` (a string) against problem `pid`. Returns the runner's result dict plus a label."""
    p = get(pid)
    if save:
        save_draft(p["id"], code)
    cmd = python_cmd()
    if cmd is None:
        msg = ("评测需要 numpy：pip install numpy，或者装 uv（https://docs.astral.sh/uv/）让 allclose 自动准备环境"
               if lang != "en" else "Judging needs numpy: pip install numpy, or install uv (https://docs.astral.sh/uv/)")
        return {"status": "env_error", "label": tr(STATUS["env_error"], lang), "message": msg, "cases": []}
    meta = {"entry": p["entry"], "banned": p.get("banned") or [], "time_limit": p.get("time_limit") or 2}
    with tempfile.TemporaryDirectory(prefix="allclose-") as tmp:
        src = Path(tmp) / "solution.py"
        src.write_text(code, encoding="utf-8")
        out = Path(tmp) / "result.json"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
        args = cmd + [str(RUNNER), "--problem", str(PROBLEMS / p["id"]), "--meta", json.dumps(meta),
                      "--code", str(src), "--out", str(out), "--mode", mode, "--lang", lang]
        if fn:
            args += ["--fn", fn]
        t0 = time.time()
        try:
            proc = subprocess.run(args, cwd=tmp, env=env, capture_output=True, text=True,
                                  timeout=60 if mode == "run" else 180)
        except subprocess.TimeoutExpired:
            res = {"status": "time_limit", "cases": [],
                   "message": "整体运行超时" if lang != "en" else "The whole run timed out"}
        else:
            if out.exists():
                res = json.loads(out.read_text(encoding="utf-8"))
            else:
                res = {"status": "runtime_error", "cases": [],
                       "message": ((proc.stderr or proc.stdout or "").strip()[-2500:]
                                   or f"judge exited with code {proc.returncode}")}
        res["wall_ms"] = round((time.time() - t0) * 1000)
    res["label"] = tr(STATUS.get(res["status"], (res["status"], res["status"])), lang)
    res["mode"] = mode
    if keep_record and mode == "submit" and res["status"] not in ("env_error", "internal_error"):
        record(p["id"], res)
    return res


# ---------------- AI hints & follow-up questions ----------------

FOLLOWUP_N = 3


def _problem_block(p, code, lang):
    zh = lang != "en"
    title = p["title"]["en" if not zh else "zh"]
    stmt = p["statement"]["en" if not zh else "zh"].strip()
    return (f"## {'题目' if zh else 'Problem'}: {title}\n{stmt}\n\n"
            f"## {'候选人的代码' if zh else 'Candidate code'}\n```python\n{code.strip() or '# (empty)'}\n```\n")


def _result_block(result, zh):
    if not result:
        return ""
    fail = next((c for c in result.get("cases") or [] if not c.get("ok")), None)
    lines = [f"status: {result.get('status')} ({result.get('passed', 0)}/{result.get('total', 0)} cases passed)"]
    if result.get("message"):
        lines.append(str(result["message"])[:1200])
    if fail:
        lines.append(f"first failing case: {fail.get('name')}: {fail.get('msg') or ''}"[:1200])
        for k, v in (fail.get("input") or {}).items():
            lines.append(f"  {k} = {str(v)[:300]}")
        if fail.get("expected"):
            lines.append(f"  expected = {str(fail['expected'])[:300]}")
        if fail.get("got"):
            lines.append(f"  got = {str(fail['got'])[:300]}")
    return f"## {'最近一次本地评测' if zh else 'Latest local judge result'}\n" + "\n".join(lines) + "\n"


def ai_prompt(p, code, mode, history=None, result=None, lang="zh"):
    """One stateless prompt per turn: everything the model needs is in it."""
    zh = lang != "en"
    if mode == "hint":
        rules = ("你是一位耐心的大模型 / 机器学习方向面试官。候选人在做一道手撕题时卡住了，请给他一个提示。\n"
                 "规则：只给一个提示，2 到 4 句；指出最可能出错的地方，或者下一步该想什么；"
                 "不要给出完整代码，最多给一行关键表达式；代码基本为空时，提示整体思路的第一步。用中文。"
                 if zh else
                 "You are a patient ML / LLM interviewer. The candidate is stuck on a hand-coding problem; give one hint.\n"
                 "Rules: a single hint in 2-4 sentences; point at the most likely bug or the next thing to think about; "
                 "never give the full solution, at most one key expression; if the code is nearly empty, hint the first step.")
        return f"{rules}\n\n{_problem_block(p, code, lang)}\n{_result_block(result, zh)}\n" + \
            ("请直接输出提示：" if zh else "Your hint:")
    history = [h for h in (history or []) if h.get("text")]
    asked = sum(1 for h in history if h.get("role") == "interviewer")
    seeds = "\n".join(f"- {q}" for q in (p["followups"].get(lang) or p["followups"]["zh"]))
    passed = (result or {}).get("status") == "accepted"
    if zh:
        intro = ("你是一位大模型 / 机器学习方向的技术面试官，现在是“手撕代码”之后的追问环节。候选人刚在本地写完下面这道题，"
                 + ("并且通过了全部测试用例。" if passed else "但还没有通过全部测试。"))
        rules = (f"规则：一共问 {FOLLOWUP_N} 个问题，每次只问一个；像真人面试官一样口语化，每段话不超过 4 句；"
                 "问题要贴着他写的代码和这道题，考察原理、复杂度、数值稳定性、边界情况、工程优化、和 PyTorch 等框架实现的区别；"
                 "不要直接给出完整代码答案。")
        if asked == 0:
            now = f"现在开场：先用一两句话点评他的代码（点出一个具体的地方），然后问第 1 个问题（共 {FOLLOWUP_N} 个）。"
        elif asked < FOLLOWUP_N:
            now = f"现在：先用一两句话评价他上一个回答（对在哪里，错的或漏的直接指出并给出正确要点），然后问第 {asked + 1} 个问题（共 {FOLLOWUP_N} 个）。"
        else:
            now = ("问题已经问完。现在：先评价他最后一个回答，然后输出 <done/>，接着用两三句话总结这次手撕和追问的表现、"
                   "给出一条最值得改进的建议，最后输出 <score>0 到 10 的整数</score>。")
        who = {"interviewer": "面试官", "candidate": "候选人"}
        talk = "\n".join(f"{who.get(h['role'], h['role'])}：{h['text']}" for h in history) or "（还没开始）"
        return (f"{intro}\n\n{_problem_block(p, code, lang)}\n{_result_block(result, zh)}\n"
                f"## 可以参考的追问方向（挑和他代码最相关的，可以改写，也可以问你自己的问题）\n{seeds}\n\n"
                f"## {rules}\n\n## 目前的对话\n{talk}\n\n{now}\n只输出面试官要说的话：")
    intro = ("You are a technical interviewer for ML / LLM roles, in the follow-up part right after a hand-coding "
             "exercise. The candidate just wrote the problem below on their own machine and "
             + ("passed every test case." if passed else "has not passed every test yet."))
    rules = (f"Rules: ask {FOLLOWUP_N} questions in total, one at a time; sound like a real interviewer, at most 4 "
             "sentences per turn; tie each question to their code and this problem (principles, complexity, numerical "
             "stability, edge cases, engineering optimizations, differences from PyTorch and other frameworks); "
             "never hand them a full code answer.")
    if asked == 0:
        now = f"Now open: one or two sentences on their code (name one specific thing), then ask question 1 of {FOLLOWUP_N}."
    elif asked < FOLLOWUP_N:
        now = (f"Now: one or two sentences assessing their last answer (what was right; state plainly what was wrong "
               f"or missing and the correct point), then ask question {asked + 1} of {FOLLOWUP_N}.")
    else:
        now = ("All questions are asked. Now assess their last answer, then output <done/>, then summarize the "
               "exercise and follow-ups in two or three sentences with the single most useful improvement, and end "
               "with <score>an integer 0-10</score>.")
    talk = "\n".join(f"{h['role'].capitalize()}: {h['text']}" for h in history) or "(not started)"
    return (f"{intro}\n\n{_problem_block(p, code, lang)}\n{_result_block(result, zh)}\n"
            f"## Follow-up directions you may use (pick what fits their code, rephrase, or ask your own)\n{seeds}\n\n"
            f"## {rules}\n\n## Conversation so far\n{talk}\n\n{now}\nOutput only what the interviewer says:")


def parse_ai(text):
    import re
    done = "<done/>" in text or "<done>" in text
    m = re.search(r"<score>\s*(\d+(?:\.\d+)?)\s*</score>", text)
    score = max(0.0, min(10.0, float(m.group(1)))) if m else None
    reply = re.sub(r"</?done/?>|<score>.*?</score>", "", text, flags=re.S).strip()
    return reply, done, score


# ---------------- HTTP routes (served by the studio) ----------------

def routes(ai=None):
    """(get_routes, post_routes) for voice.make_handler. ai(backend, model, prompt, final) -> reply text."""
    def safe(fn):
        def wrapped(arg):
            try:
                return fn(arg)
            except KeyError as e:
                return {"ok": False, "error": f"no such problem: {e.args[0]}"}
            except Exception as e:  # noqa: BLE001 - the page shows the message instead of a dead request
                return {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return wrapped

    def problems(_q):
        return {"available": True, "env": env_note(), "home": str(home()), "ai": ai is not None,
                "problems": load()["problems"], "progress": progress()}

    def draft(q):
        p = get(q.get("id", ""))
        return {"ok": True, "id": p["id"], "code": read_draft(p["id"]), "path": str(draft_path(p["id"]))}

    def save(b):
        p = get(b.get("id", ""))
        return {"ok": True, "path": str(save_draft(p["id"], str(b.get("code") or "")))}

    def run(b):
        p = get(b.get("id", ""))
        lang = "en" if b.get("lang") == "en" else "zh"
        res = judge(p["id"], str(b.get("code") or ""), "run" if b.get("mode") == "run" else "submit", lang, save=True)
        res["progress"] = progress().get(p["id"])
        return res

    def ask_ai(b):
        if ai is None:
            return {"ok": False, "error": "AI needs the studio server with a backend"}
        p = get(b.get("id", ""))
        lang = "en" if b.get("lang") == "en" else "zh"
        mode = "hint" if b.get("mode") == "hint" else "followup"
        prompt = ai_prompt(p, str(b.get("code") or ""), mode, b.get("history"), b.get("result"), lang)
        asked = sum(1 for h in b.get("history") or [] if h.get("role") == "interviewer")
        reply, done, score = parse_ai(ai(b.get("backend"), b.get("model"), prompt, mode == "followup" and asked >= FOLLOWUP_N))
        return {"ok": True, "reply": reply, "done": done, "score": score,
                "turn": min(asked + 1, FOLLOWUP_N), "total": FOLLOWUP_N}

    return ({"/api/allclose/problems": safe(problems), "/api/allclose/draft": safe(draft)},
            {"/api/allclose/save": safe(save), "/api/allclose/judge": safe(run), "/api/allclose/ai": safe(ask_ai)})


# ---------------- CLI ----------------

def statement(p, lang):
    title = p["title"].get(lang) or p["title"]["zh"]
    head = (f"#{p['no']} {title}  ·  {tr(LEVELS[p['difficulty']], lang)}  ·  {tr(TRACKS[p['track']], lang)}\n"
            f"function: {p['entry']}()   topics: {', '.join(p.get('topics') or [])}\n")
    for c in p.get("companies") or []:
        head += f"{'面经考过' if lang != 'en' else 'asked at'}: {c['name'] if lang != 'en' else c['en']}  {c['source']}\n"
    return head + "\n" + (p["statement"].get(lang) or p["statement"]["zh"]).strip() + "\n"


def print_result(p, res, lang):
    zh = lang != "en"
    mark = {"accepted": "✓"}.get(res["status"], "✗")
    print(f"≈ allclose · #{p['no']} {p['id']}  [{'运行样例' if zh and res['mode'] == 'run' else res['mode']}]")
    for c in res.get("cases", []):
        ms = f"{c['ms']:.2f} ms" if c.get("ms") is not None else "—"
        print(f"  {'✓' if c['ok'] else '✗'} {c['name']:<34} {ms:>10}")
        if not c["ok"] and c.get("msg"):
            for line in c["msg"].splitlines():
                print("      " + line)
        if not c["ok"] and c.get("input"):
            for k, v in c["input"].items():
                print(f"      {k} = " + v.replace("\n", "\n        "))
            print("      expected: " + str(c.get("expected", "")).replace("\n", "\n        "))
            if c.get("got"):
                print("      got:      " + str(c.get("got", "")).replace("\n", "\n        "))
        if c.get("stdout"):
            print("      stdout: " + c["stdout"].strip()[:400].replace("\n", "\n        "))
    if res.get("message"):
        print(res["message"])
    total = res.get("total") or len(res.get("cases", []))
    print(f"{mark} {res['label']}" + (f" · {res.get('passed', 0)}/{total}" if total else "")
          + (f" · {res['ms']:.1f} ms" if res.get("ms") else ""))


def cmd_list(a):
    prog = progress()
    rows = [p for p in load()["problems"]
            if (not a.track or p["track"] == a.track) and (not a.difficulty or p["difficulty"] == a.difficulty)]
    if a.json:
        print(json.dumps([{k: p[k] for k in ("no", "id", "title", "difficulty", "track", "topics")}
                          | {"passed": prog.get(p["id"], {}).get("passed", False)} for p in rows], ensure_ascii=False))
        return 0
    for p in rows:
        done = "✓" if prog.get(p["id"], {}).get("passed") else " "
        title = p["title"].get(a.lang) or p["title"]["zh"]
        print(f"{done} {p['no']:>3}  {p['id']:<28} {pad(tr(LEVELS[p['difficulty']], a.lang), 7)} "
              f"{pad(tr(TRACKS[p['track']], a.lang), 14)} {title}")
    passed = sum(1 for p in load()["problems"] if prog.get(p["id"], {}).get("passed"))
    print(f"\n{passed}/{len(load()['problems'])} passed · files in {home()}")
    return 0


def cmd_show(a):
    print(statement(get(a.id), a.lang))
    return 0


def cmd_pull(a):
    p = get(a.id)
    path = draft_path(p["id"])
    if path.exists() and not a.force:
        print(f"{path} already exists (use --force to overwrite)")
        return 0
    save_draft(p["id"], p["starter"])
    print(path)
    return 0


def cmd_test(a):
    p = get(a.id)
    path = Path(a.file) if a.file else draft_path(p["id"])
    if not path.is_file():
        print(f"no file at {path}; run `allclose.py pull {p['id']}` first", file=sys.stderr)
        return 2
    res = judge(p["id"], path.read_text(encoding="utf-8"), "run" if a.run else "submit", a.lang)
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print_result(p, res, a.lang)
    return 0 if res["status"] == "accepted" else 2 if res["status"] in ("env_error", "internal_error") else 1


def cmd_hint(a):
    p = get(a.id)
    hints = p["hints"].get(a.lang) or p["hints"]["zh"]
    if a.all:
        for i, h in enumerate(hints, 1):
            print(f"{i}. {h}")
        return 0
    state = home() / ".hints.json"
    try:
        seen = json.loads(state.read_text())
    except (OSError, ValueError):
        seen = {}
    k = min(seen.get(p["id"], 0), len(hints) - 1)
    print(f"{k + 1}/{len(hints)}. {hints[k]}")
    seen[p["id"]] = k + 1
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(seen))
    return 0


def cmd_followups(a):
    for i, q in enumerate(get(a.id)["followups"].get(a.lang) or get(a.id)["followups"]["zh"], 1):
        print(f"{i}. {q}")
    return 0


def cmd_solution(a):
    print(get(a.id)["solution"])
    return 0


def cmd_progress(a):
    prog = progress()
    for p in load()["problems"]:
        s = prog.get(p["id"])
        if s:
            print(f"{'✓' if s['passed'] else '·'} {p['id']:<28} submits={s['submits']} last={s['last']} {s.get('last_status', '')}")
    return 0


def wrong_variants(pid):
    path = PROBLEMS / pid / "wrong.py"
    if not path.exists():
        return path, []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return path, [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]


def cmd_check(a):
    """Every reference must pass; the starter and every buggy variant in wrong.py must be caught."""
    problems = [get(i) for i in a.ids] if a.ids else load()["problems"]
    bad = 0
    for p in problems:
        sol = (PROBLEMS / p["id"] / "solution.py").read_text(encoding="utf-8")
        line = []
        r = judge(p["id"], sol, "submit", "en", keep_record=False)
        ok_ref = r["status"] == "accepted"
        line.append(f"ref {'ok' if ok_ref else 'FAIL ' + r['status'] + ' ' + str(r.get('message') or [c['msg'] for c in r['cases'] if not c['ok']][:1])}")
        r = judge(p["id"], p["starter"], "submit", "en", keep_record=False)
        ok_starter = r["status"] != "accepted"
        line.append("starter " + ("caught" if ok_starter else "PASSES?!"))
        path, names = wrong_variants(p["id"])
        code = path.read_text(encoding="utf-8") if names else ""
        missed = []
        for n in names:
            r = judge(p["id"], code, "submit", "en", fn=n, keep_record=False)
            if r["status"] == "accepted":
                missed.append(n)
            elif r["status"] in ("internal_error", "compile_error"):
                missed.append(f"{n}({r['status']}: {r.get('message')})")
        line.append(f"wrong {len(names) - len(missed)}/{len(names)} caught" + (f" MISSED {missed}" if missed else ""))
        good = ok_ref and ok_starter and names and not missed
        bad += not good
        print(f"{'✓' if good else '✗'} {p['no']:>3} {p['id']:<28} " + " · ".join(line))
    print(f"\n{len(problems) - bad}/{len(problems)} problems verified")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list")
    s.add_argument("--track", choices=list(TRACKS))
    s.add_argument("--difficulty", choices=list(LEVELS))
    s.add_argument("--json", action="store_true")
    for name in ("show", "solution", "followups"):
        sub.add_parser(name).add_argument("id")
    s = sub.add_parser("pull")
    s.add_argument("id")
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("test")
    s.add_argument("id")
    s.add_argument("file", nargs="?")
    s.add_argument("--run", action="store_true")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("hint")
    s.add_argument("id")
    s.add_argument("--all", action="store_true")
    sub.add_parser("progress")
    sub.add_parser("check").add_argument("ids", nargs="*")
    for sp in sub.choices.values():
        sp.add_argument("--lang", default=argparse.SUPPRESS, choices=["zh", "en"])
    a = ap.parse_args()
    try:
        return globals()["cmd_" + a.cmd](a)
    except KeyError as e:
        print(f"no such problem: {e.args[0]} (see `allclose.py list`)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
