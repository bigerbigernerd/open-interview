"""Buggy variants the tests must catch."""
import numpy as np


def _heads(y, b, h, dh):
    return y.reshape(b, 1, h, dh).transpose(0, 2, 1, 3)


def attends_before_append(x, w_q, w_k, w_v, w_o, num_heads, k_cache, v_cache):
    b, _, d = x.shape
    dh = d // num_heads
    q = _heads(x @ w_q, b, num_heads, dh)
    s = q @ k_cache.transpose(0, 1, 3, 2) / np.sqrt(dh)  # misses its own position
    w = np.exp(s - s.max(axis=-1, keepdims=True))
    out = (w / w.sum(axis=-1, keepdims=True) @ v_cache).transpose(0, 2, 1, 3).reshape(b, 1, d)
    return out @ w_o, np.concatenate([k_cache, _heads(x @ w_k, b, num_heads, dh)], 2), np.concatenate([v_cache, _heads(x @ w_v, b, num_heads, dh)], 2)


def prepends(x, w_q, w_k, w_v, w_o, num_heads, k_cache, v_cache):
    b, _, d = x.shape
    dh = d // num_heads
    q = _heads(x @ w_q, b, num_heads, dh)
    k = np.concatenate([_heads(x @ w_k, b, num_heads, dh), k_cache], 2)
    v = np.concatenate([_heads(x @ w_v, b, num_heads, dh), v_cache], 2)
    s = q @ k.transpose(0, 1, 3, 2) / np.sqrt(dh)
    w = np.exp(s - s.max(axis=-1, keepdims=True))
    out = (w / w.sum(axis=-1, keepdims=True) @ v).transpose(0, 2, 1, 3).reshape(b, 1, d)
    return out @ w_o, k, v


def scale_by_d(x, w_q, w_k, w_v, w_o, num_heads, k_cache, v_cache):
    b, _, d = x.shape
    dh = d // num_heads
    q = _heads(x @ w_q, b, num_heads, dh)
    k = np.concatenate([k_cache, _heads(x @ w_k, b, num_heads, dh)], 2)
    v = np.concatenate([v_cache, _heads(x @ w_v, b, num_heads, dh)], 2)
    s = q @ k.transpose(0, 1, 3, 2) / np.sqrt(d)
    w = np.exp(s - s.max(axis=-1, keepdims=True))
    out = (w / w.sum(axis=-1, keepdims=True) @ v).transpose(0, 2, 1, 3).reshape(b, 1, d)
    return out @ w_o, k, v


def no_output_projection(x, w_q, w_k, w_v, w_o, num_heads, k_cache, v_cache):
    b, _, d = x.shape
    dh = d // num_heads
    q = _heads(x @ w_q, b, num_heads, dh)
    k = np.concatenate([k_cache, _heads(x @ w_k, b, num_heads, dh)], 2)
    v = np.concatenate([v_cache, _heads(x @ w_v, b, num_heads, dh)], 2)
    s = q @ k.transpose(0, 1, 3, 2) / np.sqrt(dh)
    w = np.exp(s - s.max(axis=-1, keepdims=True))
    return (w / w.sum(axis=-1, keepdims=True) @ v).transpose(0, 2, 1, 3).reshape(b, 1, d), k, v
