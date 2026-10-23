import numpy as np


def cases():
    rng = np.random.default_rng(7)
    return [
        dict(name="D=2, positions 0..2", kwargs=dict(x=np.ones((3, 2)), positions=np.arange(3)), sample=True),
        dict(name="D=4, T=3", kwargs=dict(x=rng.normal(size=(3, 4)), positions=np.arange(3)), sample=True),
        dict(name="position 0 is identity", kwargs=dict(x=rng.normal(size=(1, 8)), positions=np.array([0]))),
        dict(name="batch x heads x T x D", kwargs=dict(x=rng.normal(size=(2, 3, 5, 8)), positions=np.arange(5))),
        dict(name="non-contiguous positions", kwargs=dict(x=rng.normal(size=(3, 16)), positions=np.array([5, 17, 100]))),
        dict(name="base 500000 (Llama 3)", kwargs=dict(x=rng.normal(size=(4, 64)), positions=np.arange(1000, 1004), base=500000.0)),
        dict(name="D=128, long positions", kwargs=dict(x=rng.normal(size=(2, 6, 128)), positions=np.arange(4090, 4096))),
    ]
