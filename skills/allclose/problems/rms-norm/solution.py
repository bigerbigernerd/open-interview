import numpy as np


def rms_norm(x, weight, eps=1e-6):
    ms = np.mean(x * x, axis=-1, keepdims=True)
    return x / np.sqrt(ms + eps) * weight
