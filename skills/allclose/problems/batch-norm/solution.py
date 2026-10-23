import numpy as np


def batch_norm_train(x, gamma, beta, running_mean, running_var, momentum=0.1, eps=1e-5):
    axes = (0,) + tuple(range(2, x.ndim))
    shape = [1] * x.ndim
    shape[1] = x.shape[1]
    n = x.size // x.shape[1]
    mean = x.mean(axis=axes)
    var = x.var(axis=axes)  # biased, used to normalize
    y = (x - mean.reshape(shape)) / np.sqrt(var.reshape(shape) + eps) * gamma.reshape(shape) + beta.reshape(shape)
    new_mean = (1 - momentum) * running_mean + momentum * mean
    new_var = (1 - momentum) * running_var + momentum * var * n / (n - 1)  # unbiased for the running estimate
    return y, new_mean, new_var
