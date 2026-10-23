import numpy as np


def dpo_loss(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1):
    chosen = beta * (policy_chosen_logps - ref_chosen_logps)
    rejected = beta * (policy_rejected_logps - ref_rejected_logps)
    loss = np.logaddexp(0.0, -(chosen - rejected)).mean()  # -log sigmoid, stable
    return float(loss), chosen, rejected
