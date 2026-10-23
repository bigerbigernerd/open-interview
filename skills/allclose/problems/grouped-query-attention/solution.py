import numpy as np


def grouped_query_attention(q, k, v, causal=False):
    g = q.shape[1] // k.shape[1]
    k = np.repeat(k, g, axis=1)
    v = np.repeat(v, g, axis=1)
    t = q.shape[2]
    s = q @ k.transpose(0, 1, 3, 2) / np.sqrt(q.shape[-1])
    if causal:
        s = np.where(np.tril(np.ones((t, t), dtype=bool)), s, -np.inf)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s)
    return w / w.sum(axis=-1, keepdims=True) @ v
