"""Buggy variants the tests must catch."""
import numpy as np


def _attn(q, k, v, causal, scale):
    t = q.shape[2]
    s = q @ k.transpose(0, 1, 3, 2) / scale
    if causal:
        s = np.where(np.tril(np.ones((t, t), dtype=bool)), s, -np.inf)
    e = np.exp(s - s.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True) @ v


def tiled_heads(q, k, v, causal=False):
    g = q.shape[1] // k.shape[1]
    return _attn(q, np.tile(k, (1, g, 1, 1)), np.tile(v, (1, g, 1, 1)), causal, np.sqrt(q.shape[-1]))


def no_scaling(q, k, v, causal=False):
    g = q.shape[1] // k.shape[1]
    return _attn(q, np.repeat(k, g, 1), np.repeat(v, g, 1), causal, 1.0)


def ignores_causal(q, k, v, causal=False):
    g = q.shape[1] // k.shape[1]
    return _attn(q, np.repeat(k, g, 1), np.repeat(v, g, 1), False, np.sqrt(q.shape[-1]))
