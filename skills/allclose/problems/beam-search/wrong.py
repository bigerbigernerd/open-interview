"""Buggy variants the tests must catch."""
import numpy as np


def _search(log_probs, start, eos, beam_size, max_len, stop_at_eos=True, keep_finished=True, norm=False):
    v = log_probs.shape[1]
    beams, finished = [((), 0.0)], []
    for _ in range(max_len):
        cands = [(seq + (t,), s + float(log_probs[seq[-1] if seq else start, t])) for seq, s in beams for t in range(v)]
        cands.sort(key=lambda c: -c[1])
        beams = []
        for seq, s in cands[:beam_size]:
            (finished if stop_at_eos and seq[-1] == eos else beams).append((seq, s))
        if not beams:
            break
    pool = (finished if keep_finished else []) + beams or finished
    seq, s = max(pool, key=lambda c: c[1] / (len(c[0]) if norm else 1))
    return list(seq), s


def greedy(log_probs, start, eos, beam_size, max_len):
    return _search(log_probs, start, eos, 1, max_len)


def eos_does_not_stop(log_probs, start, eos, beam_size, max_len):
    return _search(log_probs, start, eos, beam_size, max_len, stop_at_eos=False)


def drops_finished(log_probs, start, eos, beam_size, max_len):
    return _search(log_probs, start, eos, beam_size, max_len, keep_finished=False)


def length_normalized(log_probs, start, eos, beam_size, max_len):
    return _search(log_probs, start, eos, beam_size, max_len, norm=True)
