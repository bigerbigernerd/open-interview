import numpy as np


def multi_head_attention(x: np.ndarray, w_q: np.ndarray, w_k: np.ndarray, w_v: np.ndarray, w_o: np.ndarray,
                         num_heads: int, causal: bool = False) -> np.ndarray:
    """Self-attention over x (B, T, D) with num_heads heads; returns (B, T, D)."""
    raise NotImplementedError
