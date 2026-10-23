import numpy as np


def ppo_clip_loss(logp_new, logp_old, advantages, mask=None, clip_eps=0.2):
    """Token-level PPO clipped surrogate. Returns (loss: float, clip_frac: float)."""
    raise NotImplementedError
