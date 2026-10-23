import numpy as np


def cases():
    rng = np.random.default_rng(13)

    def data(n, d, noise=1.0):
        X = rng.normal(size=(n, d))
        w = rng.normal(size=d)
        y = (X @ w + 0.5 + rng.normal(size=n) * noise > 0).astype(float)
        return X, y

    X1, y1 = data(20, 2)
    X2, y2 = data(100, 5)
    X3, y3 = data(60, 3, noise=0.0)
    return [
        dict(name="tiny, 1 epoch", kwargs=dict(X=np.array([[1.0, 2.0], [-1.0, 0.5], [0.3, -2.0]]), y=np.array([1.0, 0.0, 1.0]), epochs=1), sample=True),
        dict(name="20 x 2, 100 epochs", kwargs=dict(X=X1, y=y1), sample=True),
        dict(name="100 x 5, lr 0.5", kwargs=dict(X=X2, y=y2, lr=0.5, epochs=50)),
        dict(name="with L2", kwargs=dict(X=X2, y=y2, l2=0.1, epochs=80)),
        dict(name="separable, strong L2", kwargs=dict(X=X3, y=y3, l2=1.0, epochs=200)),
        dict(name="unbalanced labels", kwargs=dict(X=X1, y=np.r_[np.ones(17), np.zeros(3)], epochs=30)),
    ]
