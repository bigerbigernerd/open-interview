import numpy as np


def cases():
    rng = np.random.default_rng(26)

    def args(b, g, t, ragged=True, binary=False, **kw):
        old = -np.abs(rng.normal(size=(b, g, t)))
        new = old + rng.normal(size=(b, g, t)) * 0.3
        ref = old + rng.normal(size=(b, g, t)) * 0.2
        rewards = rng.integers(0, 2, size=(b, g)).astype(float) if binary else rng.normal(size=(b, g))
        mask = np.ones((b, g, t))
        if ragged:
            for i in range(b):
                for j in range(g):
                    mask[i, j, rng.integers(1, t + 1):] = 0
        return dict(logp_new=new, logp_old=old, logp_ref=ref, rewards=rewards, mask=mask, **kw)

    same = args(1, 4, 5)
    same["rewards"] = np.ones((1, 4))
    return [
        dict(name="1 prompt x 4 answers, full mask", kwargs=args(1, 4, 3, ragged=False), sample=True),
        dict(name="2 x 4, ragged lengths", kwargs=args(2, 4, 6), sample=True),
        dict(name="binary rewards, G=8", kwargs=args(3, 8, 10, binary=True)),
        dict(name="all rewards equal (A = 0)", kwargs=same),
        dict(name="beta = 0, clip 0.1", kwargs=args(2, 6, 7, beta=0.0, clip_eps=0.1)),
        dict(name="very different lengths", kwargs=args(4, 4, 30)),
    ]
