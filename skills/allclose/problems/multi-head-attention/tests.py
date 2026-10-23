import numpy as np


def cases():
    rng = np.random.default_rng(6)

    def args(b, t, d, h, causal=False):
        w = lambda: rng.normal(size=(d, d)) / np.sqrt(d)
        return dict(x=rng.normal(size=(b, t, d)), w_q=w(), w_k=w(), w_v=w(), w_o=w(), num_heads=h, causal=causal)

    return [
        dict(name="B=1 T=3 D=4 H=2", kwargs=args(1, 3, 4, 2), sample=True),
        dict(name="causal, B=1 T=4 D=4 H=2", kwargs=args(1, 4, 4, 2, True), sample=True),
        dict(name="single head", kwargs=args(2, 5, 6, 1)),
        dict(name="B=2 T=7 D=12 H=3", kwargs=args(2, 7, 12, 3)),
        dict(name="causal B=2 T=7 D=12 H=3", kwargs=args(2, 7, 12, 3, True)),
        dict(name="T=1 causal", kwargs=args(3, 1, 8, 4, True)),
        dict(name="head size 1 (H = D)", kwargs=args(1, 5, 4, 4, True)),
        dict(name="B=2 T=16 D=32 H=8 causal", kwargs=args(2, 16, 32, 8, True)),
    ]
