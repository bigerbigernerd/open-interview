import numpy as np


def softmax(x, axis=-1):
    z = x - np.max(x, axis=axis, keepdims=True)  # shift so the largest exponent is exp(0) = 1
    e = np.exp(z)
    return e / np.sum(e, axis=axis, keepdims=True)
