#!/usr/bin/env python3
"""Query the open interview question bank (stdlib only).

Examples:
  bank.py stats
  bank.py tags companies                      # also: roles, topics, types, levels
  bank.py search --company 字节 --role backend --topic redis
  bank.py sample --role frontend -n 6 --mix technical=4,behavioral=1,coding=1 --lang zh
  bank.py sample --company google --role swe -n 5 --seed 7
  bank.py show <id> [<id> ...]
  bank.py experiences --company bytedance     # 面经 list;  bank.py experience <id> for one

Filters (search/sample): --company --role --type --topic --level --lang --difficulty 2-4 --hot --text KW --source KW
Company and role accept aliases (字节, tiktok, 后端 ...). --role also matches parent roles
(backend -> swe) and role-agnostic questions. Add --json for machine-readable output.
"""
import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE.parent / "data" / "index.json"


def load():
    if not INDEX.exists():
        sys.exit(f"index not found: {INDEX}\nIn a clone of the repo run: python3 tools/build.py")
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    repo_bank = HERE.parents[2] / "bank"
    if repo_bank.is_dir():  # running from a repo checkout: warn when the index is older than the YAML
        newest = max((p.stat().st_mtime for p in repo_bank.rglob("*.y*ml")), default=0)
        if newest > INDEX.stat().st_mtime:
            print("note: bank/ changed since the index was built; run python3 tools/build.py", file=sys.stderr)
    return data


def resolver(vocab):
    table = {}
    for slug, info in vocab.items():
        for name in [slug, info.get("name", ""), info.get("en", "")] + list(info.get("aliases", [])):
            if name:
                table[str(name).lower()] = slug
    return table


def resolve(data, kind, value):
    if value is None:
        return None
    table = resolver(data["tags"][kind])
    slug = table.get(value.lower())
    if slug:
        return slug
    hits = sorted({s for k, s in table.items() if value.lower() in k})
    if len(hits) == 1:
        return hits[0]
    known = ", ".join(sorted(data["tags"][kind]))
    sys.exit(f"unknown {kind[:-1]} '{value}'" + (f"; did you mean one of: {', '.join(hits)}" if hits
                                                   else f". Known: {known}"))


def role_chain(data, role):
    roles, seen = set(), role
    while seen and seen not in roles:
        roles.add(seen)
        seen = data["tags"]["roles"].get(seen, {}).get("parent")
    return roles


def split(v):
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


def matcher(data, a, ignore_company=False):
    company = None if ignore_company else resolve(data, "companies", a.company)
    roles = role_chain(data, resolve(data, "roles", a.role)) if a.role else None
    types = set(split(a.type))
    topics = set(split(a.topic))
    lo, hi = 1, 5
    if a.difficulty:
        parts = a.difficulty.split("-")
        lo, hi = int(parts[0]), int(parts[-1])
    text = a.text.lower() if a.text else None
    src_hits = None
    if a.source:
        src_hits = {i for i, s in enumerate(data["sources"]) if a.source.lower() in s["name"].lower()}

    def ok(q):
        if company and company not in q.get("companies", []):
            return False
        if roles is not None and q.get("roles") and not roles & set(q["roles"]):
            return False
        if types and q["type"] not in types:
            return False
        if topics and not topics & set(q.get("topics", [])):
            return False
        if a.level and q.get("levels") and a.level not in q["levels"]:
            return False
        if a.lang and q["lang"] != a.lang:
            return False
        if a.difficulty and not (q.get("difficulty") and lo <= q["difficulty"] <= hi):
            return False
        if a.hot and not q.get("hot"):
            return False
        if text and text not in q["q"].lower():
            return False
        if src_hits is not None and q["src"] not in src_hits:
            return False
        return True

    return ok


def weighted_pick(pool, n, rng):
    pool, out = list(pool), []
    while pool and len(out) < n:
        total = sum(q.get("weight", 1) for q in pool)
        r, acc = rng.uniform(0, total), 0.0
        for i, q in enumerate(pool):
            acc += q.get("weight", 1)
            if acc >= r:
                out.append(pool.pop(i))
                break
        else:
            out.append(pool.pop())
    return out


