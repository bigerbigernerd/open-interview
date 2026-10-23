import numpy as np


def cases():
    rng = np.random.default_rng(20)

    def args(shape, d_out, r, alpha, merge=False, zero_b=False):
        d_in = shape[-1]
        return dict(x=rng.normal(size=shape), w=rng.normal(size=(d_in, d_out)), a=rng.normal(size=(d_in, r)),
                    b=np.zeros((r, d_out)) if zero_b else rng.normal(size=(r, d_out)), alpha=alpha, merge=merge)

    return [
        dict(name="r=2, alpha=4", kwargs=args((3, 4), 5, 2, 4.0), sample=True),
        dict(name="merge=True", kwargs=args((3, 4), 5, 2, 4.0, merge=True), sample=True),
        dict(name="B = 0 at init equals the base layer", kwargs=args((2, 6), 3, 4, 8.0, zero_b=True)),
        dict(name="r=8, alpha=16, batch x seq", kwargs=args((2, 5, 16), 12, 8, 16.0)),
        dict(name="r=1", kwargs=args((4, 8), 8, 1, 1.0)),
        dict(name="merge, r=4, alpha=32", kwargs=args((1, 10), 7, 4, 32.0, merge=True)),
    ]
