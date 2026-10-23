import numpy as np


def cases():
    rng = np.random.default_rng(10)

    def args(shape, **kw):
        c = shape[1]
        return dict(x=rng.normal(size=shape) * 2 + 1, gamma=rng.normal(size=c), beta=rng.normal(size=c),
                    running_mean=rng.normal(size=c) * 0.1, running_var=rng.random(c) + 0.5, **kw)

    return [
        dict(name="(N, C) = (4, 3)", kwargs=args((4, 3)), sample=True),
        dict(name="(N, C, H, W) = (2, 3, 4, 4)", kwargs=args((2, 3, 4, 4)), sample=True),
        dict(name="momentum 0.5", kwargs=args((8, 5), momentum=0.5)),
        dict(name="N = 2", kwargs=args((2, 4))),
        dict(name="square (N = C = 6)", kwargs=args((6, 6))),
        dict(name="4-D, N = 1", kwargs=args((1, 2, 3, 5))),
        dict(name="large batch", kwargs=args((64, 8, 2, 2), momentum=0.01, eps=1e-3)),
    ]
