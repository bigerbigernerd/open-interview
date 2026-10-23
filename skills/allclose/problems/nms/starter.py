import numpy as np


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> list:
    """Greedy non-maximum suppression. Returns kept indices in selection order."""
    raise NotImplementedError
