"""Buggy variants the tests must catch."""
import numpy as np


def _softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def no_scale(q, k, v, mask=None):
    s = q @ np.swapaxes(k, -1, -2)
    if mask is not None:
        s = np.where(mask, s, -np.inf)
    return _softmax(s) @ v


def scale_by_d(q, k, v, mask=None):
    s = q @ np.swapaxes(k, -1, -2) / q.shape[-1]
    if mask is not None:
        s = np.where(mask, s, -np.inf)
    return _softmax(s) @ v


def mask_after_softmax(q, k, v, mask=None):
    w = _softmax(q @ np.swapaxes(k, -1, -2) / np.sqrt(q.shape[-1]))
    if mask is not None:
        w = w * mask  # rows no longer sum to 1
    return w @ v


def mask_to_zero(q, k, v, mask=None):
    s = q @ np.swapaxes(k, -1, -2) / np.sqrt(q.shape[-1])
    if mask is not None:
        s = s * mask  # a masked score of 0 still gets weight
    return _softmax(s) @ v


def no_max_shift(q, k, v, mask=None):
    s = q @ np.swapaxes(k, -1, -2) / np.sqrt(q.shape[-1])
    if mask is not None:
        s = np.where(mask, s, -np.inf)
    e = np.exp(s)
    return e / e.sum(axis=-1, keepdims=True) @ v


def softmax_over_queries(q, k, v, mask=None):
    s = q @ np.swapaxes(k, -1, -2) / np.sqrt(q.shape[-1])
    if mask is not None:
        s = np.where(mask, s, -1e9)
    e = np.exp(s - s.max(axis=-2, keepdims=True))
    return e / e.sum(axis=-2, keepdims=True) @ v
