"""Buggy variants the tests must catch."""
import numpy as np


def alpha_not_divided(x, w, a, b, alpha, merge=False):
    if merge:
        return w + alpha * (a @ b)
    return x @ w + alpha * (x @ a) @ b


def r_over_alpha(x, w, a, b, alpha, merge=False):
    s = a.shape[1] / alpha
    return w + s * (a @ b) if merge else x @ w + s * (x @ a) @ b


def no_scaling(x, w, a, b, alpha, merge=False):
    return w + a @ b if merge else x @ w + (x @ a) @ b


def merge_returns_output(x, w, a, b, alpha, merge=False):
    return x @ w + alpha / a.shape[1] * (x @ a) @ b
