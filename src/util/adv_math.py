import numpy as np

def lerp(u: np.ndarray | float, v: np.ndarray | float, t: np.ndarray | float) -> np.ndarray | float:
    return (v-u) * t + u

def gaussian_dist(x: np.ndarray | float, opt: np.ndarray | float, variation: np.ndarray | float) -> np.ndarray | float:
    return np.exp(-1/2 * ((x - opt) / variation) ** 2)

def relu(z: np.ndarray) -> np.ndarray:
    return np.maximum(0, z)

def softmax(z: np.ndarray) -> np.ndarray:
     return np.exp(z) / sum(np.exp(z))

def proj(u: np.ndarray, v: np.ndarray) -> float:
    return u.dot(v) / np.linalg.norm(v)

def angle_between(u: np.ndarray, v: np.ndarray) -> float:
    return np.arccos(np.clip(u.dot(v) / np.linalg.norm(u) / np.linalg.norm(v), a_min=-1, a_max=1))

def find_poi(u: np.ndarray, v: np.ndarray, u_origin: np.ndarray, v_origin: np.ndarray) -> np.ndarray:
    a1, b1 = u[:2][::-1]
    c1 = u[:2].dot(u_origin[:2])

    a2, b2 = v[:2][::-1]
    c2 = v[:2].dot(v_origin[:2])

    return np.array([
        (c1*b2 - b1*c2) / (a1*b2 - b1*a2),
        (a1*c2 - c1*a2) / (a1*b2 - b1*a2),
        0
    ])

def triangle_wave(p: float, t: float):
    return 2 * abs(2 * (t/p - np.floor(t/p + 1/2))) - 1

def sigmoid(x: float | np.ndarray, amp: float | np.ndarray, squeeze: float | np.ndarray) -> float | np.ndarray:
    return amp * (2 / (1 + np.exp(-squeeze * x)) - 1)

def rotated_log(x: float | np.ndarray) -> float | np.ndarray:
    if x > 0:
        return np.log(x + 1)
    elif x < 0:
        return -np.log(-x + 1)
    else:
        return 0