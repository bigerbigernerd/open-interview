import numpy as np


def kmeans(X, init_centroids, n_iters):
    c = np.array(init_centroids, dtype=float)
    labels = np.zeros(len(X), dtype=int)
    for _ in range(n_iters):
        d = ((X[:, None, :] - c[None, :, :]) ** 2).sum(-1)  # (N, K) squared distances
        labels = d.argmin(axis=1)  # ties -> lower index
        for k in range(len(c)):
            mask = labels == k
            if mask.any():
                c[k] = X[mask].mean(axis=0)
    return c, labels