def fmt(data, q, verbose=False):
    meta = [data["tags"]["types"].get(q["type"], {}).get("name", q["type"])]
    if q.get("roles"):
        meta.append("/".join(q["roles"]))
    if q.get("companies"):
        meta.append("@" + ",".join(q["companies"]))
    if q.get("difficulty"):
        meta.append(f"d{q['difficulty']}")
    if q.get("hot"):
        meta.append("hot")
    if q.get("_fill"):
        meta.append("general")
    lines = [f"[{q['id']}] ({' · '.join(meta)}) {q['q']}"]
    if q.get("round"):
        lines.append(f"    面经轮次: {q['round']} ({q.get('exp')})")
    for f in q.get("followups", []):
        lines.append(f"    ↳ follow-up: {f}")
    if verbose:
        for k in q.get("key_points", []):
            lines.append(f"    ✓ key point: {k}")
        if q.get("answer_brief"):
            lines.append(f"    ✓ brief answer: {q['answer_brief']}")
        if q.get("topics"):
            lines.append(f"    topics: {', '.join(q['topics'])}")
        src = data["sources"][q["src"]]
        lines.append(f"    source: {src['name']} ({src.get('license', '?')})  {q.get('url') or src.get('url', '')}")
    return "\n".join(lines)


def emit(data, items, a, verbose=False):
    if a.json:
        print(json.dumps(items, ensure_ascii=False, indent=1))
        return
    for q in items:
        print(fmt(data, q, verbose or a.verbose))


def cmd_stats(data, a):
    c = data["counts"]
    print(f"{c['questions']} questions, {c['experiences']} interview reports (面经), index {data.get('digest', '?')}")
    print("by type:", ", ".join(f"{k} {v}" for k, v in c["type"].items()))
    print("by lang:", ", ".join(f"{k} {v}" for k, v in c["lang"].items()))
    print("sources:")
    for s in data["sources"]:
        print(f"  - {s['name']} ({s.get('license', '?')})")


def cmd_tags(data, a):
    kind = a.kind
    field = {"companies": "companies", "roles": "roles", "topics": "topics", "types": "type",
             "levels": "levels"}[kind]
    counts = {}
    for q in data["questions"]:
        vals = q.get(field, []) if field != "type" else [q["type"]]
        for v in vals:
            counts[v] = counts.get(v, 0) + 1
    vocab = data["tags"][kind]
    rows = sorted(set(vocab) | set(counts), key=lambda k: (-counts.get(k, 0), k))
    for k in rows:
        info = vocab.get(k, {})
        name = info if isinstance(info, str) else info.get("name", "")
        extra = "" if isinstance(info, str) else (" aka " + ", ".join(info["aliases"]) if info.get("aliases") else "")
        print(f"{counts.get(k, 0):5d}  {k:16s} {name}{extra}")


def cmd_search(data, a):
    ok = matcher(data, a)
    hits = [q for q in data["questions"] if ok(q)]
    print(f"# {len(hits)} match(es)" + (f", showing {a.limit}" if len(hits) > a.limit else ""), file=sys.stderr)
    emit(data, hits[: a.limit], a)


def cmd_sample(data, a):
    rng = random.Random(a.seed)
    mix = {}
    for part in split(a.mix):
        t, _, n = part.partition("=")
        mix[t] = int(n or 1)
    plan = mix or {None: a.n}
    picked, ids = [], set()
    for qtype, n in plan.items():
        args = argparse.Namespace(**vars(a))
        if qtype:
            args.type = qtype
        got = weighted_pick([q for q in data["questions"] if matcher(data, args)(q)], n, rng)
        if a.company and len(got) < n:  # not enough company-tagged questions: fill from the general pool
            general = [q for q in data["questions"]
                       if matcher(data, args, ignore_company=True)(q) and q["id"] not in {g["id"] for g in got}]
            got += [dict(q, _fill=True) for q in weighted_pick(general, n - len(got), rng)]
        for q in got:
            if q["id"] not in ids:
                ids.add(q["id"])
                picked.append(q)
    if not picked:
        sys.exit("no questions match; loosen the filters (try dropping --topic or --lang)")
    if a.company and any(q.get("_fill") for q in picked):
        print("# note: items marked 'general' are not tagged with this company yet", file=sys.stderr)
    emit(data, picked, a)


