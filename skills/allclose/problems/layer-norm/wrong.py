"""Buggy variants the tests must catch."""
import numpy as np


def unbiased_variance(x, gamma, beta, eps=1e-5):
    mu = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True, ddof=1)  # divides by D-1
    return (x - mu) / np.sqrt(var + eps) * gamma + beta


def eps_outside_sqrt(x, gamma, beta, eps=1e-5):
    mu = x.mean(axis=-1, keepdims=True)
    var = ((x - mu) ** 2).mean(axis=-1, keepdims=True)
    return (x - mu) / (np.sqrt(var) + eps) * gamma + beta


def one_pass_variance(x, gamma, beta, eps=1e-5):
    mu = x.mean(axis=-1, keepdims=True)
    var = (x * x).mean(axis=-1, keepdims=True) - mu * mu  # catastrophic cancellation
    return (x - mu) / np.sqrt(np.maximum(var, 0) + eps) * gamma + beta


def first_axis(x, gamma, beta, eps=1e-5):
    mu = x.mean(axis=0, keepdims=True)
    var = ((x - mu) ** 2).mean(axis=0, keepdims=True)
    return (x - mu) / np.sqrt(var + eps) * gamma + beta
