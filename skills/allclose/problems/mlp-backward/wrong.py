"""Buggy variants the tests must catch."""
import numpy as np


def _fwd(x, y, w1, b1, w2, b2):
    n = x.shape[0]
    z1 = x @ w1 + b1
    h = np.maximum(z1, 0)
    logits = h @ w2 + b2
    s = logits - logits.max(axis=1, keepdims=True)
    logp = s - np.log(np.exp(s).sum(axis=1, keepdims=True))
    return n, z1, h, logp


def summed_not_mean(x, y, w1, b1, w2, b2):
    n, z1, h, logp = _fwd(x, y, w1, b1, w2, b2)
    d = np.exp(logp)
    d[np.arange(n), y] -= 1  # forgot / N
    dz1 = (d @ w2.T) * (z1 > 0)
    return {"loss": float(-logp[np.arange(n), y].mean()), "w1": x.T @ dz1, "b1": dz1.sum(0), "w2": h.T @ d, "b2": d.sum(0)}


def no_relu_mask(x, y, w1, b1, w2, b2):
    n, z1, h, logp = _fwd(x, y, w1, b1, w2, b2)
    d = np.exp(logp)
    d[np.arange(n), y] -= 1
    d /= n
    dz1 = d @ w2.T
    return {"loss": float(-logp[np.arange(n), y].mean()), "w1": x.T @ dz1, "b1": dz1.sum(0), "w2": h.T @ d, "b2": d.sum(0)}


def forgot_one_hot(x, y, w1, b1, w2, b2):
    n, z1, h, logp = _fwd(x, y, w1, b1, w2, b2)
    d = np.exp(logp) / n
    dz1 = (d @ w2.T) * (z1 > 0)
    return {"loss": float(-logp[np.arange(n), y].mean()), "w1": x.T @ dz1, "b1": dz1.sum(0), "w2": h.T @ d, "b2": d.sum(0)}


def bias_grad_mean(x, y, w1, b1, w2, b2):
    n, z1, h, logp = _fwd(x, y, w1, b1, w2, b2)
    d = np.exp(logp)
    d[np.arange(n), y] -= 1
    d /= n
    dz1 = (d @ w2.T) * (z1 > 0)
    return {"loss": float(-logp[np.arange(n), y].mean()), "w1": x.T @ dz1, "b1": dz1.mean(0), "w2": h.T @ d, "b2": d.mean(0)}
