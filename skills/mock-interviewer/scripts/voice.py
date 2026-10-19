#!/usr/bin/env python3
"""Voice bridge: the agent is the interviewer's brain, a browser tab is its mouth and ears.

The browser speaks each question with the free Web Speech API (speechSynthesis) and turns the
candidate's spoken answer into text (SpeechRecognition, or typing as a fallback). Stdlib only.

  voice.py start [--port 8765] [--no-open]   start the local server in the background, print the URL
  voice.py say "text" [--show MD]            speak without waiting (intro, transitions, feedback)
  voice.py ask "text" [--show MD] [--timeout 50]
                                             speak a question, wait for the candidate's answer and
                                             print it. Exit 3 = still answering -> run `wait` again.
  voice.py wait [--timeout 50]               keep waiting for the latest question's answer

Waits are short on purpose (50 s) so they fit inside any agent's command timeout; agents loop on
`wait` until the answer arrives. Keep --timeout below your agent's per-command limit.
  voice.py end [--report FILE | --text MD]   show the final report in the UI
  voice.py status | stop

--show puts text on screen without reading it aloud (code, a problem statement, a diagram).
Answers may start with [HINT], [SKIP] or [END] when the candidate presses those buttons.
Transcripts are appended to ~/.mock-interviewer/sessions/*.jsonl.
"""
import argparse
import json
import mimetypes
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
UI = SKILL / "ui"
DATA = SKILL / "data"
HOME = Path(os.environ.get("MOCK_INTERVIEWER_HOME", Path.home() / ".mock-interviewer"))
STATE = HOME / "bridge.json"
HEADER = "X-Requested-With"
HEADER_VALUE = "open-interview"


# ---------------- server ----------------

class Bridge:
    def __init__(self, log_path):
        self.cv = threading.Condition()
        self.events = []        # {seq, kind, id?, text, show?, expect?, ts}
        self.answers = {}       # question id -> answer text
        self.pending = None     # question id awaiting an answer
        self.last_ask = None    # most recent question that expects an answer (answered or not)
        self.last_poll = 0.0
        self.counter = 0
        self.log_path = log_path

    def _log(self, ev):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    def push(self, kind, **kw):
        with self.cv:
            ev = {"seq": len(self.events) + 1, "kind": kind, "ts": time.time(), **kw}
            self.events.append(ev)
            self._log(ev)
            self.cv.notify_all()
            return ev

    def say(self, text, show, expect):
        with self.cv:
            self.counter += 1
            qid = f"q{self.counter}"
            if expect:
                self.pending = qid
                self.last_ask = qid
        self.push("interviewer", id=qid, text=text, show=show, expect=expect)
        return qid

    def answer(self, qid, text):
        with self.cv:
            if qid in self.answers:
                return False
            self.answers[qid] = text
            if self.pending == qid:
                self.pending = None
        self.push("answer", id=qid, text=text)
        return True

    def wait_answer(self, qid, timeout):
        deadline = time.time() + timeout
        with self.cv:
            while qid not in self.answers:
                left = deadline - time.time()
                if left <= 0:
                    return None
                self.cv.wait(left)
            return self.answers[qid]

    def poll(self, after, timeout):
        deadline = time.time() + timeout
        with self.cv:
            self.last_poll = time.time()
            while len(self.events) <= after:
                left = deadline - time.time()
                if left <= 0:
                    break
                self.cv.wait(min(left, 5))
                self.last_poll = time.time()
            return self.events[after:]


