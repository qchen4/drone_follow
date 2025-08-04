# utils/math_utils.py
import numpy as np

def clamp(val, lo, hi):
    """Return *val* bounded to [lo, hi]."""
    return max(lo, min(hi, val))

def vec_length(vec):
    """Euclidean length of a 2- or 3-element iterable."""
    return float(np.linalg.norm(vec))
