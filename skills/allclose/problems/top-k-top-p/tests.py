import numpy as np


def cases():
    rng = np.random.default_rng(8)
    return [
        dict(name="example top_p=0.8", kwargs=dict(logits=np.array([2.0, 1.0, 0.5, -1.0]), top_p=0.8), sample=True),
        dict(name="top_k=2", kwargs=dict(logits=np.array([0.3, 2.0, -1.0, 1.5, 0.0])), sample=True),
        dict(name="temperature 0.5", kwargs=dict(logits=rng.normal(size=6), temperature=0.5), sample=True),
        dict(name="top_k=2 explicit", kwargs=dict(logits=np.array([0.3, 2.0, -1.0, 1.5, 0.0]), top_k=2)),
        dict(name="temperature 2 + top_k 3", kwargs=dict(logits=rng.normal(size=10) * 3, temperature=2.0, top_k=3)),
        dict(name="top_p tiny keeps only the argmax", kwargs=dict(logits=rng.normal(size=12), top_p=0.01)),
        dict(name="top_k >= vocab is a no-op", kwargs=dict(logits=rng.normal(size=5), top_k=9)),
        dict(name="batch, top_k=5 then top_p=0.8", kwargs=dict(logits=rng.normal(size=(4, 20)) * 2, top_k=5, top_p=0.8)),
        dict(name="batch, temperature 0.7, top_p 0.9", kwargs=dict(logits=rng.normal(size=(3, 50)) * 2, temperature=0.7, top_p=0.9)),
        dict(name="flat distribution, top_p 0.5", kwargs=dict(logits=rng.normal(size=(2, 30)) * 0.1, top_p=0.5)),
    ]
