"""Buggy variants the tests must catch."""
import numpy as np


def adam_with_l2(param, grad, m, v, t, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0.01):
    grad = grad + weight_decay * param  # coupled L2, not AdamW
    m = beta1 * m + (1 - beta1) * grad
    v = beta2 * v + (1 - beta2) * grad * grad
    return param - lr * (m / (1 - beta1 ** t)) / (np.sqrt(v / (1 - beta2 ** t)) + eps), m, v


def no_bias_correction(param, grad, m, v, t, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0.01):
    param = param * (1 - lr * weight_decay)
    m = beta1 * m + (1 - beta1) * grad
    v = beta2 * v + (1 - beta2) * grad * grad
    return param - lr * m / (np.sqrt(v) + eps), m, v


def eps_inside_sqrt(param, grad, m, v, t, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0.01):
    param = param * (1 - lr * weight_decay)
    m = beta1 * m + (1 - beta1) * grad
    v = beta2 * v + (1 - beta2) * grad * grad
    return param - lr * (m / (1 - beta1 ** t)) / np.sqrt(v / (1 - beta2 ** t) + eps), m, v


def decay_after_update(param, grad, m, v, t, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8, weight_decay=0.01):
    m = beta1 * m + (1 - beta1) * grad
    v = beta2 * v + (1 - beta2) * grad * grad
    param = param - lr * (m / (1 - beta1 ** t)) / (np.sqrt(v / (1 - beta2 ** t)) + eps)
    return param * (1 - lr * weight_decay), m, v
