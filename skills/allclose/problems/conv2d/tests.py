import numpy as np


def cases():
    rng = np.random.default_rng(16)
    r = lambda *s: rng.normal(size=s)
    return [
        dict(name="1x1x3x3 input, 2x2 kernel", kwargs=dict(x=np.arange(9.0).reshape(1, 1, 3, 3), w=np.array([[[[1.0, 0.0], [0.0, -1.0]]]])), sample=True),
        dict(name="padding 1", kwargs=dict(x=r(1, 1, 4, 4), w=r(1, 1, 3, 3), padding=1), sample=True),
        dict(name="stride 2 + bias", kwargs=dict(x=r(2, 3, 7, 7), w=r(4, 3, 3, 3), b=r(4), stride=2)),
        dict(name="asymmetric kernel 1x3", kwargs=dict(x=r(1, 2, 5, 6), w=r(3, 2, 1, 3), b=r(3))),
        dict(name="stride 2, padding 2, kernel 5", kwargs=dict(x=r(2, 2, 9, 8), w=r(2, 2, 5, 5), stride=2, padding=2)),
        dict(name="kernel = input size", kwargs=dict(x=r(3, 4, 3, 3), w=r(5, 4, 3, 3), b=r(5))),
        dict(name="(4, 8, 32, 32) x 16 filters within 2 s", kwargs=dict(x=r(4, 8, 32, 32), w=r(16, 8, 3, 3), b=r(16), padding=1)),
    ]
