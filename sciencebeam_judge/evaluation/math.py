from __future__ import division

import numpy as np


def mean(data):
    return sum(data) / len(data)


def safe_mean(data, default_value=0):
    return mean(data) if data else default_value


def is_close(a, b):
    return np.allclose([a], [b])
