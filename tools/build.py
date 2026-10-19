#!/usr/bin/env python3
"""Validate bank/ and build skills/mock-interviewer/data/index.json.

    python3 tools/build.py           # validate + write the index
    python3 tools/build.py --check   # validate only (CI); exit 1 on errors

Needs PyYAML (pip install pyyaml). The skill itself only reads the built JSON.
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "bank"
OUT = ROOT / "skills" / "mock-interviewer" / "data" / "index.json"

LANGS = {"zh", "en"}
ITEM_KEYS = {"id", "q", "lang", "type", "roles", "topics", "companies", "levels", "difficulty", "weight",
             "hot", "followups", "key_points", "answer_brief", "url", "notes"}
FILE_KEYS = {"source", "defaults", "questions"}
SOURCE_KEYS = {"name", "url", "license", "commit", "author"}
EXP_KEYS = {"id", "company", "role", "level", "date", "department", "location", "result", "lang", "source",
            "summary", "rounds", "notes"}
ROUND_KEYS = {"name", "type", "duration", "questions", "notes"}
RESULTS = {"offer", "rejected", "pending", "unknown", "withdrawn"}
DEFAULT_SOURCE = {"name": "open-interview contributors", "license": "CC-BY-SA-4.0"}


def suggest(value, vocab):
    close = difflib.get_close_matches(str(value), list(vocab), n=1)
    return f" — did you mean '{close[0]}'?" if close else " (add it to bank/tags.yml first)"


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def norm(text):
    return re.sub(r"[\W_]+", "", text.lower())


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def slug(path):
    rel = path.relative_to(BANK).with_suffix("").as_posix()
    rel = rel.replace("questions/imported/", "").replace("questions/", "").replace("experiences/", "exp/")
    return re.sub(r"[^a-z0-9]+", "-", rel.lower()).strip("-")


def check_item(item, where, tags, rep):
    for k in item:
        if k not in ITEM_KEYS:
            rep.err(where, f"unknown field '{k}'" + suggest(k, ITEM_KEYS).replace(" (add it to bank/tags.yml first)", ""))
    q = item.get("q")
    if not isinstance(q, str) or not q.strip():
        rep.err(where, "missing 'q' (question text)")
    elif len(q) > 600:
        rep.err(where, "question longer than 600 chars; put context in notes or link it")
    if item.get("lang") not in LANGS:
        rep.err(where, f"lang must be one of {sorted(LANGS)}")
    if item.get("type") not in tags["types"]:
        rep.err(where, f"type '{item.get('type')}' not in tags.yml types")
    for field, vocab in (("roles", "roles"), ("companies", "companies"), ("levels", "levels")):
        for v in item.get(field, []):
            if v not in tags[vocab]:
                rep.err(where, f"{field} value '{v}' not in tags.yml" + suggest(v, tags[vocab]))
    for t in item.get("topics", []):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(t)):
            rep.err(where, f"topic '{t}' should be lowercase-kebab")
        elif t not in tags["topics"]:
            rep.warn(where, f"topic '{t}' not listed in tags.yml topics")
    d = item.get("difficulty")
    if d is not None and (not isinstance(d, int) or not 1 <= d <= 5):
        rep.err(where, "difficulty must be an integer 1-5")
    w = item.get("weight")
    if w is not None and (not isinstance(w, (int, float)) or not 0 <= w <= 5):
        rep.err(where, "weight must be a number 0-5")
    for f in ("followups", "key_points"):
        if any(not isinstance(x, str) for x in item.get(f, [])):
            rep.err(where, f"{f} must be a list of strings")
    u = item.get("url")
    if u is not None and not re.match(r"https?://", str(u)):
        rep.err(where, "url must start with http(s)://")


def resolve(raw, defaults, where, tags, rep):
    """Merge file defaults into one item and normalise list fields."""
    if isinstance(raw, str):
        raw = {"q": raw}
    if not isinstance(raw, dict):
        rep.err(where, "each question must be a string or a mapping with 'q'")
        return None
    item = {**defaults, **raw}
    for f in ("roles", "topics", "companies", "levels", "followups", "key_points"):
        if f in item:
            item[f] = as_list(item[f])
    item.setdefault("type", "technical")
    if isinstance(item.get("q"), str):
        item["q"] = item["q"].strip()
    check_item(item, where, tags, rep)
    return item


def load_yaml(path, rep):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        rep.err(path.relative_to(ROOT).as_posix(), f"YAML error: {e}")
        return None


def check_source(src, where, rep):
    if src is None:
        return dict(DEFAULT_SOURCE)
    if not isinstance(src, dict):
        rep.err(where, "source must be a mapping")
        return dict(DEFAULT_SOURCE)
    for k in src:
        if k not in SOURCE_KEYS:
            rep.err(where, f"unknown source field '{k}'")
    if not src.get("name"):
        rep.err(where, "source.name is required")
    return {**{"license": DEFAULT_SOURCE["license"]}, **src}


def load_question_file(path, tags, rep):
    where = path.relative_to(ROOT).as_posix()
    doc = load_yaml(path, rep)
    if doc is None:
        return None, []
    if isinstance(doc, list):
        doc = {"questions": doc}
    if not isinstance(doc, dict) or not isinstance(doc.get("questions"), list):
        rep.err(where, "expected a mapping with a 'questions' list")
        return None, []
    for k in doc:
        if k not in FILE_KEYS:
            rep.err(where, f"unknown top-level field '{k}'")
    source = check_source(doc.get("source"), where, rep)
    defaults = doc.get("defaults") or {}
    if "q" in defaults or "id" in defaults:
        rep.err(where, "defaults cannot set q or id")
    items = []
    for i, raw in enumerate(doc["questions"]):
        item = resolve(raw, defaults, f"{where} #{i + 1}", tags, rep)
        if item:
            items.append(item)
    return source, items


def load_experience_file(path, tags, rep):
    where = path.relative_to(ROOT).as_posix()
    doc = load_yaml(path, rep)
    if not isinstance(doc, dict):
        rep.err(where, "expected a mapping (see bank/experiences/_template.yml)")
        return None, None, []
    for k in doc:
        if k not in EXP_KEYS:
            rep.err(where, f"unknown field '{k}'")
    # Imported 面经 may leave date out when the upstream author never said when the interview was.
    required = ("company", "role", "rounds") if "/imported/" in where else ("company", "role", "date", "rounds")
    for k in required:
        if not doc.get(k):
            rep.err(where, f"'{k}' is required")
    if doc.get("company") and doc["company"] not in tags["companies"]:
        rep.err(where, f"company '{doc['company']}' not in tags.yml" + suggest(doc["company"], tags["companies"]))
    if doc.get("role") and doc["role"] not in tags["roles"]:
        rep.err(where, f"role '{doc['role']}' not in tags.yml" + suggest(doc["role"], tags["roles"]))
    if doc.get("level") and doc["level"] not in tags["levels"]:
        rep.err(where, f"level '{doc['level']}' not in tags.yml")
    if doc.get("result") and doc["result"] not in RESULTS:
        rep.err(where, f"result must be one of {sorted(RESULTS)}")
    date = str(doc.get("date", ""))
    if date and not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", date):
        rep.err(where, "date must look like 2026-09 or 2026-09-18")
    source = check_source(doc.get("source"), where, rep)
    lang = doc.get("lang", "zh")
    base = {"lang": lang, "companies": [doc.get("company")] if doc.get("company") else [],
            "roles": [doc.get("role")] if doc.get("role") else [],
            "levels": [doc["level"]] if doc.get("level") else []}
    exp = {k: doc[k] for k in ("company", "role", "level", "date", "department", "location", "result",
                               "summary", "notes") if doc.get(k) is not None}
    if date:
        exp["date"] = date
    exp["lang"] = lang
    exp["rounds"] = []
    items = []
    for r_i, rnd in enumerate(as_list(doc.get("rounds"))):
        rwhere = f"{where} rounds[{r_i}]"
        if not isinstance(rnd, dict) or not rnd.get("name"):
            rep.err(rwhere, "each round needs a 'name' (e.g. 一面 / Phone screen)")
            continue
        for k in rnd:
            if k not in ROUND_KEYS:
                rep.err(rwhere, f"unknown round field '{k}'")
        rdefaults = {**base, "type": rnd.get("type", "technical")}
        ids = []
        for q_i, raw in enumerate(as_list(rnd.get("questions"))):
            item = resolve(raw, rdefaults, f"{rwhere} #{q_i + 1}", tags, rep)
            if item:
                item["round"] = rnd["name"]
                items.append(item)
                ids.append(item)
        exp["rounds"].append({k: rnd[k] for k in ("name", "type", "duration", "notes") if k in rnd}
                             | {"questions": ids})
    return source, exp, items


def build(check_only=False):
    rep = Report()
    tags = yaml.safe_load((BANK / "tags.yml").read_text(encoding="utf-8"))
    for k in ("companies", "roles", "types", "levels", "topics"):
        tags.setdefault(k, {})
    for slug_, r in tags["roles"].items():
        if r.get("parent") and r["parent"] not in tags["roles"]:
            rep.err("bank/tags.yml", f"role {slug_} has unknown parent {r['parent']}")

    sources, src_index = [], {}

    def src_id(src):
        key = json.dumps(src, sort_keys=True, ensure_ascii=False)
        if key not in src_index:
            src_index[key] = len(sources)
            sources.append(src)
        return src_index[key]

    questions, experiences, ids, texts = [], [], {}, {}

    def add(item, path, src, exp_id=None):
        qid = item.get("id") or f"{slug(path)}-{hashlib.sha1(norm(item['q']).encode()).hexdigest()[:6]}"
        where = path.relative_to(ROOT).as_posix()
        if qid in ids:
            rep.err(where, f"duplicate id '{qid}' (also in {ids[qid]})")
            return None
        ids[qid] = where
        key = norm(item["q"])
        if key in texts and exp_id is None:
            rep.warn(where, f"same question text as {texts[key]}")
        texts.setdefault(key, qid)
        out = {"id": qid, "q": item["q"], "lang": item["lang"], "type": item["type"]}
        for f in ("roles", "topics", "companies", "levels", "followups", "key_points"):
            if item.get(f):
                out[f] = item[f]
        for f in ("difficulty", "hot", "answer_brief", "url", "notes", "round"):
            if item.get(f) not in (None, ""):
                out[f] = item[f]
        if item.get("weight", 1) != 1:
            out["weight"] = item["weight"]
        out["src"] = src_id(src)
        if exp_id:
            out["exp"] = exp_id
        questions.append(out)
        return qid

    for path in sorted((BANK / "questions").rglob("*.y*ml")):
        source, items = load_question_file(path, tags, rep)
        if source is None or path.name.startswith("_"):
            continue
        for item in items:
            add(item, path, source)

    for path in sorted((BANK / "experiences").rglob("*.y*ml")):
        source, exp, items = load_experience_file(path, tags, rep)
        if exp is None or rep.errors or path.name.startswith("_"):
            continue
        exp_id = slug(path)
        exp["id"] = exp_id
        exp["src"] = src_id(source)
        for rnd in exp["rounds"]:
            rnd["questions"] = [add(item, path, source, exp_id) for item in rnd["questions"]]
        experiences.append(exp)

    for w in rep.warnings[:40]:
        print(f"warning: {w}")
    if len(rep.warnings) > 40:
        print(f"... {len(rep.warnings) - 40} more warnings")
    for e in rep.errors:
        print(f"ERROR: {e}")
    if rep.errors:
        print(f"\n{len(rep.errors)} error(s). See CONTRIBUTING.md for the format.")
        return 1

    counts = {"questions": len(questions), "experiences": len(experiences)}
    for field in ("type", "lang"):
        c = {}
        for q in questions:
            c[q[field]] = c.get(q[field], 0) + 1
        counts[field] = dict(sorted(c.items(), key=lambda kv: -kv[1]))
    print(f"ok: {counts['questions']} questions, {counts['experiences']} experiences, {len(sources)} sources")
    if check_only:
        return 0

    # A content digest instead of a timestamp keeps rebuilds byte-identical when bank/ did not change.
    digest = hashlib.sha1(json.dumps([questions, experiences, sources], ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:12]
    index = {
        "schema": 1,
        "digest": digest,
        "counts": counts,
        "tags": {k: tags[k] for k in ("companies", "roles", "types", "levels", "topics")},
        "sources": sources,
        "experiences": experiences,
        "questions": questions,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    notices = ["# Third-party licenses\n\nindex.json includes material from the projects below "
               "(see LICENSE-DATA.md in the repository).\n"]
    for lic in sorted(BANK.rglob("UPSTREAM-LICENSE.txt")):
        notices.append("\n---\n\n```\n" + lic.read_text(encoding="utf-8").strip() + "\n```\n")
    (OUT.parent / "THIRD_PARTY_LICENSES.md").write_text("".join(notices), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate only")
    sys.exit(build(ap.parse_args().check))
