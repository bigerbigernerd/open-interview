import numpy as np


def conv2d(x, w, b=None, stride=1, padding=0):
    n, c, h, wd = x.shape
    f, _, kh, kw = w.shape
    xp = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))
    ho = (h + 2 * padding - kh) // stride + 1
    wo = (wd + 2 * padding - kw) // stride + 1
    out = np.zeros((n, f, ho, wo))
    for i in range(kh):
        for j in range(kw):
            patch = xp[:, :, i:i + stride * ho:stride, j:j + stride * wo:stride]  # (N, C, Ho, Wo)
            out += np.einsum("nchw,fc->nfhw", patch, w[:, :, i, j])
    if b is not None:
        out += b[None, :, None, None]
    return out
