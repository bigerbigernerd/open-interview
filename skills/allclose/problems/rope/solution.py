import numpy as np


def apply_rope(x, positions, base=10000.0):
    d = x.shape[-1]
    inv_freq = base ** (-np.arange(0, d, 2) / d)              # (D/2,)
    theta = np.outer(np.asarray(positions, dtype=float), inv_freq)  # (T, D/2)
    theta = np.concatenate([theta, theta], axis=-1)            # (T, D)
    half = d // 2
    rotated = np.concatenate([-x[..., half:], x[..., :half]], axis=-1)
    return x * np.cos(theta) + rotated * np.sin(theta)
