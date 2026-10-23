import numpy as np


def apply_rope(x: np.ndarray, positions: np.ndarray, base: float = 10000.0) -> np.ndarray:
    """Rotary embedding, HF LLaMA "rotate half" convention. x (..., T, D), positions (T,)."""
    raise NotImplementedError
