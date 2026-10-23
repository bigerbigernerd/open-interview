import numpy as np


def cases():
    rng = np.random.default_rng(28)

    def args(n, d, scale=1.0, temperature=0.07, related=0.0):
        img = rng.normal(size=(n, d)) * scale
        txt = rng.normal(size=(n, d)) * scale + related * img
        return dict(image_emb=img, text_emb=txt, temperature=temperature)

    return [
        dict(name="N=3, D=4", kwargs=args(3, 4), sample=True),
        dict(name="aligned pairs, N=4", kwargs=args(4, 8, related=3.0), sample=True),
        dict(name="unnormalized scales", kwargs=args(6, 5, scale=50.0, related=1.0)),
        dict(name="asymmetric (rows vs columns differ)", kwargs=dict(image_emb=rng.normal(size=(5, 6)), text_emb=np.repeat(rng.normal(size=(1, 6)), 5, 0) + rng.normal(size=(5, 6)) * 0.3)),
        dict(name="temperature 1.0", kwargs=args(8, 16, temperature=1.0)),
        dict(name="temperature 0.001 (stability)", kwargs=args(6, 8, temperature=0.001, related=0.5)),
        dict(name="N=64, D=32", kwargs=args(64, 32, related=1.0)),
    ]
