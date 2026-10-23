"""Buggy variants the tests must catch."""
import numpy as np


def _core(xp, w, ho, wo, stride, flip=False):
    f, c, kh, kw = w.shape
    if flip:
        w = w[:, :, ::-1, ::-1]
    out = np.zeros((xp.shape[0], f, ho, wo))
    for i in range(kh):
        for j in range(kw):
            out += np.einsum("nchw,fc->nfhw", xp[:, :, i:i + stride * ho:stride, j:j + stride * wo:stride], w[:, :, i, j])
    return out


def flipped_kernel(x, w, b=None, stride=1, padding=0):
    p = padding
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)))
    ho = (x.shape[2] + 2 * p - w.shape[2]) // stride + 1
    wo = (x.shape[3] + 2 * p - w.shape[3]) // stride + 1
    out = _core(xp, w, ho, wo, stride, flip=True)
    return out + (b[None, :, None, None] if b is not None else 0)


def pad_one_side(x, w, b=None, stride=1, padding=0):
    p = padding
    xp = np.pad(x, ((0, 0), (0, 0), (2 * p, 0), (2 * p, 0)))
    ho = (x.shape[2] + 2 * p - w.shape[2]) // stride + 1
    wo = (x.shape[3] + 2 * p - w.shape[3]) // stride + 1
    out = _core(xp, w, ho, wo, stride)
    return out + (b[None, :, None, None] if b is not None else 0)


def ignores_bias(x, w, b=None, stride=1, padding=0):
    p = padding
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)))
    ho = (x.shape[2] + 2 * p - w.shape[2]) // stride + 1
    wo = (x.shape[3] + 2 * p - w.shape[3]) // stride + 1
    return _core(xp, w, ho, wo, stride)


def seven_loops(x, w, b=None, stride=1, padding=0):
    """Correct but far too slow."""
    p = padding
    xp = np.pad(x, ((0, 0), (0, 0), (p, p), (p, p)))
    n, c, _, _ = x.shape
    f, _, kh, kw = w.shape
    ho = (x.shape[2] + 2 * p - kh) // stride + 1
    wo = (x.shape[3] + 2 * p - kw) // stride + 1
    out = np.zeros((n, f, ho, wo))
    for a in range(n):
        for o in range(f):
            for i in range(ho):
                for j in range(wo):
                    s = 0.0
                    for ch in range(c):
                        for u in range(kh):
                            for v in range(kw):
                                s += xp[a, ch, i * stride + u, j * stride + v] * w[o, ch, u, v]
                    out[a, o, i, j] = s + (b[o] if b is not None else 0.0)
    return out
