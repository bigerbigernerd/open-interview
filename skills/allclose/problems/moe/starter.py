import numpy as np


def moe_forward(x, w_router, w1, w2, top_k):
    """Top-k routed MoE with renormalized gates. Returns (y (N, D), aux_loss float)."""
    raise NotImplementedError
