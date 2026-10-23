import numpy as np


def lora_linear(x, w, a, b, alpha, merge=False):
    """y = x @ w + (alpha / r) * (x @ a) @ b, or the merged weight when merge=True."""
    raise NotImplementedError