def cmd_show(data, a):
    by_id = {q["id"]: q for q in data["questions"]}
    missing = [i for i in a.ids if i not in by_id]
    if missing:
        sys.exit(f"unknown id: {', '.join(missing)}")
    emit(data, [by_id[i] for i in a.ids], a, verbose=True)


def cmd_experiences(data, a):
    company = resolve(data, "companies", a.company)
    role = resolve(data, "roles", a.role) if a.role else None
    exps = [e for e in data["experiences"]
            if (not company or e["company"] == company) and (not role or e["role"] in role_chain(data, role))]
    if a.json:
        print(json.dumps(exps, ensure_ascii=False, indent=1))
        return
    if not exps:
        print("no 面经 yet for this filter — contributions welcome (bank/experiences/_template.yml)")
    for e in exps:
        n = sum(len(r["questions"]) for r in e["rounds"])
        rounds = " → ".join(r["name"] for r in e["rounds"])
        print(f"[{e['id']}] {e['date']} {e['company']} {e['role']} {e.get('level', '')} "
              f"{e.get('result', '')} · {rounds} · {n} questions\n    {e.get('summary', '')}")


def cmd_experience(data, a):
    exp = next((e for e in data["experiences"] if e["id"] == a.id), None)
    if not exp:
        sys.exit(f"unknown experience id {a.id}")
    if a.json:
        print(json.dumps(exp, ensure_ascii=False, indent=1))
        return
    by_id = {q["id"]: q for q in data["questions"]}
    head = " ".join(str(exp.get(k, "")) for k in ("date", "company", "department", "role", "level", "result"))
    print(f"# {head}\n{exp.get('summary', '')}")
    for r in exp["rounds"]:
        print(f"\n## {r['name']} ({r.get('type', '')}{', ' + str(r['duration']) + ' min' if r.get('duration') else ''})")
        for qid in r["questions"]:
            print(fmt(data, by_id[qid], verbose=a.verbose))
        if r.get("notes"):
            print(f"  notes: {r['notes']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def filters(p):
        p.add_argument("--company")
        p.add_argument("--role")
        p.add_argument("--type", help="comma list: technical,coding,system-design,behavioral,project,hr")
        p.add_argument("--topic", help="comma list, any match")
        p.add_argument("--level")
        p.add_argument("--lang", choices=["zh", "en"])
        p.add_argument("--difficulty", help="e.g. 3 or 2-4")
        p.add_argument("--hot", action="store_true", help="only high-frequency questions")
        p.add_argument("--text", help="substring in question text")
        p.add_argument("--source", help="substring of source repo name")
        p.add_argument("--json", action="store_true")
        p.add_argument("-v", "--verbose", action="store_true", help="show key points and sources")

    sub.add_parser("stats")
    t = sub.add_parser("tags")
    t.add_argument("kind", nargs="?", default="companies", choices=["companies", "roles", "topics", "types", "levels"])
    s = sub.add_parser("search")
    filters(s)
    s.add_argument("--limit", type=int, default=30)
    sm = sub.add_parser("sample")
    filters(sm)
    sm.add_argument("-n", type=int, default=8)
    sm.add_argument("--mix", help="per-type counts, e.g. technical=4,coding=1,behavioral=2 (overrides -n)")
    sm.add_argument("--seed", type=int)
    sh = sub.add_parser("show")
    sh.add_argument("ids", nargs="+")
    sh.add_argument("--json", action="store_true")
    sh.add_argument("-v", "--verbose", action="store_true")
    ex = sub.add_parser("experiences")
    ex.add_argument("--company")
    ex.add_argument("--role")
    ex.add_argument("--json", action="store_true")
    e1 = sub.add_parser("experience")
    e1.add_argument("id")
    e1.add_argument("--json", action="store_true")
    e1.add_argument("-v", "--verbose", action="store_true")

    a = ap.parse_args()
    data = load()
    {"stats": cmd_stats, "tags": cmd_tags, "search": cmd_search, "sample": cmd_sample, "show": cmd_show,
     "experiences": cmd_experiences, "experience": cmd_experience}[a.cmd](data, a)


if __name__ == "__main__":
    main()
