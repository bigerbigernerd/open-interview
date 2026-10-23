import numpy as np


def cases():
    rng = np.random.default_rng(19)

    def args(shape, h, scale=1.0):
        d = shape[-1]
        return dict(x=rng.normal(size=shape) * scale, w_gate=rng.normal(size=(d, h)) / np.sqrt(d),
                    w_up=rng.normal(size=(d, h)) / np.sqrt(d), w_down=rng.normal(size=(h, d)) / np.sqrt(h))

    return [
        dict(name="2 x 4, H = 6", kwargs=args((2, 4), 6), sample=True),
        dict(name="batch x seq x D", kwargs=args((2, 3, 8), 16), sample=True),
        dict(name="square H = D", kwargs=args((5, 6), 6)),
        dict(name="large activations", kwargs=args((4, 8), 12, scale=30.0)),
        dict(name="1-D input", kwargs=args((10,), 24)),
    ]
