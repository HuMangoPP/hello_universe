
class Receptors:
    def __init__(self, receptor_data: dict):
        self.circle_receptors = receptor_data['circle']
        self.triangle_receptors = receptor_data['triangle']
        self.square_receptors = receptor_data['square']
        self.pentagon_receptors = receptor_data['pentagon']
        self.hexagon_receptors = receptor_data['hexagon']
    
    def poll_surroundings(self):
        ...
    
    def zip_num_receptors(self) -> list[int]:
        return [
            self.circle_receptors,
            self.triangle_receptors,
            self.square_receptors,
            self.pentagon_receptors,
            self.hexagon_receptors
        ]