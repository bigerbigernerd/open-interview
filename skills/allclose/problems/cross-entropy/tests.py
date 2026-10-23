import numpy as np


def cases():
    rng = np.random.default_rng(2)
    big = rng.normal(size=(64, 50)) * 3
    return [
        dict(name="example", kwargs=dict(logits=np.array([[2.0, 1.0, 0.1]]), labels=np.array([0])), sample=True),
        dict(name="batch of 4, 5 classes", kwargs=dict(logits=rng.normal(size=(4, 5)), labels=np.array([0, 3, 4, 1])), sample=True),
        dict(name="label smoothing 0.1", kwargs=dict(logits=rng.normal(size=(3, 4)), labels=np.array([2, 0, 1]), label_smoothing=0.1), sample=True),
        dict(name="square logits", kwargs=dict(logits=rng.normal(size=(6, 6)), labels=np.array([5, 0, 2, 2, 1, 4]))),
        dict(name="binary", kwargs=dict(logits=rng.normal(size=(5, 2)), labels=np.array([0, 1, 1, 0, 1]))),
        dict(name="label far below the max (log 0)", kwargs=dict(logits=np.array([[0.0, 1000.0], [-500.0, 500.0]]), labels=np.array([0, 0]))),
        dict(name="huge logits", kwargs=dict(logits=np.array([[1e4, 1e4 + 1, 1e4 - 3]]), labels=np.array([1]))),
        dict(name="smoothing 0.2 with extreme logits", kwargs=dict(logits=np.array([[0.0, 800.0, -800.0]]), labels=np.array([1]), label_smoothing=0.2)),
        dict(name="64 x 50", kwargs=dict(logits=big, labels=rng.integers(0, 50, size=64), label_smoothing=0.05)),
    ]
