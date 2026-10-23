"""Buggy variants the tests must catch."""
import numpy as np


def _softmax(z):
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def _topk(z, k):
    if 0 < k < z.shape[-1]:
        kth = np.sort(z, axis=-1)[..., -k][..., None]
        z = np.where(z >= kth, z, -np.inf)
    return z


def _topp(p, top_p, inclusive_cross=True):
    order = np.argsort(-p, axis=-1)
    sp = np.take_along_axis(p, order, axis=-1)
    c = np.cumsum(sp, axis=-1)
    keep_sorted = (c - sp < top_p) if inclusive_cross else (c <= top_p)
    keep = np.zeros_like(keep_sorted)
    np.put_along_axis(keep, order, keep_sorted, axis=-1)
    q = np.where(keep, p, 0.0)
    return q / q.sum(axis=-1, keepdims=True)


def drops_crossing_token(logits, temperature=1.0, top_k=0, top_p=1.0):
    p = _softmax(_topk(logits / temperature, top_k))
    return _topp(p, top_p, inclusive_cross=False) if top_p < 1 else p


def temperature_after_softmax(logits, temperature=1.0, top_k=0, top_p=1.0):
    p = _softmax(_topk(logits, top_k)) / temperature
    p = p / p.sum(axis=-1, keepdims=True)
    return _topp(p, top_p) if top_p < 1 else p


def top_p_before_top_k(logits, temperature=1.0, top_k=0, top_p=1.0):
    p = _softmax(logits / temperature)
    if top_p < 1:
        p = _topp(p, top_p)
    if 0 < top_k < p.shape[-1]:
        kth = np.sort(p, axis=-1)[..., -top_k][..., None]
        p = np.where(p >= kth, p, 0.0)
        p = p / p.sum(axis=-1, keepdims=True)
    return p


def no_renormalize(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = logits / temperature
    p = _softmax(z)
    if 0 < top_k < z.shape[-1]:
        kth = np.sort(z, axis=-1)[..., -top_k][..., None]
        p = np.where(z >= kth, p, 0.0)  # filtered but never renormalized
    return p
