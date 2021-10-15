def precision_for_tp_fp(tp: int, fp: int, na: float = 0) -> float:
    return tp / (tp + fp) if tp + fp > 0 else na


def recall_for_tp_fn_fp(tp: int, fn: int, fp: int, na: float = 0) -> float:
    return tp / (tp + fn + fp) if tp + fn > 0 else na


def f1_for_precision_recall(precision: float, recall: float, na: float = 0) -> float:
    return 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else na
