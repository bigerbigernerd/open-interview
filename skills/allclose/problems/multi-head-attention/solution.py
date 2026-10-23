import numpy as np


def multi_head_attention(x, w_q, w_k, w_v, w_o, num_heads, causal=False):
    b, t, d = x.shape
    dh = d // num_heads

    def split(y):  # (B, T, D) -> (B, H, T, Dh)
        return y.reshape(b, t, num_heads, dh).transpose(0, 2, 1, 3)

    q, k, v = split(x @ w_q), split(x @ w_k), split(x @ w_v)
    s = q @ k.transpose(0, 1, 3, 2) / np.sqrt(dh)
    if causal:
        s = np.where(np.tril(np.ones((t, t), dtype=bool)), s, -np.inf)
    s = s - s.max(axis=-1, keepdims=True)
    w = np.exp(s)
    w /= w.sum(axis=-1, keepdims=True)
    out = (w @ v).transpose(0, 2, 1, 3).reshape(b, t, d)
    return out @ w_o
