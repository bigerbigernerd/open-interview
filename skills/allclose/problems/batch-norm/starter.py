import numpy as np


def batch_norm_train(x, gamma, beta, running_mean, running_var, momentum=0.1, eps=1e-5):
    """Training-mode BatchNorm over channel axis 1. Returns (y, new_running_mean, new_running_var)."""
    raise NotImplementedError
