import numpy as np


def cases():
    rng = np.random.default_rng(12)

    def args(n, d, h, c, scale=1.0):
        return dict(x=rng.normal(size=(n, d)), y=rng.integers(0, c, size=n), w1=rng.normal(size=(d, h)) * scale,
                    b1=rng.normal(size=h) * 0.1, w2=rng.normal(size=(h, c)) * scale, b2=rng.normal(size=c) * 0.1)

    return [
        dict(name="N=2 D=3 H=4 C=2", kwargs=args(2, 3, 4, 2), sample=True),
        dict(name="N=5 D=4 H=6 C=3", kwargs=args(5, 4, 6, 3), sample=True),
        dict(name="square shapes", kwargs=args(4, 4, 4, 4)),
        dict(name="N=1", kwargs=args(1, 3, 5, 4)),
        dict(name="large weights (stable loss)", kwargs=args(6, 5, 8, 3, scale=20.0)),
        dict(name="N=32 D=10 H=16 C=5", kwargs=args(32, 10, 16, 5)),
    ]
