"""Buggy variants the tests must catch."""
import numpy as np


def _parts(logp_new, logp_old, logp_ref, adv, clip_eps, beta):
    a = adv[:, :, None]
    r = np.exp(logp_new - logp_old)
    surr = np.minimum(r * a, np.clip(r, 1 - clip_eps, 1 + clip_eps) * a)
    d = logp_ref - logp_new
    return -(surr - beta * (np.exp(d) - d - 1))


def biased_std(logp_new, logp_old, logp_ref, rewards, mask, clip_eps=0.2, beta=0.04, eps=1e-4):
    adv = (rewards - rewards.mean(1, keepdims=True)) / (rewards.std(1, keepdims=True) + eps)
    pt = _parts(logp_new, logp_old, logp_ref, adv, clip_eps, beta)
    return float(((pt * mask).sum(-1) / mask.sum(-1)).mean()), adv


def token_level_mean(logp_new, logp_old, logp_ref, rewards, mask, clip_eps=0.2, beta=0.04, eps=1e-4):
    adv = (rewards - rewards.mean(1, keepdims=True)) / (rewards.std(1, ddof=1, keepdims=True) + eps)
    pt = _parts(logp_new, logp_old, logp_ref, adv, clip_eps, beta)
    return float((pt * mask).sum() / mask.sum()), adv


def k1_kl(logp_new, logp_old, logp_ref, rewards, mask, clip_eps=0.2, beta=0.04, eps=1e-4):
    adv = (rewards - rewards.mean(1, keepdims=True)) / (rewards.std(1, ddof=1, keepdims=True) + eps)
    a = adv[:, :, None]
    r = np.exp(logp_new - logp_old)
    surr = np.minimum(r * a, np.clip(r, 1 - clip_eps, 1 + clip_eps) * a)
    pt = -(surr - beta * (logp_new - logp_ref))
    return float(((pt * mask).sum(-1) / mask.sum(-1)).mean()), adv


def global_normalization(logp_new, logp_old, logp_ref, rewards, mask, clip_eps=0.2, beta=0.04, eps=1e-4):
    adv = (rewards - rewards.mean()) / (rewards.std(ddof=1) + eps)  # across prompts, not within a group
    pt = _parts(logp_new, logp_old, logp_ref, adv, clip_eps, beta)
    return float(((pt * mask).sum(-1) / mask.sum(-1)).mean()), adv
