import numpy as np


def clip_loss(image_emb, text_emb, temperature=0.07):
    """Symmetric InfoNCE over L2-normalized embeddings; pair i <-> i. Returns a float."""
    raise NotImplementedError
