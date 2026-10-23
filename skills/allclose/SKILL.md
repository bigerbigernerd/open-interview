---
name: allclose
description: allclose · 手撕 — hand-coding practice for ML / LLM interviews, judged locally. 30 problems (softmax, cross-entropy, LayerNorm/RMSNorm, attention, MHA, GQA, RoPE, KV cache, top-k/top-p, beam search, BPE, MoE, LoRA, DPO, PPO, GRPO, FlashAttention merge, speculative decoding, AUC, NMS, conv2d, k-means…), each with tests that run the candidate's numpy code on their own machine and compare it with a reference within rtol/atol. Use when the user wants to practice 手撕代码 for 大模型 / 算法岗 interviews, implement attention or other ML building blocks from scratch and have them checked, or be asked follow-up questions about their implementation.
---

# allclose · 手撕

The user writes a numpy implementation; `scripts/allclose.py` judges it in a separate local process
against a reference solution (pass = `np.allclose` on every case, including overflow, edge-case and
large-input cases). Nothing is uploaded. All commands run from this skill's directory.

```bash
python3 scripts/allclose.py list [--track ml|dl|llm] [--difficulty easy|medium|hard]   # ✓ = passed
python3 scripts/allclose.py show attention          # statement (ID = slug or number); --lang en
python3 scripts/allclose.py pull attention          # writes the starter to ~/allclose/attention.py
python3 scripts/allclose.py test attention --run    # sample cases only
python3 scripts/allclose.py test attention --json   # all cases; exit 0 = accepted, 1 = not yet, 2 = could not judge
python3 scripts/allclose.py hint attention          # next curated hint
python3 scripts/allclose.py followups attention     # interviewer follow-ups for after it passes
python3 scripts/allclose.py solution attention      # reference (only when the user asks for it)
python3 scripts/allclose.py progress
```

Judging needs numpy. The script uses the current python if it has numpy, else `uv run --with numpy`,
else it reports `env_error` with install instructions (or set `ALLCLOSE_PYTHON=/path/to/python`).

## Running a 手撕 session

1. Pick a problem that fits the target role and level (`list`, then `show`). LLM roles: attention, MHA,
   RoPE, KV cache, GQA, sampling, MoE, DPO/PPO/GRPO. Search / ads / CV: AUC, NMS, logistic regression,
   k-means, conv2d. Prefer one the user has not passed yet.
2. State the problem in your own words with the exact signature, shapes and conventions from `show`
   (the conventions matter: e.g. RoPE uses "rotate half", top-p keeps the token that crosses p).
3. Run `pull`, tell the user the file path (`~/allclose/<id>.py`), and let them write it in their editor.
   Do not write the solution for them. Ask for their approach and complexity first, like an interviewer.
4. When they say they're done, run `test <id> --json` and read the result:
   - `accepted` → say so briefly, then ask 2-3 questions from `followups` (one at a time, tied to their
     code), and assess the answers.
   - `wrong_answer` / `runtime_error` / `time_limit` / `compile_error` → report the first failing case
     (`cases[i].msg`, `input`, `expected`, `got`) in one or two lines and nudge, Socratically. Escalate to
     `hint` only when they are stuck; never paste the reference unless they ask.
5. At the end, summarize: passed or not, attempts, what the bugs were (numerical stability, axes,
   masking, conventions), and how they handled the follow-ups.

The browser version of the same thing (editor, run/submit, results, AI follow-ups through a local
Claude Code / Codex / agy / Cursor / OpenCode CLI) is the 手撕 tab of the studio:
`python3 ../mock-interviewer/scripts/studio.py`, then open `/#allclose`.

## Adding a problem

One folder per problem in `problems/<id>/`: `problem.yml` (num, title, difficulty, track, topics, entry,
statement, hints and follow-ups in zh + en), `starter.py`, `solution.py`, `tests.py` (`cases()` returns
dicts with `name`, `kwargs`, optional `sample`, `limit`, `rtol`, `atol`) and `wrong.py` (buggy variants
the tests must catch). Then:

```bash
python3 ../../tools/build.py                 # validates and rebuilds data/problems.json (needs PyYAML)
python3 scripts/allclose.py check <id>       # reference passes; starter and every wrong.py variant fail
```
