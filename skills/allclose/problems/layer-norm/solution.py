import numpy as np


def layer_norm(x, gamma, beta, eps=1e-5):
    mu = x.mean(axis=-1, keepdims=True)
    xc = x - mu
    var = (xc * xc).mean(axis=-1, keepdims=True)  # two-pass variance: no cancellation
    return xc / np.sqrt(var + eps) * gamma + beta
