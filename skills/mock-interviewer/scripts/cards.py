#!/usr/bin/env python3
"""记忆卡 (flashcards) storage for the studio: the review log and tags live in files on this machine.

    ~/.mock-interviewer/cards/reviews.jsonl   one review per line: {"c": card id, "t": ms, "r": 1-4}
    ~/.mock-interviewer/cards/meta.json       tags, suspended cards, settings

The page replays the log with FSRS (ui/fsrs.js) to get each card's schedule, so nothing else is stored.
On the static site the same data lives in localStorage instead.

    python3 cards.py path      # where the files are
    python3 cards.py export    # print everything as one JSON (same format as the page's export)
"""
import json
import os
import sys
import threading
from pathlib import Path

HOME = Path(os.environ.get("MOCK_INTERVIEWER_HOME", Path.home() / ".mock-interviewer")) / "cards"
LOG = HOME / "reviews.jsonl"
META = HOME / "meta.json"
MAX_META = 2_000_000
LOCK = threading.Lock()


def clean(e):
    """A valid log entry, or None. Reviews: c, t, r (+ x for extra practice, ms for time on card). Undo: u."""
    if not isinstance(e, dict):
        return None
    if isinstance(e.get("u"), (int, float)):
        return {"u": int(e["u"])}
    c, t, r = e.get("c"), e.get("t"), e.get("r")
    if not (isinstance(c, str) and 0 < len(c) <= 200 and isinstance(t, (int, float)) and r in (1, 2, 3, 4)):
        return None
    out = {"c": c, "t": int(t), "r": r}
    if e.get("x"):
        out["x"] = 1
    if isinstance(e.get("ms"), (int, float)) and 0 <= e["ms"] < 36e5:
        out["ms"] = int(e["ms"])
    return out


def read_log():
    if not LOG.exists():
        return []
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        try:
            e = clean(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn last line from a crash; skip it
        if e:
            out.append(e)
    return out


def read_meta():
    try:
        m = json.loads(META.read_text(encoding="utf-8"))
        return m if isinstance(m, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def append(events):
    evs = [e for e in map(clean, events or []) if e]
    if evs:
        HOME.mkdir(parents=True, exist_ok=True)
        with LOCK, LOG.open("a", encoding="utf-8") as f:
            f.write("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in evs))
    return len(evs)


def write_meta(meta):
    body = json.dumps(meta, ensure_ascii=False, indent=1)
    if not isinstance(meta, dict) or len(body) > MAX_META:
        return False
    HOME.mkdir(parents=True, exist_ok=True)
    with LOCK:
        tmp = META.with_suffix(".tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(META)
    return True


def routes():
    def state(_q):
        return {"available": True, "log": read_log(), "meta": read_meta(), "home": str(HOME)}

    def log(b):
        return {"ok": True, "n": append(b.get("events"))}

    def meta(b):
        return {"ok": write_meta(b.get("meta"))}

    def merge(b):
        """Import a page export: add reviews not already in the log, take the imported meta where ours is empty."""
        have = {(e.get("c"), e.get("t"), e.get("u")) for e in read_log()}
        new = [e for e in map(clean, b.get("log") or []) if e and (e.get("c"), e.get("t"), e.get("u")) not in have]
        n = append(new)
        m, inc = read_meta(), b.get("meta") if isinstance(b.get("meta"), dict) else {}
        for k, v in inc.items():
            if isinstance(v, dict) and isinstance(m.get(k), dict):
                m[k] = {**v, **m[k]}
            else:
                m.setdefault(k, v)
        return {"ok": write_meta(m), "added": n}

    return ({"/api/cards": state},
            {"/api/cards/log": log, "/api/cards/meta": meta, "/api/cards/import": merge})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "path"
    if cmd == "path":
        print(HOME)
    elif cmd == "export":
        print(json.dumps({"log": read_log(), "meta": read_meta()}, ensure_ascii=False))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
