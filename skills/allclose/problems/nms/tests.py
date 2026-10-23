import numpy as np


def cases():
    rng = np.random.default_rng(15)
    xy = rng.random((2000, 2)) * 100
    wh = rng.random((2000, 2)) * 20 + 1
    big = np.concatenate([xy, xy + wh], axis=1)
    classic = np.array([[10, 10, 50, 50], [12, 12, 52, 52], [100, 100, 140, 140], [11, 9, 49, 51], [102, 98, 138, 141]], dtype=float)
    return [
        dict(name="two clusters", kwargs=dict(boxes=classic, scores=np.array([0.9, 0.8, 0.7, 0.85, 0.6]), iou_threshold=0.5), sample=True),
        dict(name="no overlap keeps all, sorted by score", kwargs=dict(boxes=np.array([[0, 0, 1, 1], [2, 2, 3, 3], [4, 4, 5, 5]], dtype=float), scores=np.array([0.2, 0.9, 0.5]), iou_threshold=0.3), sample=True),
        dict(name="IoU exactly at threshold is kept", kwargs=dict(boxes=np.array([[0, 0, 2, 1], [1, 0, 3, 1]], dtype=float), scores=np.array([0.9, 0.8]), iou_threshold=1 / 3)),
        dict(name="tied scores: lower index first", kwargs=dict(boxes=np.array([[0, 0, 10, 10], [1, 1, 11, 11], [0, 0, 10, 10]], dtype=float), scores=np.array([0.5, 0.5, 0.5]), iou_threshold=0.5)),
        dict(name="threshold 0 drops any overlap", kwargs=dict(boxes=classic, scores=np.array([0.1, 0.2, 0.3, 0.4, 0.5]), iou_threshold=0.0)),
        dict(name="touching edges (IoU 0)", kwargs=dict(boxes=np.array([[0, 0, 1, 1], [1, 0, 2, 1]], dtype=float), scores=np.array([0.6, 0.7]), iou_threshold=0.0)),
        dict(name="small boxes (no +1 in area)", kwargs=dict(boxes=np.array([[0, 0, 0.5, 0.5], [0.1, 0.1, 0.6, 0.6], [0.3, 0, 0.8, 0.5]]), scores=np.array([0.9, 0.8, 0.7]), iou_threshold=0.3)),
        dict(name="N = 2000 within 2 s", kwargs=dict(boxes=big, scores=rng.random(2000), iou_threshold=0.4)),
    ]
