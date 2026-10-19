#!/usr/bin/env python3
"""Run a locally installed agent CLI as a plain text-in, text-out model (stdlib only).

The studio uses this so the interviewer runs on whatever the user already has and is logged in to:
Claude Code, Codex, Antigravity (agy), Cursor Agent or OpenCode. No API keys are involved.
Every call runs headless, in an empty scratch directory, in the CLI's read-only / no-tools mode.

  backends.py list               which CLIs are installed
  backends.py ping <id>          send a one-line prompt and time the reply

Override a binary path with OPEN_INTERVIEW_<ID>_BIN, e.g. OPEN_INTERVIEW_CLAUDE_BIN=/opt/claude.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path(os.environ.get("MOCK_INTERVIEWER_HOME", Path.home() / ".mock-interviewer"))
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


class BackendError(RuntimeError):
    pass


def _claude(exe, prompt, model, final, out):
    cmd = [exe, "-p", "--output-format", "text", "--tools", "", "--no-session-persistence",
           "--strict-mcp-config", "--disable-slash-commands"]
    return cmd + (["--model", model] if model else []), prompt


def _codex(exe, prompt, model, final, out):
    # The user's config may default to maximum reasoning effort; an interviewer turn does not need it.
    cmd = [exe, "exec", "--skip-git-repo-check", "--sandbox", "read-only", "--ephemeral", "--color", "never",
           "-c", f"model_reasoning_effort={'medium' if final else 'low'}", "-o", str(out)]
    return cmd + (["-m", model] if model else []) + ["-"], prompt


def _agy(exe, prompt, model, final, out):
    return [exe, "--disable-slash-commands", "--sandbox"] + (["--model", model] if model else []) + ["-p", prompt], None


def _cursor(exe, prompt, model, final, out):
    cmd = [exe, "-p", "--output-format", "text", "--mode", "ask", "--trust"]
    return cmd + (["--model", model] if model else []) + [prompt], None


def _opencode(exe, prompt, model, final, out):
    return [exe, "run", "--pure", "--agent", "plan"] + (["-m", model] if model else []) + [prompt], None


# id: (display name, binary names / extra paths, command builder, reads the reply from the -o file)
BACKENDS = {
    "claude": ("Claude Code", ["claude", "~/.claude/local/claude"], _claude, False),
    "codex": ("Codex", ["codex"], _codex, True),
    "agy": ("Antigravity (agy)", ["agy"], _agy, False),
    "cursor": ("Cursor Agent", ["cursor-agent"], _cursor, False),
    "opencode": ("OpenCode", ["opencode"], _opencode, False),
}


def find(bid):
    override = os.environ.get(f"OPEN_INTERVIEW_{bid.upper()}_BIN")
    if override:
        return override if Path(override).exists() else None
    for name in BACKENDS[bid][1]:
        path = shutil.which(os.path.expanduser(name))
        if path:
            return path
    return None


def detect():
    return [{"id": bid, "name": spec[0], "path": find(bid), "available": bool(find(bid))}
            for bid, spec in BACKENDS.items()]


def complete(bid, prompt, model=None, final=False, timeout=240):
    """Send one prompt, return the reply text. Raises BackendError with a readable reason."""
    if bid not in BACKENDS:
        raise BackendError(f"unknown backend {bid}")
    exe = find(bid)
    if not exe:
        raise BackendError(f"{BACKENDS[bid][0]} is not installed (no `{BACKENDS[bid][1][0]}` on PATH)")
    workdir = HOME / "run"  # empty, so the CLI picks up no project instructions or files
    workdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=workdir) as tmp:
        out = Path(tmp) / "reply.txt"
        cmd, stdin = BACKENDS[bid][2](exe, prompt, model, final, out)
        env = {**os.environ, "NO_COLOR": "1", "TERM": "dumb"}
        try:
            p = subprocess.run(cmd, input=stdin if stdin is not None else "", capture_output=True, text=True,
                               cwd=tmp, env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise BackendError(f"{BACKENDS[bid][0]} did not answer within {timeout}s")
        text = out.read_text(encoding="utf-8") if BACKENDS[bid][3] and out.exists() else p.stdout
    text = ANSI.sub("", text).strip()
    if p.returncode != 0 or not text:
        err = ANSI.sub("", (p.stderr or p.stdout or "").strip())
        tail = " ".join(err.splitlines()[-4:])[-400:]
        raise BackendError(f"{BACKENDS[bid][0]} failed (exit {p.returncode}): {tail or 'empty reply'}")
    return text


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "ping"):
        sys.exit(__doc__)
    if sys.argv[1] == "list":
        for b in detect():
            print(f"{b['id']:9s} {'✓' if b['available'] else '·'} {b['name']:20s} {b['path'] or ''}")
        return
    bid = sys.argv[2]
    t = time.time()
    try:
        reply = complete(bid, "Reply with exactly one line: PONG 你好. Do not use any tools.",
                         model=sys.argv[3] if len(sys.argv) > 3 else None)
    except BackendError as e:
        sys.exit(f"✗ {e}")
    print(f"✓ {bid} {time.time() - t:.1f}s: {reply[:200]}")


if __name__ == "__main__":
    main()
