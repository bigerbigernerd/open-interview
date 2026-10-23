"""Buggy variants the tests must catch."""
import numpy as np


def _sig(z):
    return 1 / (1 + np.exp(-z))


def no_divide_by_n(X, y, lr=0.1, epochs=100, l2=0.0):
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(epochs):
        err = _sig(X @ w + b) - y
        w, b = w - lr * (X.T @ err + l2 * w), b - lr * err.sum()
    return w, float(b)


def regularizes_bias(X, y, lr=0.1, epochs=100, l2=0.0):
    n = len(y)
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(epochs):
        err = _sig(X @ w + b) - y
        w, b = w - lr * (X.T @ err / n + l2 * w), b - lr * (err.mean() + l2 * b)
    return w, float(b)


def wrong_sign(X, y, lr=0.1, epochs=100, l2=0.0):
    n = len(y)
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(epochs):
        err = y - _sig(X @ w + b)
        w, b = w - lr * (X.T @ err / n + l2 * w), b - lr * err.mean()
    return w, float(b)


def stale_bias_gradient(X, y, lr=0.1, epochs=100, l2=0.0):
    n = len(y)
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(epochs):
        w = w - lr * (X.T @ (_sig(X @ w + b) - y) / n + l2 * w)
        b = b - lr * (_sig(X @ w + b) - y).mean()  # uses the new w
    return w, float(b)
