import numpy as np


def cases():
    rng = np.random.default_rng(18)

    def args(b, d, h, t):
        w = lambda: rng.normal(size=(d, d)) / np.sqrt(d)
        dh = d // h
        return dict(x=rng.normal(size=(b, 1, d)), w_q=w(), w_k=w(), w_v=w(), w_o=w(), num_heads=h,
                    k_cache=rng.normal(size=(b, h, t, dh)), v_cache=rng.normal(size=(b, h, t, dh)))

    return [
        dict(name="first token (empty cache)", kwargs=args(1, 4, 2, 0), sample=True),
        dict(name="T=3, D=4, H=2", kwargs=args(1, 4, 2, 3), sample=True),
        dict(name="batch 2, T=5, D=8, H=4", kwargs=args(2, 8, 4, 5)),
        dict(name="single head", kwargs=args(2, 6, 1, 4)),
        dict(name="T=1, D=12, H=3", kwargs=args(3, 12, 3, 1)),
        dict(name="long cache T=64, D=32, H=8", kwargs=args(2, 32, 8, 64)),
    ]
