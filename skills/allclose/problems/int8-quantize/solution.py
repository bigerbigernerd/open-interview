import numpy as np


def quantize_int8(w):
    amax = np.abs(w).max(axis=1)
    scale = np.where(amax > 0, amax / 127, 1.0)
    q = np.clip(np.round(w / scale[:, None]), -127, 127).astype(np.int8)
    return q, scale
