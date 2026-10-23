import numpy as np


def moe_forward(x, w_router, w1, w2, top_k):
    n, e = x.shape[0], w_router.shape[1]
    logits = x @ w_router
    probs = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs /= probs.sum(axis=1, keepdims=True)
    idx = np.argsort(-probs, axis=1, kind="stable")[:, :top_k]   # (N, k)
    gates = np.take_along_axis(probs, idx, axis=1)
    gates /= gates.sum(axis=1, keepdims=True)
    y = np.zeros_like(x, dtype=float)
    for ex in range(e):
        rows, slot = np.nonzero(idx == ex)
        if rows.size:
            out = np.maximum(x[rows] @ w1[ex], 0) @ w2[ex]
            np.add.at(y, rows, gates[rows, slot][:, None] * out)
    f = np.bincount(idx.ravel(), minlength=e) / (n * top_k)
    p = probs.mean(axis=0)
    return y, float(e * np.sum(f * p))
