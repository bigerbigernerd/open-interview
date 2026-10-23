"""Buggy variants the tests must catch."""
import numpy as np


def per_tensor(w):
    s = np.abs(w).max() / 127
    return np.clip(np.round(w / s), -127, 127).astype(np.int8), np.full(w.shape[0], s)


def divides_by_128(w):
    amax = np.abs(w).max(axis=1)
    s = np.where(amax > 0, amax / 128, 1.0)
    return np.clip(np.round(w / s[:, None]), -127, 127).astype(np.int8), s


def truncates(w):
    amax = np.abs(w).max(axis=1)
    s = np.where(amax > 0, amax / 127, 1.0)
    return np.clip(w / s[:, None], -127, 127).astype(np.int8), s


def half_away_from_zero(w):
    amax = np.abs(w).max(axis=1)
    s = np.where(amax > 0, amax / 127, 1.0)
    x = w / s[:, None]
    return np.clip(np.sign(x) * np.floor(np.abs(x) + 0.5), -127, 127).astype(np.int8), s
