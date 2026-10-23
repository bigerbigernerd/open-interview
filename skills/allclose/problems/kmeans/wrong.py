"""Buggy variants the tests must catch."""
import numpy as np


def _assign(X, c):
    return ((X[:, None, :] - c[None, :, :]) ** 2).sum(-1).argmin(1)


def empty_cluster_nan(X, init_centroids, n_iters):
    c = np.array(init_centroids, dtype=float)
    for _ in range(n_iters):
        labels = _assign(X, c)
        c = np.array([X[labels == k].mean(axis=0) for k in range(len(c))])
    return c, labels


def manhattan(X, init_centroids, n_iters):
    c = np.array(init_centroids, dtype=float)
    for _ in range(n_iters):
        labels = np.abs(X[:, None, :] - c[None, :, :]).sum(-1).argmin(1)
        for k in range(len(c)):
            if (labels == k).any():
                c[k] = X[labels == k].mean(axis=0)
    return c, labels


def labels_after_update(X, init_centroids, n_iters):
    c = np.array(init_centroids, dtype=float)
    for _ in range(n_iters):
        labels = _assign(X, c)
        for k in range(len(c)):
            if (labels == k).any():
                c[k] = X[labels == k].mean(axis=0)
    return c, _assign(X, c)


def online_update(X, init_centroids, n_iters):
    c = np.array(init_centroids, dtype=float)
    for _ in range(n_iters):
        labels = _assign(X, c)
        for k in range(len(c)):
            if (labels == k).any():
                c[k] = X[labels == k].mean(axis=0)
                labels = _assign(X, c)  # reassigns mid-update
    return c, labels
