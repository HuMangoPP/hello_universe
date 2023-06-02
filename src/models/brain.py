import numpy as np
import random

from ..util.adv_math import lerp, relu, softmax


NEURON_TYPES = {
    'sensor': 0,
    'hidden': 1,
    'effector': 2,
}
THRESHOLD_VALUE = 1/3

MUTATION_RATE = 0.1
D_WEIGHT = 0.1

class BrainHistory:
    def __init__(self):
        self.axon_pool = {}
        self.innov_number = 1


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
    

class Brain:
    def __init__(self, brain_data: dict, brain_history: BrainHistory):
        self.brain_history = brain_history
        neurons = brain_data['neurons']
        axons = brain_data['axons']
        self.neurons = [Neuron(neuron_type) for neuron_type in neurons]
        self.axons : list[Axon] = []
        for axon in axons:
            # determine innov number
            axon_label = f"{axon['in']}-{axon['out']}"
            if axon_label not in self.brain_history.axon_pool:
                self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                self.brain_history.innov_number += 1

            # add axon
            self.axons.append(Axon(axon['in'], axon['out'], axon['w'], self.brain_history.axon_pool[axon_label]))
    
    def mutate(self, itl_stat: float):
        # determine the allowed number of neurons and axons based on the itl stat
        allowed_neurons = int(itl_stat / 5) 
        allowed_axons = int(itl_stat / 2) + 5

        # determine the number of neurons (not including sensors or effectors)
        # and enabled axons
        num_neurons = len([neuron for neuron in self.neurons if neuron.neuron_type == 1])
        num_active_axons = len([axon for axon in self.axons if axon.enabled])

        # if num_neurons < allowed_neurons and num_active_axons < allowed_axons:
        if random.uniform(0, 1) <= MUTATION_RATE:
            # mutation adds neuron and splits a connection into two
            self.add_neuron(1)
            
            # choose a random connection to insert a node into
            axon_to_replace = random.choice(self.axons)
            axon_to_replace.enabled = False
            
            # determine innov numbers
            axon_label = f'{axon_to_replace.in_neuron}-{num_neurons}'
            if axon_label not in self.brain_history.axon_pool:
                self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                self.brain_history.innov_number += 1
            self.add_axon(axon_to_replace.in_neuron, num_neurons, axon_to_replace.weight, self.brain_history.axon_pool[axon_label])

            axon_label = f'{num_neurons}-{axon_to_replace.out_neuron}'
            if axon_label not in self.brain_history.axon_pool:
                self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                self.brain_history.innov_number += 1
            self.add_axon(num_neurons, axon_to_replace.out_neuron, 1, self.brain_history.axon_pool[axon_label])

            # increase these for later parts of the algorithm
            num_neurons += 1
            num_active_axons += 1
        # if num_active_axons < allowed_axons:
        if random.uniform(0, 1) <= MUTATION_RATE:
            # mutation adds a new random connection or changes its weight if it exists
            # find an in and out neuron
            in_neuron = random.choice([index for index, neuron in enumerate(self.neurons) if neuron.neuron_type in [0, 1]])
            out_neuron = random.choice([index for index, neuron in enumerate(self.neurons) if neuron.neuron_type in [1, 2] and index != in_neuron])
            # get all of the axons 
            axon_labels = {f'{axon.in_neuron}-{axon.out_neuron}': axon for axon in self.axons}
            axon_label = f'{in_neuron}-{out_neuron}'
            if axon_label in axon_labels:
                # change the weight of this axon
                axon_labels[axon_label].weight += random.uniform(-D_WEIGHT, D_WEIGHT)
            else:
                # otherwise, add the axon
                # determine the innov number
                if axon_label not in self.brain_history.axon_pool:
                    self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                    self.brain_history.innov_number += 1
                self.add_axon(in_neuron, out_neuron, random.uniform(0, 1), self.brain_history.axon_pool[axon_label])
        if random.uniform(0, 1) <= MUTATION_RATE:
            # change a random weight
            axon_to_change = random.choice(self.axons)
            axon_to_change.weight += random.uniform(-D_WEIGHT, D_WEIGHT)

    def cross_breed(self, other_brain) -> dict:
        t = random.uniform(0.25, 0.75)
        axon_data = []
        for axon in self.axons:
            if other_brain.has_axon_of_innov(axon.innov):
                axon_data.append({
                    'in': axon.in_neuron,
                    'out': axon.out_neuron,
                    'w': lerp(axon.weight, other_brain.get_axon_weight(axon.in_neuron, axon.out_neuron), t)
                })
            else:
                axon_data.append({
                    'in': axon.in_neuron,
                    'out': axon.out_neuron,
                    'w': axon.weight
                })
        for axon in other_brain.axons:
            if not self.has_axon_of_innov(axon.innov):
                axon_data.append({
                    'in': axon.in_neuron,
                    'out': axon.out_neuron,
                    'w': axon.weight
                })

        brain_data = {
            'neurons': self.get_neuron_types() if len(self.neurons) > len(other_brain.neurons) else other_brain.get_neuron_types(),
            'axons': axon_data       
        }
        return brain_data

    def add_neuron(self, neuron_type: int):
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

    def get_energy_cost(self) -> float:
        return 0.5 * len([axon for axon in self.axons if axon.enabled])
    
    def get_neuron_types(self) -> list:
        return [neuron.neuron_type for neuron in self.neurons]

    def get_axon_weight(self, in_neuron: int, out_neuron: int) -> float:
        for axon in self.axons:
            if axon.in_neuron == in_neuron and axon.out_neuron == out_neuron:
                return axon.weight
            
        return -1

    def has_axon_of_innov(self, innov: int) -> bool:
        return innov in set([axon.innov for axon in self.axons if axon.enabled])

    def get_innov(self) -> list:
        return [axon.innov for axon in self.axons if axon.enabled]