"""Buggy variants the tests must catch (`allclose.py check softmax`)."""
import numpy as np


def no_max_shift(x, axis=-1):
    e = np.exp(x)  # overflows to inf -> nan
    return e / np.sum(e, axis=axis, keepdims=True)


def no_keepdims(x, axis=-1):
    e = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e / np.sum(e, axis=axis)  # broadcasts along the wrong axis


def global_max(x, axis=-1):
    e = np.exp(x - np.max(x))  # rows far below the global max underflow to 0/0
    return e / np.sum(e, axis=axis, keepdims=True)


def ignores_axis(x, axis=-1):
    e = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e / np.sum(e, axis=-1, keepdims=True)
