import numpy as np


def _dist(rng, k, v, sharp=1.0):
    z = rng.normal(size=(k, v)) * sharp
    e = np.exp(z - z.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


def _case(rng, k, v, u=None, close=False):
    q = _dist(rng, k, v, 2.0)
    p = _dist(rng, k + 1, v, 2.0)
    if close:
        p[:k] = 0.8 * q + 0.2 * p[:k]
    toks = np.array([rng.choice(v, p=q[i]) for i in range(k)])
    return dict(draft_tokens=toks, draft_probs=q, target_probs=p, u=rng.random(k) if u is None else u)


def cases():
    rng = np.random.default_rng(30)
    same = _case(rng, 3, 5)
    same["target_probs"][:3] = same["draft_probs"]
    first = _case(rng, 4, 6, u=np.array([0.999, 0.1, 0.1, 0.1]))
    x0 = first["draft_tokens"][0]
    first["target_probs"][0, x0] *= 0.05
    first["target_probs"][0] /= first["target_probs"][0].sum()
    return [
        dict(name="K=3, V=5", kwargs=_case(rng, 3, 5, close=True), sample=True),
        dict(name="target == draft: accept all, use p_K", kwargs=same, sample=True),
        dict(name="reject at the first token", kwargs=first),
        dict(name="u = 0 accepts everything", kwargs=_case(rng, 5, 8, u=np.zeros(5))),
        dict(name="K=8, V=50, close models", kwargs=_case(rng, 8, 50, close=True)),
        dict(name="K=6, V=20, unrelated models", kwargs=_case(rng, 6, 20)),
        dict(name="K=1", kwargs=_case(rng, 1, 4, close=True)),
    ]
