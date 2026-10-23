import numpy as np


def cases():
    rng = np.random.default_rng(11)

    def args(shape, t, **kw):
        return dict(param=rng.normal(size=shape), grad=rng.normal(size=shape), m=rng.normal(size=shape) * 0.1,
                    v=rng.random(shape) * 0.01, t=t, **kw)

    first = dict(param=np.array([1.0, -2.0, 3.0]), grad=np.array([0.1, 0.2, -0.3]), m=np.zeros(3), v=np.zeros(3), t=1)
    return [
        dict(name="first step from zero state", kwargs=first, sample=True),
        dict(name="t = 10", kwargs=args((4,), 10), sample=True),
        dict(name="matrix, t = 3", kwargs=args((3, 5), 3)),
        dict(name="no weight decay", kwargs=args((6,), 2, weight_decay=0.0)),
        dict(name="large lr and decay", kwargs=args((5,), 4, lr=0.1, weight_decay=0.1)),
        dict(name="late step t = 5000", kwargs=args((4, 4), 5000, beta2=0.95)),
        dict(name="tiny gradients (eps matters)", kwargs=dict(param=np.zeros(3), grad=np.full(3, 1e-9), m=np.zeros(3), v=np.zeros(3), t=1, lr=1.0, eps=1e-6)),
    ]
