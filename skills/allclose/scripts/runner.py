#!/usr/bin/env python3
"""Judge one candidate file against one problem, in a fresh process. Needs numpy.

  runner.py --problem DIR --meta JSON --code FILE --out RESULT.json [--mode run|submit] [--fn NAME] [--lang zh|en]

--meta carries the problem's entry function, banned calls and time limit: {"entry": "softmax", ...}.

allclose.py starts this in a subprocess (so a crash, an infinite loop or a stray sys.exit in the
candidate's code can't take the caller down) and reads the JSON written to --out. Expected outputs
come from the problem's reference solution.py, run on deep copies of the same inputs.
"""
import argparse
import ast
import contextlib
import copy
import io
import json
import math
import signal
import sys
import time
import traceback
from pathlib import Path

import numpy as np

ALLOWED_IMPORTS = {"numpy", "math", "typing", "collections", "itertools", "functools", "heapq", "bisect",
                   "dataclasses", "__future__", "random", "re", "string", "operator"}
RTOL, ATOL = 1e-5, 1e-6

MSG = {
    "zh": {
        "syntax": "第 {line} 行语法错误：{msg}",
        "import": "第 {line} 行：本题只能用 numpy 和标准库，不能 import {mod}",
        "banned": "第 {line} 行：本题不允许调用 {name}，请自己实现",
        "missing": "没找到函数 {fn}()，别改函数名",
        "module": "执行代码时出错",
        "none": "{path} 是 None，忘了 return？",
        "type": "{path} 类型不对：期望 {want}，得到 {got}",
        "shape": "{path} 形状不对：期望 {want}，得到 {got}",
        "len": "{path} 长度不对：期望 {want}，得到 {got}",
        "keys": "{path} 的键不对：期望 {want}，得到 {got}",
        "nan": "{path}{idx} 是 {got}（数值溢出或除以 0？）",
        "value": "{path}{idx} 不对：期望 {want}，得到 {got}，最大误差 {err}",
        "exact": "{path} 不对：期望 {want}，得到 {got}",
        "timeout": "超时：这个用例跑了超过 {limit} 秒",
        "todo": "还没写完：函数抛出了 NotImplementedError",
        "ref": "参考答案在这个用例上出错了（评测器的 bug，欢迎提 issue）：{err}",
        "out": "返回值",
    },
    "en": {
        "syntax": "Syntax error on line {line}: {msg}",
        "import": "Line {line}: only numpy and the standard library are allowed, not {mod}",
        "banned": "Line {line}: {name} is off-limits here, implement it yourself",
        "missing": "Function {fn}() not found, keep the original name",
        "module": "Error while loading your code",
        "none": "{path} is None. Forgot to return?",
        "type": "{path} has the wrong type: expected {want}, got {got}",
        "shape": "{path} has the wrong shape: expected {want}, got {got}",
        "len": "{path} has the wrong length: expected {want}, got {got}",
        "keys": "{path} has the wrong keys: expected {want}, got {got}",
        "nan": "{path}{idx} is {got} (overflow or division by zero?)",
        "value": "{path}{idx} is wrong: expected {want}, got {got}, max error {err}",
        "exact": "{path} is wrong: expected {want}, got {got}",
        "timeout": "Time limit: this case ran longer than {limit} s",
        "todo": "Not done yet: the function raised NotImplementedError",
        "ref": "The reference solution failed on this case (a judge bug, please open an issue): {err}",
        "out": "output",
    },
}


class Mismatch(Exception):
    pass


class CaseTimeout(BaseException):  # BaseException so a bare `except Exception` in user code can't swallow it
    pass


# ---------------- static checks ----------------

def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def static_check(code, path, banned, t):
    """None if fine, else a message. `banned` entries match the end of a dotted name, e.g. 'linalg.inv'."""
    try:
        tree = ast.parse(code, filename=path)
    except SyntaxError as e:
        return t["syntax"].format(line=e.lineno, msg=e.msg)
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            mods = [node.module or ""]
        for m in mods:
            if m.split(".")[0] not in ALLOWED_IMPORTS:
                return t["import"].format(line=node.lineno, mod=m)
        if banned and isinstance(node, ast.Attribute):
            name = dotted(node)
            if name and any(name == b or name.endswith("." + b) for b in banned):
                return t["banned"].format(line=node.lineno, name=name)
    return None


# ---------------- previews ----------------

def fmt_num(x):
    if isinstance(x, (bool, np.bool_)):
        return str(bool(x))
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        return str(x)
    return f"{x:.6g}"


