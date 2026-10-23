import numpy as np


def cases():
    rng = np.random.default_rng(3)

    def args(shape, offset=0.0, scale=1.0):
        d = shape[-1]
        return dict(x=rng.normal(size=shape) * scale + offset, gamma=rng.normal(size=d), beta=rng.normal(size=d))

    tiny = args((2, 6), scale=1e-3)
    return [
        dict(name="2 x 4", kwargs=args((2, 4)), sample=True),
        dict(name="1-D", kwargs=args((5,)), sample=True),
        dict(name="batch x seq x hidden", kwargs=args((2, 3, 8))),
        dict(name="square", kwargs=args((6, 6))),
        dict(name="tiny variance (eps matters)", kwargs=tiny),
        dict(name="constant rows", kwargs=dict(x=np.full((2, 5), 7.0), gamma=np.ones(5), beta=np.arange(5.0))),
        dict(name="huge mean 1e7 (cancellation)", kwargs=args((3, 16), offset=1e7)),
        dict(name="custom eps", kwargs=dict(args((4, 4), scale=0.01), eps=1e-3)),
    ]
