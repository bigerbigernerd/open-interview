import numpy as np


def lora_linear(x, w, a, b, alpha, merge=False):
    scaling = alpha / a.shape[1]
    if merge:
        return w + scaling * (a @ b)
    return x @ w + scaling * ((x @ a) @ b)
