import numpy as np


def grouped_query_attention(q, k, v, causal=False):
    """q (B, Hq, T, D), k/v (B, Hkv, T, D); query head h uses kv head h // (Hq // Hkv)."""
    raise NotImplementedError
