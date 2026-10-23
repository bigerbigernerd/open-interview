"""Buggy variants the tests must catch."""
import numpy as np


def naive_log_sigmoid(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1):
    c = beta * (policy_chosen_logps - ref_chosen_logps)
    r = beta * (policy_rejected_logps - ref_rejected_logps)
    return float(-np.log(1 / (1 + np.exp(-(c - r)))).mean()), c, r


def beta_on_the_loss(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1):
    c = policy_chosen_logps - ref_chosen_logps
    r = policy_rejected_logps - ref_rejected_logps
    return float(beta * np.logaddexp(0, -(c - r)).mean()), beta * c, beta * r


def reference_sign_flipped(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1):
    c = beta * (policy_chosen_logps + ref_chosen_logps)
    r = beta * (policy_rejected_logps + ref_rejected_logps)
    return float(np.logaddexp(0, -(c - r)).mean()), c, r


def summed(policy_chosen_logps, policy_rejected_logps, ref_chosen_logps, ref_rejected_logps, beta=0.1):
    c = beta * (policy_chosen_logps - ref_chosen_logps)
    r = beta * (policy_rejected_logps - ref_rejected_logps)
    return float(np.logaddexp(0, -(c - r)).sum()), c, r
