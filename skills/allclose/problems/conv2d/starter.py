import numpy as np


def conv2d(x, w, b=None, stride=1, padding=0):
    """Cross-correlation like F.conv2d. x (N, C, H, W), w (F, C, KH, KW) -> (N, F, H_out, W_out)."""
    raise NotImplementedError
