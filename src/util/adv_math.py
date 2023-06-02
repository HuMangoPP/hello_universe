import numpy as np

def lerp(u: np.ndarray | float, v: np.ndarray | float, t: float) -> np.ndarray | float:
    return (v-u) * t + u

def gaussian_dist(x: float, opt: float, variation: float) -> float:
    return np.exp(-1/2 * ((x - opt) / variation) ** 2)