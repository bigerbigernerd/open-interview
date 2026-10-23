import numpy as np


def decode_step(x, w_q, w_k, w_v, w_o, num_heads, k_cache, v_cache):
    b, _, d = x.shape
    dh = d // num_heads

    def heads(y):  # (B, 1, D) -> (B, H, 1, Dh)
        return y.reshape(b, 1, num_heads, dh).transpose(0, 2, 1, 3)

    q = heads(x @ w_q)
    k = np.concatenate([k_cache, heads(x @ w_k)], axis=2)
    v = np.concatenate([v_cache, heads(x @ w_v)], axis=2)
    s = q @ k.transpose(0, 1, 3, 2) / np.sqrt(dh)  # (B, H, 1, T+1)
    w = np.exp(s - s.max(axis=-1, keepdims=True))
    w /= w.sum(axis=-1, keepdims=True)
    out = (w @ v).transpose(0, 2, 1, 3).reshape(b, 1, d)
    return out @ w_o, k, v
