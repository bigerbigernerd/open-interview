"""Buggy variants the tests must catch."""
import numpy as np


def _parts(x):
    axes = (0,) + tuple(range(2, x.ndim))
    shape = [1] * x.ndim
    shape[1] = x.shape[1]
    return axes, shape, x.size // x.shape[1]


def biased_running_var(x, gamma, beta, running_mean, running_var, momentum=0.1, eps=1e-5):
    axes, shape, n = _parts(x)
    mean, var = x.mean(axis=axes), x.var(axis=axes)
    y = (x - mean.reshape(shape)) / np.sqrt(var.reshape(shape) + eps) * gamma.reshape(shape) + beta.reshape(shape)
    return y, (1 - momentum) * running_mean + momentum * mean, (1 - momentum) * running_var + momentum * var


def momentum_reversed(x, gamma, beta, running_mean, running_var, momentum=0.1, eps=1e-5):
    axes, shape, n = _parts(x)
    mean, var = x.mean(axis=axes), x.var(axis=axes)
    y = (x - mean.reshape(shape)) / np.sqrt(var.reshape(shape) + eps) * gamma.reshape(shape) + beta.reshape(shape)
    return y, momentum * running_mean + (1 - momentum) * mean, momentum * running_var + (1 - momentum) * var * n / (n - 1)


def batch_axis_only(x, gamma, beta, running_mean, running_var, momentum=0.1, eps=1e-5):
    axes, shape, n = _parts(x)
    mean, var = x.mean(axis=0, keepdims=True), x.var(axis=0, keepdims=True)  # ignores H, W
    y = (x - mean) / np.sqrt(var + eps) * gamma.reshape(shape) + beta.reshape(shape)
    m, v = x.mean(axis=axes), x.var(axis=axes)
    return y, (1 - momentum) * running_mean + momentum * m, (1 - momentum) * running_var + momentum * v * n / (n - 1)


def unbiased_normalization(x, gamma, beta, running_mean, running_var, momentum=0.1, eps=1e-5):
    axes, shape, n = _parts(x)
    mean, var = x.mean(axis=axes), x.var(axis=axes, ddof=1)
    y = (x - mean.reshape(shape)) / np.sqrt(var.reshape(shape) + eps) * gamma.reshape(shape) + beta.reshape(shape)
    return y, (1 - momentum) * running_mean + momentum * mean, (1 - momentum) * running_var + momentum * var
