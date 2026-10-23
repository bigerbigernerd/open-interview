import numpy as np


def _table(rng, v, eos_bias=0.0):
    z = rng.normal(size=(v, v)) * 2
    z[:, 0] += eos_bias  # token 0 is eos in every case
    z -= z.max(axis=1, keepdims=True)
    return z - np.log(np.exp(z).sum(axis=1, keepdims=True))


def cases():
    rng = np.random.default_rng(21)
    return [
        dict(name="V=4, beam 2, 3 steps", kwargs=dict(log_probs=_table(rng, 4), start=1, eos=0, beam_size=2, max_len=3), sample=True),
        dict(name="beam 1 is greedy", kwargs=dict(log_probs=_table(rng, 5), start=2, eos=0, beam_size=1, max_len=4), sample=True),
        dict(name="likely eos (early finish)", kwargs=dict(log_probs=_table(rng, 6, eos_bias=2.0), start=1, eos=0, beam_size=3, max_len=6)),
        dict(name="unlikely eos", kwargs=dict(log_probs=_table(rng, 6, eos_bias=-3.0), start=3, eos=0, beam_size=3, max_len=5)),
        dict(name="max_len 1", kwargs=dict(log_probs=_table(rng, 5), start=1, eos=0, beam_size=4, max_len=1)),
        dict(name="V=8, beam 4, 7 steps", kwargs=dict(log_probs=_table(rng, 8, eos_bias=0.5), start=5, eos=0, beam_size=4, max_len=7)),
        dict(name="V=10, beam 5, 6 steps", kwargs=dict(log_probs=_table(rng, 10, eos_bias=1.0), start=2, eos=0, beam_size=5, max_len=6)),
        dict(name="V=6, beam 3, 8 steps", kwargs=dict(log_probs=_table(rng, 6, eos_bias=1.5), start=4, eos=0, beam_size=3, max_len=8)),
    ]
