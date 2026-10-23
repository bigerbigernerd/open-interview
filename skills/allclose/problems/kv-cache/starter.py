import numpy as np


def decode_step(x, w_q, w_k, w_v, w_o, num_heads, k_cache, v_cache):
    """x (B, 1, D); caches (B, H, T, Dh). Returns (y (B, 1, D), new_k_cache, new_v_cache)."""
    raise NotImplementedError
