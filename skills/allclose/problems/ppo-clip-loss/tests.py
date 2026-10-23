import numpy as np


def cases():
    rng = np.random.default_rng(25)

    def args(b, t, drift=0.3, masked=False, **kw):
        old = -np.abs(rng.normal(size=(b, t))) * 2
        new = old + rng.normal(size=(b, t)) * drift
        d = dict(logp_new=new, logp_old=old, advantages=rng.normal(size=(b, t)))
        if masked:
            m = np.ones((b, t))
            for i in range(b):
                m[i, rng.integers(1, t):] = 0
            d["mask"] = m
        d.update(kw)
        return d

    return [
        dict(name="2 x 3, no mask", kwargs=args(2, 3), sample=True),
        dict(name="with padding mask", kwargs=args(3, 6, masked=True), sample=True),
        dict(name="small updates (no clipping)", kwargs=args(4, 5, drift=0.01)),
        dict(name="large updates (heavy clipping)", kwargs=args(4, 8, drift=1.0)),
        dict(name="clip_eps 0.1 with mask", kwargs=args(5, 10, drift=0.4, masked=True, clip_eps=0.1)),
        dict(name="negative advantages only", kwargs=dict(args(3, 4, drift=0.8), advantages=-np.abs(rng.normal(size=(3, 4))))),
    ]
