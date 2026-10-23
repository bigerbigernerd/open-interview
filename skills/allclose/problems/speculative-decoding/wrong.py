"""Buggy variants the tests must catch."""
import numpy as np


def deterministic_accept(draft_tokens, draft_probs, target_probs, u):
    acc = []
    for i, x in enumerate(draft_tokens):
        p, q = target_probs[i], draft_probs[i]
        if p[x] >= q[x]:  # ignores u
            acc.append(int(x))
            continue
        r = np.maximum(p - q, 0)
        return acc, r / r.sum()
    return acc, target_probs[len(draft_tokens)]


def residual_not_clipped(draft_tokens, draft_probs, target_probs, u):
    acc = []
    for i, x in enumerate(draft_tokens):
        p, q = target_probs[i], draft_probs[i]
        if u[i] < min(1.0, p[x] / q[x]):
            acc.append(int(x))
            continue
        r = p - q
        return acc, r / np.abs(r).sum()
    return acc, target_probs[len(draft_tokens)]


def resample_from_target(draft_tokens, draft_probs, target_probs, u):
    acc = []
    for i, x in enumerate(draft_tokens):
        p, q = target_probs[i], draft_probs[i]
        if u[i] < min(1.0, p[x] / q[x]):
            acc.append(int(x))
            continue
        return acc, p  # should be the residual
    return acc, target_probs[len(draft_tokens)]


def bonus_from_last_draft_position(draft_tokens, draft_probs, target_probs, u):
    acc = []
    for i, x in enumerate(draft_tokens):
        p, q = target_probs[i], draft_probs[i]
        if u[i] < min(1.0, p[x] / q[x]):
            acc.append(int(x))
            continue
        r = np.maximum(p - q, 0)
        return acc, r / r.sum()
    return acc, target_probs[len(draft_tokens) - 1]
