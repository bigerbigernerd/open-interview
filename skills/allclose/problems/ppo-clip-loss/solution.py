import numpy as np


def ppo_clip_loss(logp_new, logp_old, advantages, mask=None, clip_eps=0.2):
    if mask is None:
        mask = np.ones_like(logp_new)
    mask = mask.astype(float)
    ratio = np.exp(logp_new - logp_old)
    obj = np.minimum(ratio * advantages, np.clip(ratio, 1 - clip_eps, 1 + clip_eps) * advantages)
    loss = -(obj * mask).sum() / mask.sum()
    clip_frac = ((np.abs(ratio - 1) > clip_eps) * mask).sum() / mask.sum()
    return float(loss), float(clip_frac)
