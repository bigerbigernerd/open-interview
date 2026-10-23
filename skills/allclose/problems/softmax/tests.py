import numpy as np


def cases():
    rng = np.random.default_rng(1)
    return [
        dict(name="1-D example", kwargs=dict(x=np.array([1.0, 2.0, 3.0])), sample=True),
        dict(name="2-D, last axis", kwargs=dict(x=rng.normal(size=(4, 5))), sample=True),
        dict(name="axis=0", kwargs=dict(x=rng.normal(size=(3, 6)), axis=0), sample=True),
        dict(name="3-D, axis=1", kwargs=dict(x=rng.normal(size=(2, 7, 3)), axis=1)),
        dict(name="square matrix", kwargs=dict(x=rng.normal(size=(5, 5)))),
        dict(name="large logits (overflow)", kwargs=dict(x=np.array([[1000.0, 1001.0, 1002.0], [-5.0, 0.0, 5.0]]))),
        dict(name="very negative logits", kwargs=dict(x=np.array([-1000.0, -1001.0, -1002.0]))),
        dict(name="constant rows", kwargs=dict(x=np.full((2, 4), 3.0))),
        dict(name="single element", kwargs=dict(x=np.array([[42.0]]))),
        dict(name="wide, large scale", kwargs=dict(x=rng.normal(scale=50, size=(8, 300)))),
    ]
