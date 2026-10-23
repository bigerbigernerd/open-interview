"""Buggy variants the tests must catch."""
import numpy as np


def ties_count_zero(y_true, y_score):
    y = np.asarray(y_true).astype(bool)
    pos, neg = y_score[y], y_score[~y]
    return float((pos[:, None] > neg[None, :]).mean())


def pairwise_too_slow(y_true, y_score):
    """Correct value, O(P*N) time and memory."""
    y = np.asarray(y_true).astype(bool)
    pos, neg = y_score[y], y_score[~y]
    return float(((pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :])).mean())


def ordinal_ranks(y_true, y_score):
    y = np.asarray(y_true).astype(bool)
    ranks = np.argsort(np.argsort(y_score, kind="mergesort"), kind="mergesort") + 1.0  # ties broken arbitrarily
    p = y.sum()
    n = len(y) - p
    return float((ranks[y].sum() - p * (p + 1) / 2) / (p * n))


def accuracy_at_half(y_true, y_score):
    return float(((y_score > 0.5) == np.asarray(y_true).astype(bool)).mean())
