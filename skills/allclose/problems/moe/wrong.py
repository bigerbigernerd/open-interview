"""Buggy variants the tests must catch."""
import numpy as np


def _route(x, w_router, top_k):
    z = x @ w_router
    p = np.exp(z - z.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    return p, np.argsort(-p, axis=1, kind="stable")[:, :top_k]


def _combine(x, w1, w2, idx, gates):
    y = np.zeros_like(x, dtype=float)
    for n in range(x.shape[0]):
        for s, ex in enumerate(idx[n]):
            y[n] += gates[n, s] * (np.maximum(x[n] @ w1[ex], 0) @ w2[ex])
    return y


def _aux(p, idx, top_k):
    e = p.shape[1]
    return float(e * np.sum(np.bincount(idx.ravel(), minlength=e) / (p.shape[0] * top_k) * p.mean(0)))


def raw_probability_gates(x, w_router, w1, w2, top_k):
    p, idx = _route(x, w_router, top_k)
    return _combine(x, w1, w2, idx, np.take_along_axis(p, idx, 1)), _aux(p, idx, top_k)


def uniform_gates(x, w_router, w1, w2, top_k):
    p, idx = _route(x, w_router, top_k)
    return _combine(x, w1, w2, idx, np.full(idx.shape, 1 / top_k)), _aux(p, idx, top_k)


def aux_counts_top1_only(x, w_router, w1, w2, top_k):
    p, idx = _route(x, w_router, top_k)
    g = np.take_along_axis(p, idx, 1)
    e = p.shape[1]
    f = np.bincount(idx[:, 0], minlength=e) / p.shape[0]
    return _combine(x, w1, w2, idx, g / g.sum(1, keepdims=True)), float(e * np.sum(f * p.mean(0)))


def aux_without_e(x, w_router, w1, w2, top_k):
    p, idx = _route(x, w_router, top_k)
    g = np.take_along_axis(p, idx, 1)
    return _combine(x, w1, w2, idx, g / g.sum(1, keepdims=True)), _aux(p, idx, top_k) / p.shape[1]