def preview(x, depth=0):
    if isinstance(x, np.ndarray):
        body = np.array2string(x, precision=4, suppress_small=True, threshold=40, edgeitems=3, max_line_width=72)
        return f"array{list(x.shape)} {x.dtype}\n{body}" if x.ndim else body
    if isinstance(x, (int, float, bool, np.number, np.bool_)):
        return fmt_num(x)
    if isinstance(x, str):
        return repr(x if len(x) <= 120 else x[:120] + "…")
    if isinstance(x, (list, tuple)):
        if depth > 1:
            return f"{type(x).__name__}[{len(x)}]"
        items = [preview(v, depth + 1) for v in x[:8]]
        if any("\n" in s for s in items):
            return "\n".join(f"[{i}] {s}" for i, s in enumerate(items)) + ("\n…" if len(x) > 8 else "")
        inner = ", ".join(items) + (", …" if len(x) > 8 else "")
        return f"({inner})" if isinstance(x, tuple) else f"[{inner}]"
    if isinstance(x, dict):
        return "\n".join(f"{k}: {preview(v, depth + 1)}" for k, v in list(x.items())[:12])
    if callable(x):
        return f"<function {getattr(x, '__name__', '')}>"
    return repr(x)[:200]


def kind(x):
    if isinstance(x, np.ndarray):
        return f"ndarray{list(x.shape)}"
    return type(x).__name__


# ---------------- comparison ----------------

def is_numeric_array_like(x):
    return isinstance(x, (np.ndarray, np.number, float, int)) and not isinstance(x, bool)


def compare(got, want, t, rtol, atol, path):
    """Raise Mismatch(message) when got != want (numbers within rtol/atol, everything else exactly)."""
    if got is None and want is not None:
        raise Mismatch(t["none"].format(path=path))
    if isinstance(want, np.ndarray) or isinstance(want, (float, np.floating)):
        try:
            g = np.asarray(got)
        except Exception:
            raise Mismatch(t["type"].format(path=path, want=kind(want), got=kind(got)))
        w = np.asarray(want)
        if g.dtype == object or not (np.issubdtype(g.dtype, np.number) or g.dtype == bool):
            raise Mismatch(t["type"].format(path=path, want=kind(want), got=kind(got)))
        if g.shape != w.shape:
            raise Mismatch(t["shape"].format(path=path, want=tuple(w.shape), got=tuple(g.shape)))
        if np.issubdtype(w.dtype, np.integer) or w.dtype == bool:
            bad = g != w
            if bad.any():
                i = tuple(int(v) for v in np.argwhere(bad)[0])
                idx = list(i) if i else ""
                raise Mismatch(t["value"].format(path=path, idx=idx, want=fmt_num(w[i]), got=fmt_num(g[i]), err=fmt_num(abs(float(g[i]) - float(w[i])))))
            return
        g = g.astype(np.float64)
        w = w.astype(np.float64)
        nonfinite = ~np.isfinite(g) & np.isfinite(w)
        if nonfinite.any():
            i = tuple(int(v) for v in np.argwhere(nonfinite)[0])
            raise Mismatch(t["nan"].format(path=path, idx=list(i) if i else "", got=fmt_num(g[i])))
        if not np.allclose(g, w, rtol=rtol, atol=atol, equal_nan=True):
            over = np.abs(g - w) - (atol + rtol * np.abs(w))
            over = np.where(np.isnan(over), np.inf, over)
            i = tuple(int(v) for v in np.unravel_index(np.argmax(over), over.shape)) if over.ndim else ()
            err = float(np.nanmax(np.abs(g - w))) if g.size else 0.0
            raise Mismatch(t["value"].format(path=path, idx=list(i) if i else "", want=fmt_num(w[i]), got=fmt_num(g[i]), err=f"{err:.2e}"))
        return
    if isinstance(want, (list, tuple)):
        if isinstance(got, np.ndarray):
            got = got.tolist()
        if not isinstance(got, (list, tuple)):
            raise Mismatch(t["type"].format(path=path, want=type(want).__name__, got=kind(got)))
        if len(got) != len(want):
            raise Mismatch(t["len"].format(path=path, want=len(want), got=len(got)))
        for i, (g, w) in enumerate(zip(got, want)):
            compare(g, w, t, rtol, atol, f"{path}[{i}]")
        return
    if isinstance(want, dict):
        if not isinstance(got, dict):
            raise Mismatch(t["type"].format(path=path, want="dict", got=kind(got)))
        if set(got) != set(want):
            raise Mismatch(t["keys"].format(path=path, want=sorted(want), got=sorted(got)))
        for k in want:
            compare(got[k], want[k], t, rtol, atol, f"{path}['{k}']")
        return
    if isinstance(want, (int, np.integer, bool, np.bool_)) and not isinstance(want, (bool, np.bool_)):
        if not is_numeric_array_like(got) or np.ndim(got) != 0 or float(got) != float(want):
            raise Mismatch(t["exact"].format(path=path, want=preview(want), got=preview(got)))
        return
    if got != want:
        raise Mismatch(t["exact"].format(path=path, want=preview(want), got=preview(got)))


# ---------------- running ----------------

