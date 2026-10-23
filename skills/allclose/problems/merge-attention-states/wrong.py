"""Buggy variants the tests must catch."""
import numpy as np


def naive_exp(o1, lse1, o2, lse2):
    e1, e2 = np.exp(lse1), np.exp(lse2)  # overflows
    tot = e1 + e2
    return (e1 / tot)[..., None] * o1 + (e2 / tot)[..., None] * o2, np.log(tot)


def plain_average(o1, lse1, o2, lse2):
    return (o1 + o2) / 2, np.logaddexp(lse1, lse2)


def lse_is_max(o1, lse1, o2, lse2):
    lse = np.logaddexp(lse1, lse2)
    o = np.exp(lse1 - lse)[..., None] * o1 + np.exp(lse2 - lse)[..., None] * o2
    return o, np.maximum(lse1, lse2)


def weights_not_normalized(o1, lse1, o2, lse2):
    m = np.maximum(lse1, lse2)
    return np.exp(lse1 - m)[..., None] * o1 + np.exp(lse2 - m)[..., None] * o2, np.logaddexp(lse1, lse2)
