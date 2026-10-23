import numpy as np


def cross_entropy(logits: np.ndarray, labels: np.ndarray, label_smoothing: float = 0.0) -> float:
    """Mean cross-entropy over the batch. logits (N, C), labels (N,) ints."""
    raise NotImplementedError
