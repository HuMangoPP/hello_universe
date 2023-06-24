import numpy as np
import random

from ..util.adv_math import lerp, sigmoid

MUTATION_RATE = 0.75
D_WEIGHT = 0.25

RECEPTOR_NAMES = np.array([
    'c', 'ca',
    't', 'ta',
    's', 'sa',
    'p', 'pa',
    'h', 'ha'
])

ACTIONS = ['rot', 'mvf', 'mvr', 'mvb', 'mvl']

class BrainHistory:
    def __init__(self):
        self.axon_pool : dict[str, int] = {}
        self.innov_number = 1
    
    def get_innov(self, label: str):
        if label not in self.axon_pool:
            self.axon_pool[label] = self.innov_number
            self.innov_number += 1
        return self.axon_pool[label]

class Axon:
    def __init__(self, in_neuron: str, out_neuron: str, weight: float, enabled=True):
        self.in_neuron = in_neuron
        self.out_neuron = out_neuron
        self.weight = weight
        self.enabled = enabled
    
class Brain:
    def __init__(self, brain_data: dict, brain_history: BrainHistory):
        self.brain_history = brain_history

        # track all neurons: in, hidden, out
        self.all_neurons = set(
            [f'i_{receptor_in}' for receptor_in in RECEPTOR_NAMES] +
            ['i_tick'] + [f'o_{action}' for action in ACTIONS] + 
            brain_data['neurons']
        )
        # set of hidden neurons
        self.hidden_neurons = set(brain_data['neurons'])

        # axons
        self.axons : dict[int, Axon] = {}
        for axon_data in brain_data['axons']:
            axon_label = f'{axon_data[0]}->{axon_data[1]}'
            self.add_axon(axon_data[0], axon_data[1], axon_data[2], 
                          self.brain_history.get_innov(axon_label))

    def add_neuron(self, neuron_id: str):
        self.hidden_neurons.add(neuron_id)
        self.neuron_ids.add(neuron_id)

    def add_axon(self, in_neuron: str, out_neuron: str, weight: float, innov: int):
        self.axons[innov] = Axon(in_neuron, out_neuron, weight)
    
    # evo
    def mutate(self, itl_stat: float):
        # determine the number of neurons and enabled axons
        num_neurons = len(self.neurons)
        active_axons = [axon for axon in self.axons.values() if axon.enabled]

        # adds a new random connection or changes its weight if it exists
        if random.uniform(0, 1) <= MUTATION_RATE:
            # find an in and out neuron
            in_neuron = random.choice([neuron_id for neuron_id in self.neuron_ids 
                                       if neuron_id.split('_')[0] in 'ih'])
            out_neuron = random.choice([neuron_id for neuron_id in self.neuron_ids 
                                        if neuron_id.split('_')[0] == 'o'])
            
            # add axon
            axon_label = f'{in_neuron}->{out_neuron}'
            innov = self.brain_history.get_innov(axon_label)
            if innov in self.axons: # change weight
                self.axons[innov].weight += random.uniform(-D_WEIGHT, D_WEIGHT)
            else: # add axon
                self.add_axon(in_neuron, out_neuron, random.uniform(-1, 1), innov)

        # adds new neuron and connects it on both sides
        if random.uniform(0, 1) <= MUTATION_RATE and active_axons:
            new_neuron_id = f'h_{num_neurons}'
            num_neurons += 1
            self.add_neuron(new_neuron_id)
            
            # choose a random connection to insert into
            axon_to_replace = random.choice(active_axons)
            
            # left connection
            axon_label = f'{axon_to_replace.in_neuron}->{new_neuron_id}'
            self.add_axon(axon_to_replace.in_neuron, new_neuron_id, 
                          axon_to_replace.weight, self.brain_history.get_innov(axon_label))
            
            # right connection
            axon_label = f'{new_neuron_id}->{axon_to_replace.out_neuron}'
            self.add_axon(new_neuron_id, axon_to_replace.out_neuron,
                          1, self.brain_history.get_innov(axon_label))

        # change a random weight
        if random.uniform(0, 1) <= MUTATION_RATE and active_axons:
            axon_to_change = random.choice(active_axons)
            axon_to_change.weight += random.uniform(-D_WEIGHT, D_WEIGHT)

    def cross_breed(self, other_brain) -> dict:
        t = random.uniform(0.5, 0.75)
        axon_data = []
        for innov, axon in self.axons.items():
            if innov in other_brain.axons:
                axon_data.append([
                    axon.in_neuron,
                    axon.out_neuron,
                    lerp(axon.weight, other_brain.axons[innov].weight, t)
                ])
            else:
                axon_data.append([
                    axon.in_neuron,
                    axon.out_neuron,
                    axon.weight,
                ])
        # for innov, axon in other_brain.axons.items():
        #     if innov not in self.axons:
        #         axon_data.append([
        #             axon.in_neuron,
        #             axon.out_neuron,
        #             axon.weight
        #         ])

        brain_data = {
            'neurons': list(self.neurons),
            'axons': axon_data       
        }
        return brain_data
    
    # functionality
    def think(self, receptor_activations: np.ndarray, clock_actv: float) -> dict:
        # build the input layer
        input_layer = {
            **{
                f'i_{label}': activation
                for label, activation in zip(RECEPTOR_NAMES, receptor_activations)
            },
            'i_tick': clock_actv,
        }
        # create the output layer
        output_layer = {
            f'o_{action}': 0
            for action in ACTIONS
        }
        # update the list of all neurons with their ids
        self.neuron_ids = set(input_layer.keys()).union(set(output_layer.keys())).union(self.neurons)

        # propagate activations
        activated_neurons = {
            neuron_id: activation
            for neuron_id, activation in input_layer.items()
        }
        axons_to_fire = [axon for axon in self.axons.values() if axon.in_neuron in activated_neurons and axon.enabled]
        while axons_to_fire:
            new_neurons = {}
            for axon in axons_to_fire:
                if axon.out_neuron in output_layer:
                    output_layer[axon.out_neuron] += activated_neurons[axon.in_neuron] * axon.weight
                else:
                    new_neurons[axon.out_neuron] = sigmoid(activated_neurons[axon.in_neuron] * axon.weight)
            activated_neurons = new_neurons
            axons_to_fire = [axon for axon in self.axons.values() if axon.in_neuron in activated_neurons and axon.enabled]

        return {
            action[2:]: actv for action, actv in output_layer.items()
        }

    def get_energy_cost(self) -> float:
        return 0.5 * len([axon for axon in self.axons.values() if axon.enabled])

    # data
    def get_df(self):
        '''JSON format'''
        return {
            axon_label: axon.weight
            for axon_label, axon in self.axons.items()
        }
    