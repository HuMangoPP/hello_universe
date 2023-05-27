import numpy as np

def relu(z: np.ndarray) -> np.ndarray:
    return np.maximum(0, z)

def softmax(z: np.ndarray) -> np.ndarray:
     return np.exp(z) / sum(np.exp(z))


NEURON_TYPES = {
    'sensor': 0,
    'hidden': 1,
    'effector': 2,
}
THRESHOLD_VALUE = 1/3

class Brain:
    def __init__(self, brain_data: dict):
        neurons = brain_data['neurons']
        axons = brain_data['axons']
        self.neurons = [Neuron(neuron_type) for neuron_type in neurons]
        self.axons = [
            Axon(axon['in'], axon['out'], axon['w'], axon['i'])
            for axon in axons
        ]
    
    def mutate(self):
        ...
    
    def add_node(self, neuron_type: int):
        self.neurons.append(Neuron(neuron_type))

    def add_axon(self, in_neuron: int, out_neuron: int, weight: float, innov: int):
        self.axons.append(Axon(in_neuron, out_neuron, weight, innov))
    
    def think(self, input_activations: np.ndarray) -> np.ndarray:
        [self.neurons[i].set_activation(activation) for
         i, activation in enumerate(input_activations)]
        activated_neurons = np.arange(input_activations.size)
        axons_to_fire = [axon for axon in self.axons if axon.in_neuron in activated_neurons and axon.enabled]
        while axons_to_fire:
            [self.neurons[axon.out_neuron].set_activation(relu(self.neurons[axon.in_neuron].activation * axon.weight)) 
             for axon in axons_to_fire]
            activated_neurons = [axon.out_neuron for axon in axons_to_fire]
            axons_to_fire = [axon for axon in self.axons if axon.in_neuron in activated_neurons and axon.enabled]

        output_neurons = np.array([neuron.activation for neuron in self.neurons if neuron.neuron_type == NEURON_TYPES['effector']])
        output_neurons = softmax(output_neurons)
        meets_threshold = output_neurons > THRESHOLD_VALUE
        return np.arange(output_neurons.size)[meets_threshold]


class Neuron:
    def __init__(self, neuron_type: int):
        self.neuron_type = neuron_type
        self.activation = 0

    def set_activation(self, activation: float):
        self.activation = activation

class Axon:
    def __init__(self, in_neuron: int, out_neuron: int, weight: float,
                 innov: int, enabled=True):
        self.in_neuron = in_neuron
        self.out_neuron = out_neuron
        self.weight = weight
        self.innov = innov
        self.enabled = enabled
