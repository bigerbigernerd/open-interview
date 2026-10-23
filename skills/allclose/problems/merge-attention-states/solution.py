import numpy as np


def merge_attention_states(o1, lse1, o2, lse2):
    lse = np.logaddexp(lse1, lse2)
    w1 = np.exp(lse1 - lse)[..., None]  # share of the total softmax mass from block 1
    w2 = np.exp(lse2 - lse)[..., None]
    return w1 * o1 + w2 * o2, lse
