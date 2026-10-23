import numpy as np


def cases():
    rng = np.random.default_rng(5)
    r = lambda *s: rng.normal(size=s)
    causal = np.tril(np.ones((6, 6), dtype=bool))
    pad = np.ones((2, 1, 1, 7), dtype=bool)
    pad[0, ..., 5:] = False
    pad[1, ..., 3:] = False
    return [
        dict(name="example: identity", kwargs=dict(q=np.eye(2), k=np.eye(2), v=np.eye(2)), sample=True),
        dict(name="single head 3x4", kwargs=dict(q=r(3, 4), k=r(3, 4), v=r(3, 4)), sample=True),
        dict(name="causal mask", kwargs=dict(q=r(6, 8), k=r(6, 8), v=r(6, 8), mask=causal), sample=True),
        dict(name="batch x heads", kwargs=dict(q=r(2, 3, 5, 8), k=r(2, 3, 5, 8), v=r(2, 3, 5, 8))),
        dict(name="cross-attention Tq != Tk, dv != d", kwargs=dict(q=r(2, 4, 16), k=r(2, 9, 16), v=r(2, 9, 5))),
        dict(name="padding mask (B,1,1,Tk)", kwargs=dict(q=r(2, 2, 7, 4), k=r(2, 2, 7, 4), v=r(2, 2, 7, 4), mask=pad)),
        dict(name="large scores (stability)", kwargs=dict(q=r(4, 8) * 40, k=r(4, 8) * 40, v=r(4, 8))),
        dict(name="large scores + causal", kwargs=dict(q=r(6, 8) * 40, k=r(6, 8) * 40, v=r(6, 8), mask=causal)),
        dict(name="one key", kwargs=dict(q=r(3, 4), k=r(1, 4), v=r(1, 2))),
    ]
