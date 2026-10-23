import numpy as np


def top_k_top_p(logits: np.ndarray, temperature: float = 1.0, top_k: int = 0, top_p: float = 1.0) -> np.ndarray:
    """Probabilities after temperature, top-k and top-p filtering; same shape as logits."""
    raise NotImplementedError
