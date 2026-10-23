import numpy as np


def grpo_loss(logp_new, logp_old, logp_ref, rewards, mask, clip_eps=0.2, beta=0.04, eps=1e-4):
    adv = (rewards - rewards.mean(axis=1, keepdims=True)) / (rewards.std(axis=1, ddof=1, keepdims=True) + eps)
    a = adv[:, :, None]
    ratio = np.exp(logp_new - logp_old)
    surr = np.minimum(ratio * a, np.clip(ratio, 1 - clip_eps, 1 + clip_eps) * a)
    d = logp_ref - logp_new
    kl = np.exp(d) - d - 1
    per_token = -(surr - beta * kl)
    m = mask.astype(float)
    per_answer = (per_token * m).sum(axis=-1) / m.sum(axis=-1)
    return float(per_answer.mean()), adv
