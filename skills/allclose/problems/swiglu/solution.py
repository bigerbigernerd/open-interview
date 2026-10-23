import numpy as np


def swiglu_ffn(x, w_gate, w_up, w_down):
    g = x @ w_gate
    return (g / (1 + np.exp(-g)) * (x @ w_up)) @ w_down  # silu(g) = g * sigmoid(g)
