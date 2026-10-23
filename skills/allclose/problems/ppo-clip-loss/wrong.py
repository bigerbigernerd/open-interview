"""Buggy variants the tests must catch."""
import numpy as np


def _prep(logp_new, logp_old, mask):
    m = np.ones_like(logp_new) if mask is None else mask.astype(float)
    return m, np.exp(logp_new - logp_old)


def max_instead_of_min(logp_new, logp_old, advantages, mask=None, clip_eps=0.2):
    m, r = _prep(logp_new, logp_old, mask)
    obj = np.maximum(r * advantages, np.clip(r, 1 - clip_eps, 1 + clip_eps) * advantages)
    return float(-(obj * m).sum() / m.sum()), float(((np.abs(r - 1) > clip_eps) * m).sum() / m.sum())


def clipped_term_only(logp_new, logp_old, advantages, mask=None, clip_eps=0.2):
    m, r = _prep(logp_new, logp_old, mask)
    obj = np.clip(r, 1 - clip_eps, 1 + clip_eps) * advantages
    return float(-(obj * m).sum() / m.sum()), float(((np.abs(r - 1) > clip_eps) * m).sum() / m.sum())


def ignores_mask(logp_new, logp_old, advantages, mask=None, clip_eps=0.2):
    _, r = _prep(logp_new, logp_old, mask)
    obj = np.minimum(r * advantages, np.clip(r, 1 - clip_eps, 1 + clip_eps) * advantages)
    return float(-obj.mean()), float((np.abs(r - 1) > clip_eps).mean())


def ratio_of_logs(logp_new, logp_old, advantages, mask=None, clip_eps=0.2):
    m = np.ones_like(logp_new) if mask is None else mask.astype(float)
    r = logp_new / logp_old
    obj = np.minimum(r * advantages, np.clip(r, 1 - clip_eps, 1 + clip_eps) * advantages)
    return float(-(obj * m).sum() / m.sum()), float(((np.abs(r - 1) > clip_eps) * m).sum() / m.sum())
