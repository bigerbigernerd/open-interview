import numpy as np


def cross_entropy(logits, labels, label_smoothing=0.0):
    n, c = logits.shape
    m = logits.max(axis=1, keepdims=True)
    logp = logits - m - np.log(np.exp(logits - m).sum(axis=1, keepdims=True))  # log_softmax
    nll = -logp[np.arange(n), labels]
    smooth = -logp.mean(axis=1)  # cross-entropy against the uniform distribution
    loss = (1 - label_smoothing) * nll + label_smoothing * smooth
    return float(loss.mean())
