import numpy as np


def mlp_backward(x, y, w1, b1, w2, b2):
    n = x.shape[0]
    z1 = x @ w1 + b1
    h = np.maximum(z1, 0)
    logits = h @ w2 + b2
    shifted = logits - logits.max(axis=1, keepdims=True)
    logp = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
    loss = -logp[np.arange(n), y].mean()
    dlogits = np.exp(logp)
    dlogits[np.arange(n), y] -= 1
    dlogits /= n
    dz1 = (dlogits @ w2.T) * (z1 > 0)
    return {"loss": float(loss), "w1": x.T @ dz1, "b1": dz1.sum(axis=0), "w2": h.T @ dlogits, "b2": dlogits.sum(axis=0)}
