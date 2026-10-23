import numpy as np


def clip_loss(image_emb, text_emb, temperature=0.07):
    img = image_emb / np.linalg.norm(image_emb, axis=1, keepdims=True)
    txt = text_emb / np.linalg.norm(text_emb, axis=1, keepdims=True)
    logits = img @ txt.T / temperature

    def ce_diag(z):  # mean cross-entropy with targets on the diagonal
        z = z - z.max(axis=1, keepdims=True)
        logp = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
        return -np.diag(logp).mean()

    return float((ce_diag(logits) + ce_diag(logits.T)) / 2)
