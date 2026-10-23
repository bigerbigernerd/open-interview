import numpy as np


def dpo_loss(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1):
    """Returns (loss: float, chosen_rewards (N,), rejected_rewards (N,))."""
    raise NotImplementedError