@contextlib.contextmanager
def time_limit(seconds):
    if not hasattr(signal, "setitimer"):  # Windows: the caller's process timeout still applies
        yield
        return

    def on_alarm(*_):
        raise CaseTimeout()
    old = signal.signal(signal.SIGALRM, on_alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def load(path, name, extra_globals=None):
    code = Path(path).read_text(encoding="utf-8")
    ns = {"__name__": name, "__file__": str(path), **(extra_globals or {})}
    exec(compile(code, str(path), "exec"), ns)
    return ns


def user_trace(e, code_path):
    frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == code_path]
    head = f"{type(e).__name__}: {e}".strip()
    where = [f"  line {f.lineno}, in {f.name}: {(f.line or '').strip()}" for f in frames[-3:]]
    return "\n".join([head[:600]] + where)


def call(fn, case, limit):
    args = copy.deepcopy(case.get("args", ()))
    kwargs = copy.deepcopy(case.get("kwargs", {}))
    out_buf = io.StringIO()
    with contextlib.redirect_stdout(out_buf):
        t0 = time.perf_counter()
        with time_limit(limit):
            out = fn(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
    return out, ms, out_buf.getvalue()


def judge(problem_dir, meta, code_path, mode, fn_name, lang):
    t = MSG.get(lang, MSG["zh"])
    problem_dir = Path(problem_dir)
    entry = meta.get("entry")
    fn_name = fn_name or entry
    code = Path(code_path).read_text(encoding="utf-8")
    res = {"status": "accepted", "passed": 0, "total": 0, "ms": 0.0, "cases": [], "message": None}

    problem = static_check(code, code_path, meta.get("banned") or [], t)
    if problem:
        res.update(status="compile_error", message=problem)
        return res

    tests = load(problem_dir / "tests.py", "tests")
    ref = load(problem_dir / "solution.py", "reference")[entry]
    cases = list(tests["cases"]())
    if mode == "run":
        cases = [c for c in cases if c.get("sample")] or cases[:2]
    res["total"] = len(cases)

    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout):
            ns = load(code_path, "solution")
    except BaseException as e:  # noqa: BLE001 - anything the module does at import time
        res.update(status="runtime_error", message=t["module"] + "\n" + user_trace(e, code_path))
        return res
    fn = ns.get(fn_name)
    if not callable(fn):
        res.update(status="compile_error", message=t["missing"].format(fn=fn_name))
        return res

    custom = tests.get("compare")
    rtol, atol = tests.get("RTOL", RTOL), tests.get("ATOL", ATOL)
    default_limit = float(meta.get("time_limit") or 2)
    first_fail = None
    for i, case in enumerate(cases):
        row = {"name": case.get("name") or f"case {i + 1}", "ok": False, "ms": None, "msg": None,
               "sample": bool(case.get("sample"))}
        try:
            want, _, _ = call(ref, case, 60)
        except BaseException as e:  # noqa: BLE001
            row["msg"] = t["ref"].format(err=f"{type(e).__name__}: {e}")
            res["status"] = "internal_error"
            res["cases"].append(row)
            break
        limit = float(case.get("limit") or default_limit)
        kind_ = None
        try:
            got, ms, out = call(fn, case, limit)
            row["ms"] = round(ms, 3)
            row["stdout"] = out[-2000:] or None
            if custom:
                msg = custom(got, want, case)
                if msg:
                    raise Mismatch(msg)
            else:
                compare(got, want, t, case.get("rtol", rtol), case.get("atol", atol), t["out"])
            row["ok"] = True
            res["passed"] += 1
            res["ms"] += ms
        except Mismatch as e:
            kind_, row["msg"] = "wrong_answer", str(e)
            row["got"] = preview(got)
        except CaseTimeout:
            kind_, row["msg"] = "time_limit", t["timeout"].format(limit=limit)
        except NotImplementedError:
            kind_, row["msg"] = "runtime_error", t["todo"]
        except BaseException as e:  # noqa: BLE001 - includes SystemExit / KeyboardInterrupt from user code
            kind_, row["msg"] = "runtime_error", user_trace(e, code_path)
        if row["sample"] or (kind_ and first_fail is None):
            row["input"] = {k: preview(v) for k, v in case.get("kwargs", {}).items()}
            row["expected"] = preview(want)
            if row["ok"] and "got" not in row:
                row["got"] = preview(got)
        if kind_ and first_fail is None:
            first_fail = i
            res["status"] = kind_
        res["cases"].append(row)
        if kind_ in ("time_limit",) or (kind_ == "runtime_error" and row["msg"] == t["todo"]):
            break  # the rest would just repeat it
    res["ms"] = round(res["ms"], 2)
    res["first_fail"] = first_fail
    if stdout.getvalue():
        res["module_stdout"] = stdout.getvalue()[-2000:]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--code", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["run", "submit"], default="submit")
    ap.add_argument("--fn")
    ap.add_argument("--lang", default="zh")
    a = ap.parse_args()
    np.seterr(all="ignore")  # overflow should show up as a wrong answer with inf/NaN, not a warning flood
    try:
        res = judge(a.problem, json.loads(a.meta), str(Path(a.code).resolve()), a.mode, a.fn, a.lang)
    except BaseException as e:  # noqa: BLE001
        res = {"status": "internal_error", "message": "".join(traceback.format_exception(e))[-3000:]}
    res["numpy"] = np.__version__
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()
