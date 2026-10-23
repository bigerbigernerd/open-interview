import numpy as np


def _block(q, k, v, visible):
    """Attention of q over one key block plus its logsumexp; rows that see nothing get o = 0, lse = -inf."""
    s = q @ np.swapaxes(k, -1, -2) / np.sqrt(q.shape[-1])
    s = np.where(visible, s, -np.inf)
    m = s.max(axis=-1, keepdims=True)
    safe = np.where(np.isfinite(m), m, 0.0)
    e = np.exp(s - safe)
    z = e.sum(axis=-1, keepdims=True)
    o = np.where(z > 0, (e @ v) / np.where(z > 0, z, 1), 0.0)
    lse = np.where(z[..., 0] > 0, np.log(np.where(z[..., 0] > 0, z[..., 0], 1)) + safe[..., 0], -np.inf)
    return o, lse


def _split(rng, shape_q, tk, cut, scale=1.0, causal=False):
    *lead, t, d = shape_q
    q = rng.normal(size=shape_q) * scale
    k = rng.normal(size=(*lead, tk, d)) * scale
    v = rng.normal(size=(*lead, tk, d))
    vis = np.tril(np.ones((t, tk), dtype=bool), k=tk - t) if causal else np.ones((t, tk), dtype=bool)
    o1, l1 = _block(q, k[..., :cut, :], v[..., :cut, :], vis[:, :cut])
    o2, l2 = _block(q, k[..., cut:, :], v[..., cut:, :], vis[:, cut:])
    return dict(o1=o1, lse1=l1, o2=o2, lse2=l2)


def cases():
    rng = np.random.default_rng(27)
    return [
        dict(name="T=2, D=3, keys split 2 + 2", kwargs=_split(rng, (2, 3), 4, 2), sample=True),
        dict(name="batch x heads, split 5 + 3", kwargs=_split(rng, (2, 3, 4, 8), 8, 5), sample=True),
        dict(name="uneven split 1 + 9", kwargs=_split(rng, (6, 4), 10, 1)),
        dict(name="causal: some rows see only block 1", kwargs=_split(rng, (6, 4), 6, 3, causal=True)),
        dict(name="huge scores (overflow)", kwargs=_split(rng, (3, 16), 12, 6, scale=25.0)),
        dict(name="huge scores, causal", kwargs=_split(rng, (2, 8, 16), 8, 4, scale=25.0, causal=True)),
    ]
