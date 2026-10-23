"""Buggy variants the tests must catch."""
import numpy as np


def subtracts_mean(x, weight, eps=1e-6):
    xc = x - x.mean(axis=-1, keepdims=True)
    return xc / np.sqrt(np.mean(xc * xc, axis=-1, keepdims=True) + eps) * weight


def eps_outside_sqrt(x, weight, eps=1e-6):
    return x / (np.sqrt(np.mean(x * x, axis=-1, keepdims=True)) + eps) * weight


def sum_not_mean(x, weight, eps=1e-6):
    return x / np.sqrt(np.sum(x * x, axis=-1, keepdims=True) + eps) * weight


def no_weight(x, weight, eps=1e-6):
    return x / np.sqrt(np.mean(x * x, axis=-1, keepdims=True) + eps)
