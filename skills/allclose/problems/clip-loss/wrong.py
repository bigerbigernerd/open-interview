"""Buggy variants the tests must catch."""
import numpy as np


def _ce(z):
    z = z - z.max(1, keepdims=True)
    return -np.diag(z - np.log(np.exp(z).sum(1, keepdims=True))).mean()


def _norm(x):
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def no_normalization(image_emb, text_emb, temperature=0.07):
    logits = image_emb @ text_emb.T / temperature
    return float((_ce(logits) + _ce(logits.T)) / 2)


def one_direction(image_emb, text_emb, temperature=0.07):
    return float(_ce(_norm(image_emb) @ _norm(text_emb).T / temperature))


def times_temperature(image_emb, text_emb, temperature=0.07):
    logits = _norm(image_emb) @ _norm(text_emb).T * temperature
    return float((_ce(logits) + _ce(logits.T)) / 2)


def unstable_softmax(image_emb, text_emb, temperature=0.07):
    logits = _norm(image_emb) @ _norm(text_emb).T / temperature

    def ce(z):
        p = np.exp(z) / np.exp(z).sum(1, keepdims=True)
        return -np.log(np.diag(p)).mean()
    return float((ce(logits) + ce(logits.T)) / 2)
