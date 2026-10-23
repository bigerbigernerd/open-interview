import numpy as np


def logistic_regression(X, y, lr=0.1, epochs=100, l2=0.0):
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    for _ in range(epochs):
        p = 1 / (1 + np.exp(-(X @ w + b)))
        err = p - y
        dw = X.T @ err / n + l2 * w
        db = err.mean()
        w = w - lr * dw
        b = b - lr * db
    return w, float(b)