def make_handler(bridge, get_routes=None, post_routes=None):
    """get_routes / post_routes: {path: fn(query_or_body) -> json-able} for servers built on this one."""
    get_routes, post_routes = get_routes or {}, post_routes or {}

    class H(BaseHTTPRequestHandler):
        server_version = "open-interview-voice/1"

        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path):
            if not path.is_file():
                return self._json({"error": "not found"}, 404)
            body = path.read_bytes()
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
                ctype += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            u = urlparse(self.path)
            qs = {k: v[0] for k, v in parse_qs(u.query).items()}
            if u.path in get_routes:
                return self._json(get_routes[u.path](qs))
            if u.path == "/api/events":
                evs = bridge.poll(int(qs.get("after", 0)), min(float(qs.get("wait", 25)), 30))
                return self._json({"bridge": True, "events": evs, "pending": bridge.pending})
            if u.path == "/api/answer":
                text = bridge.wait_answer(qs.get("id", ""), min(float(qs.get("wait", 0)), 570))
                return self._json({"status": "answered", "text": text} if text is not None
                                  else {"status": "pending"})
            if u.path == "/api/status":
                return self._json({"pending": bridge.pending, "last_ask": bridge.last_ask,
                                   "events": len(bridge.events),
                                   "ui_connected": time.time() - bridge.last_poll < 40,
                                   "log": str(bridge.log_path)})
            if u.path.startswith("/data/"):
                return self._file(DATA / Path(u.path).name)
            name = u.path.strip("/") or "index.html"
            target = (UI / name).resolve()
            if UI.resolve() not in target.parents and target != UI.resolve():
                return self._json({"error": "not found"}, 404)
            return self._file(target)

        def do_POST(self):
            if self.headers.get(HEADER) != HEADER_VALUE:  # blocks cross-site form posts
                return self._json({"error": "missing header"}, 403)
            u = urlparse(self.path)
            try:
                b = self._body()
            except json.JSONDecodeError:
                return self._json({"error": "bad json"}, 400)
            if u.path in post_routes:
                return self._json(post_routes[u.path](b))
            if u.path == "/api/say":
                qid = bridge.say(b.get("text", ""), b.get("show"), bool(b.get("expect")))
                return self._json({"id": qid})
            if u.path == "/api/answer":
                ok = bridge.answer(b.get("id", ""), str(b.get("text", "")))
                return self._json({"ok": ok})
            if u.path == "/api/report":
                bridge.push("report", text=b.get("text", ""))
                return self._json({"ok": True})
            return self._json({"error": "not found"}, 404)

    return H


def free_port(preferred):
    for port in [preferred] + list(range(preferred + 1, preferred + 20)):
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # same as the server; ignores TIME_WAIT
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit("no free port")


def serve(port):
    log = HOME / "sessions" / time.strftime("%Y%m%d-%H%M%S.jsonl")
    bridge = Bridge(log)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(bridge))
    httpd.daemon_threads = True
    HOME.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"port": port, "pid": os.getpid(), "log": str(log)}))
    try:
        httpd.serve_forever()
    finally:
        if STATE.exists() and json.loads(STATE.read_text()).get("pid") == os.getpid():
            STATE.unlink()


# ---------------- client ----------------

def state():
    if not STATE.exists():
        return None
    try:
        st = json.loads(STATE.read_text())
        with urllib.request.urlopen(f"http://127.0.0.1:{st['port']}/api/status", timeout=2) as r:
            st.update(json.loads(r.read()))
        return st
    except (OSError, ValueError, KeyError):
        return None


def call(method, path, payload=None, timeout=10):
    st = state()
    if not st:
        sys.exit("voice bridge is not running; run: voice.py start")
    data = json.dumps(payload or {}).encode() if method == "POST" else None
    req = urllib.request.Request(f"http://127.0.0.1:{st['port']}{path}", data=data, method=method,
                                 headers={"Content-Type": "application/json", HEADER: HEADER_VALUE})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def cmd_start(a):
    st = state()
    if not st:
        port = free_port(a.port)
        HOME.mkdir(parents=True, exist_ok=True)
        out = (HOME / "bridge.log").open("a")
        subprocess.Popen([sys.executable, "-I", str(Path(__file__).resolve()), "serve", "--port", str(port)],
                         stdout=out, stderr=out, stdin=subprocess.DEVNULL, start_new_session=True)
        for _ in range(50):
            time.sleep(0.1)
            st = state()
            if st:
                break
        if not st:
            sys.exit(f"bridge failed to start; see {HOME / 'bridge.log'}")
    url = f"http://127.0.0.1:{st['port']}/#agent"
    print(f"voice bridge running: {url}")
    print("Ask the candidate to open it in Chrome or Edge, allow the microphone, and press 开始.")
    if not a.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def warn_if_no_ui():
    st = state()
    if st and not st.get("ui_connected"):
        print(f"warning: no browser tab connected; ask the candidate to open "
              f"http://127.0.0.1:{st['port']}/#agent", file=sys.stderr)


