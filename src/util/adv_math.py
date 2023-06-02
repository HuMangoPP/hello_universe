import numpy as np

def lerp(u: np.ndarray | float, v: np.ndarray | float, t: float) -> np.ndarray | float:
    return (v-u) * t + u

def gaussian_dist(x: float, opt: float, variation: float) -> float:
    return np.exp(-1/2 * ((x - opt) / variation) ** 2)

def relu(z: np.ndarray) -> np.ndarray:
    return np.maximum(0, z)

def softmax(z: np.ndarray) -> np.ndarray:
     return np.exp(z) / sum(np.exp(z))