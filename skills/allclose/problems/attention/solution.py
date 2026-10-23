import numpy as np


def attention(q, k, v, mask=None):
    d = q.shape[-1]
    scores = q @ np.swapaxes(k, -1, -2) / np.sqrt(d)
    if mask is not None:
        scores = np.where(mask, scores, -np.inf)
    scores = scores - scores.max(axis=-1, keepdims=True)
    w = np.exp(scores)
    w = w / w.sum(axis=-1, keepdims=True)
    return w @ v
