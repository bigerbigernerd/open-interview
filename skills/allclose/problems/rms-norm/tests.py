import numpy as np


def cases():
    rng = np.random.default_rng(9)

    def args(shape, scale=1.0, **kw):
        return dict(x=rng.normal(size=shape) * scale, weight=rng.normal(size=shape[-1]), **kw)

    return [
        dict(name="2 x 4", kwargs=args((2, 4)), sample=True),
        dict(name="1-D", kwargs=args((6,)), sample=True),
        dict(name="batch x seq x hidden", kwargs=args((2, 5, 16))),
        dict(name="mean far from zero", kwargs=dict(x=rng.normal(size=(3, 8)) + 5.0, weight=np.ones(8))),
        dict(name="tiny values (eps matters)", kwargs=args((4, 8), scale=1e-4)),
        dict(name="custom eps", kwargs=args((3, 4), scale=0.01, eps=1e-2)),
        dict(name="all zeros", kwargs=dict(x=np.zeros((2, 3)), weight=np.ones(3))),
    ]
