import numpy as np


def cases():
    rng = np.random.default_rng(29)
    outliers = rng.normal(size=(4, 16)) * 0.02
    outliers[1, 3] = 5.0
    outliers[2, 7] = -8.0
    return [
        dict(name="2 x 3", kwargs=dict(w=np.array([[0.5, -1.0, 0.25], [2.0, 0.1, -0.7]])), sample=True),
        dict(name="row of zeros", kwargs=dict(w=np.array([[0.0, 0.0, 0.0], [1.0, -0.5, 0.2]])), sample=True),
        dict(name="per-row scales differ a lot", kwargs=dict(w=np.array([[0.001, -0.002, 0.0015], [100.0, -50.0, 25.0]]))),
        dict(name="outliers", kwargs=dict(w=outliers)),
        dict(name="ties round to even (np.round)", kwargs=dict(w=np.array([[127.0, 0.5, 1.5, 2.5, -2.5, -0.5, 3.5]]))),
        dict(name="64 x 128 weights", kwargs=dict(w=rng.normal(size=(64, 128)) * 0.05)),
    ]
