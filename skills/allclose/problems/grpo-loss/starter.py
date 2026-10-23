import numpy as np


def grpo_loss(logp_new, logp_old, logp_ref, rewards, mask, clip_eps=0.2, beta=0.04, eps=1e-4):
    """GRPO loss (TRL conventions). Returns (loss: float, advantages (B, G))."""
    raise NotImplementedError
