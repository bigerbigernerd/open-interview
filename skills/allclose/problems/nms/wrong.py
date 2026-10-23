"""Buggy variants the tests must catch."""
import numpy as np


def _iou(b, rest, plus_one=0.0):
    w = np.clip(np.minimum(b[2], rest[:, 2]) - np.maximum(b[0], rest[:, 0]) + plus_one, 0, None)
    h = np.clip(np.minimum(b[3], rest[:, 3]) - np.maximum(b[1], rest[:, 1]) + plus_one, 0, None)
    inter = w * h
    area = lambda x: (x[..., 2] - x[..., 0] + plus_one) * (x[..., 3] - x[..., 1] + plus_one)
    return inter / (area(b) + area(rest) - inter)


def _greedy(boxes, order, thr, cmp, plus_one=0.0):
    keep = []
    while order.size:
        i, rest = order[0], order[1:]
        keep.append(int(i))
        order = rest[cmp(_iou(boxes[i], boxes[rest], plus_one), thr)]
    return keep


def suppress_at_equal(boxes, scores, iou_threshold):
    return _greedy(boxes, np.argsort(-scores, kind="stable"), iou_threshold, lambda a, t: a < t)


def pixel_plus_one(boxes, scores, iou_threshold):
    return _greedy(boxes, np.argsort(-scores, kind="stable"), iou_threshold, lambda a, t: a <= t, plus_one=1.0)


def input_order(boxes, scores, iou_threshold):
    return _greedy(boxes, np.arange(len(scores)), iou_threshold, lambda a, t: a <= t)


def ties_higher_index_first(boxes, scores, iou_threshold):
    order = np.lexsort((-np.arange(len(scores)), -scores))  # by score desc, then index desc
    return _greedy(boxes, order, iou_threshold, lambda a, t: a <= t)
