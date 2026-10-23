import numpy as np


def top_k_top_p(logits, temperature=1.0, top_k=0, top_p=1.0):
    z = np.asarray(logits, dtype=float) / temperature
    if 0 < top_k < z.shape[-1]:
        kth = np.sort(z, axis=-1)[..., -top_k][..., None]
        z = np.where(z >= kth, z, -np.inf)
    p = np.exp(z - z.max(axis=-1, keepdims=True))
    p /= p.sum(axis=-1, keepdims=True)
    if top_p < 1.0:
        order = np.argsort(-p, axis=-1)
        sorted_p = np.take_along_axis(p, order, axis=-1)
        before = np.cumsum(sorted_p, axis=-1) - sorted_p  # mass ranked strictly before each token
        keep_sorted = before < top_p
        keep = np.zeros_like(keep_sorted)
        np.put_along_axis(keep, order, keep_sorted, axis=-1)
        p = np.where(keep, p, 0.0)
        p /= p.sum(axis=-1, keepdims=True)
    return p
