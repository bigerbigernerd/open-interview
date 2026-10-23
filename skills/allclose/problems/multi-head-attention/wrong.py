"""Buggy variants the tests must catch."""
import numpy as np


def _attend(q, k, v, causal, scale):
    t = q.shape[-2]
    s = q @ np.swapaxes(k, -1, -2) / scale
    if causal:
        s = np.where(np.tril(np.ones((t, t), dtype=bool)), s, -np.inf)
    e = np.exp(s - s.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True) @ v


def reshape_without_transpose(x, w_q, w_k, w_v, w_o, num_heads, causal=False):
    b, t, d = x.shape
    dh = d // num_heads
    q, k, v = ((x @ w).reshape(b, num_heads, t, dh) for w in (w_q, w_k, w_v))  # mixes positions across heads
    out = _attend(q, k, v, causal, np.sqrt(dh)).reshape(b, t, d)
    return out @ w_o


def interleaved_heads(x, w_q, w_k, w_v, w_o, num_heads, causal=False):
    b, t, d = x.shape
    dh = d // num_heads
    q, k, v = ((x @ w).reshape(b, t, dh, num_heads).transpose(0, 3, 1, 2) for w in (w_q, w_k, w_v))
    out = _attend(q, k, v, causal, np.sqrt(dh)).transpose(0, 2, 3, 1).reshape(b, t, d)
    return out @ w_o


def causal_upper_triangle(x, w_q, w_k, w_v, w_o, num_heads, causal=False):
    b, t, d = x.shape
    dh = d // num_heads
    q, k, v = ((x @ w).reshape(b, t, num_heads, dh).transpose(0, 2, 1, 3) for w in (w_q, w_k, w_v))
    s = q @ np.swapaxes(k, -1, -2) / np.sqrt(dh)
    if causal:
        s = np.where(np.triu(np.ones((t, t), dtype=bool)), s, -np.inf)  # looks at the future
    e = np.exp(s - s.max(axis=-1, keepdims=True))
    out = (e / e.sum(axis=-1, keepdims=True) @ v).transpose(0, 2, 1, 3).reshape(b, t, d)
    return out @ w_o


def scale_by_model_dim(x, w_q, w_k, w_v, w_o, num_heads, causal=False):
    b, t, d = x.shape
    dh = d // num_heads
    q, k, v = ((x @ w).reshape(b, t, num_heads, dh).transpose(0, 2, 1, 3) for w in (w_q, w_k, w_v))
    out = _attend(q, k, v, causal, np.sqrt(d)).transpose(0, 2, 1, 3).reshape(b, t, d)
    return out @ w_o


def no_output_projection(x, w_q, w_k, w_v, w_o, num_heads, causal=False):
    b, t, d = x.shape
    dh = d // num_heads
    q, k, v = ((x @ w).reshape(b, t, num_heads, dh).transpose(0, 2, 1, 3) for w in (w_q, w_k, w_v))
    return _attend(q, k, v, causal, np.sqrt(dh)).transpose(0, 2, 1, 3).reshape(b, t, d)
