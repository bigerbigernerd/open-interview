import numpy as np


def roc_auc(y_true, y_score):
    y = np.asarray(y_true).astype(bool)
    s = np.asarray(y_score, dtype=float)
    order = np.argsort(s, kind="mergesort")
    _, first, counts = np.unique(s[order], return_index=True, return_counts=True)
    avg_rank = first + (counts + 1) / 2  # 1-based average rank of each tie group
    ranks = np.empty(len(s))
    ranks[order] = np.repeat(avg_rank, counts)
    p = y.sum()
    n = len(y) - p
    return float((ranks[y].sum() - p * (p + 1) / 2) / (p * n))
