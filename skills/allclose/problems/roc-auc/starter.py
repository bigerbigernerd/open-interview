import numpy as np


def roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Area under the ROC curve; tied scores count one half."""
    raise NotImplementedError
