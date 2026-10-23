import numpy as np


def merge_attention_states(o1, lse1, o2, lse2):
    """Combine attention over two disjoint key sets. o (..., T, D), lse (..., T). Returns (o, lse)."""
    raise NotImplementedError
