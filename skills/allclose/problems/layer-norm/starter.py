import numpy as np


def layer_norm(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Normalize x over its last dimension, then scale by gamma and shift by beta."""
    raise NotImplementedError
