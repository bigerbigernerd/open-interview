import numpy as np


def cases():
    rng = np.random.default_rng(4)
    n = 50000
    y_big = rng.integers(0, 2, size=n)
    s_big = rng.normal(size=n) + y_big * 0.8
    y_mid = rng.integers(0, 2, size=300)
    y_mid[:2] = [0, 1]
    return [
        dict(name="example", kwargs=dict(y_true=np.array([0, 0, 1, 1]), y_score=np.array([0.1, 0.4, 0.35, 0.8])), sample=True),
        dict(name="with ties", kwargs=dict(y_true=np.array([1, 0, 1, 0, 1]), y_score=np.array([0.5, 0.5, 0.9, 0.1, 0.5])), sample=True),
        dict(name="perfect ranking", kwargs=dict(y_true=np.array([0, 0, 0, 1, 1]), y_score=np.array([0.1, 0.2, 0.3, 0.8, 0.9]))),
        dict(name="reversed ranking", kwargs=dict(y_true=np.array([1, 1, 0, 0]), y_score=np.array([0.1, 0.2, 0.3, 0.4]))),
        dict(name="all scores equal", kwargs=dict(y_true=np.array([0, 1, 0, 1, 1]), y_score=np.full(5, 0.3))),
        dict(name="one positive", kwargs=dict(y_true=np.array([0, 0, 1, 0]), y_score=np.array([0.3, 0.9, 0.5, 0.1]))),
        dict(name="coarse scores, many ties", kwargs=dict(y_true=y_mid, y_score=np.round(rng.random(300), 1))),
        dict(name="unsorted random", kwargs=dict(y_true=y_mid, y_score=rng.random(300) + y_mid * 0.3)),
        dict(name="n = 50000 within 0.3 s", kwargs=dict(y_true=y_big, y_score=s_big), limit=0.3),
    ]
