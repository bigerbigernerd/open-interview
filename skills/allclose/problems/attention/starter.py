import numpy as np


def attention(q: np.ndarray, k: np.ndarray, v: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
    """softmax(q kᵀ / sqrt(d)) v; mask (bool, True = keep) broadcasts to (..., Tq, Tk)."""
    raise NotImplementedError
