import numpy as np


def cases():
    rng = np.random.default_rng(14)
    blobs = np.concatenate([rng.normal(size=(30, 2)) + m for m in ([0, 0], [6, 6], [0, 8])])
    big = np.concatenate([rng.normal(size=(5000, 4)) + m for m in rng.normal(size=(4, 4)) * 6])
    return [
        dict(name="4 points, 2 clusters, 1 iter", kwargs=dict(X=np.array([[0.0, 0.0], [0.0, 1.0], [5.0, 5.0], [6.0, 5.0]]), init_centroids=np.array([[0.0, 0.0], [1.0, 1.0]]), n_iters=1), sample=True),
        dict(name="3 blobs, 10 iters", kwargs=dict(X=blobs, init_centroids=blobs[[0, 1, 2]], n_iters=10), sample=True),
        dict(name="3 blobs, 1 iter", kwargs=dict(X=blobs, init_centroids=blobs[[0, 35, 70]], n_iters=1)),
        dict(name="empty cluster keeps its center", kwargs=dict(X=blobs, init_centroids=np.array([[0.0, 0.0], [6.0, 6.0], [100.0, 100.0]]), n_iters=3)),
        dict(name="duplicate initial centers (tie -> lower index)", kwargs=dict(X=blobs, init_centroids=np.array([[1.0, 1.0], [1.0, 1.0], [6.0, 6.0]]), n_iters=2)),
        dict(name="N = 20000, D = 4, K = 4", kwargs=dict(X=big, init_centroids=big[[0, 5000, 10000, 15000]] + 0.5, n_iters=8), limit=3),
    ]
