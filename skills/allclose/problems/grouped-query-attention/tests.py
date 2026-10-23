import numpy as np


def cases():
    rng = np.random.default_rng(17)

    def args(b, hq, hkv, t, d, causal=False):
        return dict(q=rng.normal(size=(b, hq, t, d)), k=rng.normal(size=(b, hkv, t, d)), v=rng.normal(size=(b, hkv, t, d)), causal=causal)

    return [
        dict(name="Hq=4, Hkv=2", kwargs=args(1, 4, 2, 3, 4), sample=True),
        dict(name="causal, Hq=4, Hkv=2", kwargs=args(1, 4, 2, 4, 4, True), sample=True),
        dict(name="MQA (Hkv=1)", kwargs=args(2, 4, 1, 5, 8)),
        dict(name="MHA (Hkv=Hq)", kwargs=args(2, 3, 3, 5, 8, True)),
        dict(name="Hq=8, Hkv=2, causal", kwargs=args(2, 8, 2, 7, 16, True)),
        dict(name="Hq=6, Hkv=3", kwargs=args(1, 6, 3, 6, 8)),
    ]
