import numpy as np


def cases():
    rng = np.random.default_rng(23)

    def args(n, d, h, e, k, router_scale=1.0):
        return dict(x=rng.normal(size=(n, d)), w_router=rng.normal(size=(d, e)) * router_scale,
                    w1=rng.normal(size=(e, d, h)) / np.sqrt(d), w2=rng.normal(size=(e, h, d)) / np.sqrt(h), top_k=k)

    return [
        dict(name="N=4, E=4, top-2", kwargs=args(4, 3, 5, 4, 2), sample=True),
        dict(name="top-1 (Switch)", kwargs=args(6, 4, 8, 4, 1), sample=True),
        dict(name="N=16, E=8, top-2", kwargs=args(16, 8, 16, 8, 2)),
        dict(name="top-k = E (dense)", kwargs=args(5, 4, 6, 3, 3)),
        dict(name="sharp router", kwargs=args(10, 6, 8, 6, 2, router_scale=5.0)),
        dict(name="N=64, E=16, top-4", kwargs=args(64, 16, 32, 16, 4)),
    ]