def wait_for(qid, timeout):
    deadline = time.time() + timeout
    while True:
        left = deadline - time.time()
        if left <= 0:
            print(f"[still answering] The candidate is still answering. Run again: voice.py wait --id {qid}")
            sys.exit(3)
        try:
            r = call("GET", f"/api/answer?id={qid}&wait={min(left, 60):.0f}", timeout=min(left, 60) + 10)
        except (urllib.error.URLError, TimeoutError):
            continue
        if r["status"] == "answered":
            print(r["text"].strip() or "[EMPTY] (candidate submitted nothing)")
            return


def show_arg(a):
    if a.show_file:
        return Path(a.show_file).read_text(encoding="utf-8")
    return a.show


def cmd_say(a):
    warn_if_no_ui()
    call("POST", "/api/say", {"text": a.text, "show": show_arg(a), "expect": False})
    print("ok")


def cmd_ask(a):
    warn_if_no_ui()
    r = call("POST", "/api/say", {"text": a.text, "show": show_arg(a), "expect": True})
    wait_for(r["id"], a.timeout)


def cmd_wait(a):
    st = state()
    if not st:
        sys.exit("voice bridge is not running")
    qid = a.id or st.get("last_ask")  # the last question, even if it was answered a moment ago
    if not qid:
        sys.exit("no question has been asked yet")
    wait_for(qid, a.timeout)


def cmd_end(a):
    text = Path(a.report).read_text(encoding="utf-8") if a.report else (a.text or "")
    call("POST", "/api/report", {"text": text})
    print("report shown")


def cmd_status(a):
    st = state()
    if not st:
        print("not running")
        return
    print(json.dumps({k: st[k] for k in ("port", "pid", "pending", "ui_connected", "log") if k in st},
                     ensure_ascii=False))


def cmd_stop(a):
    st = state()
    if not st:
        print("not running")
        return
    try:
        os.kill(st["pid"], 15)
    except ProcessLookupError:
        pass
    STATE.unlink(missing_ok=True)
    print(f"stopped; transcript: {st.get('log')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-open", action="store_true", help="do not open a browser tab")
    p = sub.add_parser("serve")
    p.add_argument("--port", type=int, default=8765)
    for name in ("say", "ask"):
        p = sub.add_parser(name)
        p.add_argument("text", help="what the interviewer says out loud (plain sentences, no markdown)")
        p.add_argument("--show", help="markdown shown on screen but not spoken")
        p.add_argument("--show-file", help="like --show, read from a file")
        if name == "ask":
            p.add_argument("--timeout", type=float, default=50, help="seconds before returning exit 3")
    p = sub.add_parser("wait")
    p.add_argument("--id", help="question id from the `ask` timeout message (default: the last question)")
    p.add_argument("--timeout", type=float, default=50)
    p = sub.add_parser("end")
    p.add_argument("--report", help="markdown file with the final feedback")
    p.add_argument("--text")
    sub.add_parser("status")
    sub.add_parser("stop")
    a = ap.parse_args()
    if a.cmd == "serve":
        return serve(a.port)
    {"start": cmd_start, "say": cmd_say, "ask": cmd_ask, "wait": cmd_wait, "end": cmd_end,
     "status": cmd_status, "stop": cmd_stop}[a.cmd](a)


if __name__ == "__main__":
    main()
