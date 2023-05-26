import numpy as np

SINGLE_RECEPTOR_CAPACITY = 1
SHAPE_MAP = {
    'circle': 0,
    'triangle': 1,
    'square': 2,
    'pentagon': 3,
    'hexagon': 4,
}

class Receptors:
    def __init__(self, receptor_data: dict):
        self.num_circle_receptors = receptor_data['circle']
        self.num_triangle_receptors = receptor_data['triangle']
        self.num_square_receptors = receptor_data['square']
        self.num_pentagon_receptors = receptor_data['pentagon']
        self.num_hexagon_receptors = receptor_data['hexagon']
    
    def poll_sensory(self, pos: np.ndarray, sense_radius: float, env):
        sensory = {
            'circle': 0,
            'triangle': 0,
            'square': 0,
            'pentagon': 0,
            'hexagon': 0
        }
        for m_pos, m_shape, m_dens in zip(env.positions, env.shape, env.density):
            if np.linalg.norm(pos - m_pos) < sense_radius:
                match m_shape:
                    case 0:
                        sensory['circle'] = min(sensory['circle'] + m_dens, self.num_circle_receptors * SINGLE_RECEPTOR_CAPACITY)
                    case 1:
                        sensory['triangle'] = min(sensory['triangle'] + m_dens, self.num_triangle_receptors * SINGLE_RECEPTOR_CAPACITY)
                    case 2:
                        sensory['square'] = min(sensory['square'] + m_dens, self.num_square_receptors * SINGLE_RECEPTOR_CAPACITY)
                    case 3:
                        sensory['pentagon'] = min(sensory['pentagon'] + m_dens, self.num_pentagon_receptors * SINGLE_RECEPTOR_CAPACITY)
                    case 4:
                        sensory['hexagon'] = min(sensory['hexagon'] + m_dens, self.num_hexagon_receptors * SINGLE_RECEPTOR_CAPACITY)
    
    def zip_num_receptors(self) -> list[int]:
        return [
            self.num_circle_receptors,
            self.num_triangle_receptors,
            self.num_square_receptors,
            self.num_pentagon_receptors,
            self.num_hexagon_receptors
        ]