"""Buggy variants the tests must catch."""
import numpy as np


def _softmax(x):
    e = np.exp(x - x.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def log_of_softmax(logits, labels, label_smoothing=0.0):
    logp = np.log(_softmax(logits))  # log(0) = -inf for very unlikely classes
    n = len(labels)
    loss = (1 - label_smoothing) * -logp[np.arange(n), labels] - label_smoothing * logp.mean(axis=1)
    return float(loss.mean())


def wrong_gather(logits, labels, label_smoothing=0.0):
    m = logits.max(axis=1, keepdims=True)
    logp = logits - m - np.log(np.exp(logits - m).sum(axis=1, keepdims=True))
    loss = (1 - label_smoothing) * -logp[:, labels] - label_smoothing * logp.mean(axis=1, keepdims=True)  # (N, N)
    return float(loss.mean())


def smoothing_over_others(logits, labels, label_smoothing=0.0):
    n, c = logits.shape
    m = logits.max(axis=1, keepdims=True)
    logp = logits - m - np.log(np.exp(logits - m).sum(axis=1, keepdims=True))
    q = np.full((n, c), label_smoothing / (c - 1))  # spreads eps over the other C-1 classes
    q[np.arange(n), labels] = 1 - label_smoothing
    return float(-(q * logp).sum(axis=1).mean())


def summed(logits, labels, label_smoothing=0.0):
    n, c = logits.shape
    m = logits.max(axis=1, keepdims=True)
    logp = logits - m - np.log(np.exp(logits - m).sum(axis=1, keepdims=True))
    loss = (1 - label_smoothing) * -logp[np.arange(n), labels] - label_smoothing * logp.mean(axis=1)
    return float(loss.sum())
