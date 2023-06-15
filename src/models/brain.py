import numpy as np
import random

from ..util.adv_math import lerp, relu, softmax

MUTATION_RATE = 1
D_WEIGHT = 0.25

class BrainHistory:
    def __init__(self):
        self.axon_pool = {}
        self.innov_number = 1

class Axon:
    def __init__(self, in_neuron: str, out_neuron: str, weight: float, enabled=True):
        self.in_neuron = in_neuron
        self.out_neuron = out_neuron
        self.weight = weight
        self.enabled = enabled
    
class Brain:
    def __init__(self, brain_data: dict, brain_history: BrainHistory):
        self.brain_history = brain_history
        self.neuron_ids = set()
        self.neurons = set(brain_data['neurons'])
        self.axons : dict[int, Axon] = {}
        for axon_data in brain_data['axons']:
            axon_label = f'{axon_data[0]}->{axon_data[1]}'
            if axon_label not in self.brain_history.axon_pool:
                self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                self.brain_history.innov_number += 1
            self.add_axon(axon_data[0], axon_data[1], axon_data[2], self.brain_history.axon_pool[axon_label])

    def add_neuron(self, neuron_id: str):
        self.neurons.add(neuron_id)
        self.neuron_ids.add(neuron_id)

    def add_axon(self, in_neuron: str, out_neuron: str, weight: float, innov: int):
        self.axons[innov] = Axon(in_neuron, out_neuron, weight)
    
    # evo
    def mutate(self, itl_stat: float):
        # determine the allowed number of neurons and axons based on the itl stat
        allowed_neurons = int(itl_stat / 5) 
        allowed_axons = int(itl_stat / 2) + 5

        # determine the number of neurons (not including sensors or effectors)
        # and enabled axons
        num_neurons = len(self.neurons)
        active_axons = [axon for axon in self.axons.values() if axon.enabled]

        # adds a new random connection or changes its weight if it exists
        if random.uniform(0, 1) <= MUTATION_RATE:
            # find an in and out neuron
            in_neuron = random.choice([neuron_id for neuron_id in self.neuron_ids if neuron_id.split('_')[0] in 'ih'])
            out_neuron = random.choice([neuron_id for neuron_id in self.neuron_ids if neuron_id.split('_')[0] == 'o'])
            
            # get all of the axons 
            axon_label = f'{in_neuron}->{out_neuron}'
            if axon_label in self.brain_history.axon_pool:
                innov = self.brain_history.axon_pool[axon_label]
                if innov in self.axons:
                # change the weight of this axon
                    self.axons[innov].weight += random.uniform(-D_WEIGHT, D_WEIGHT)
                else:
                    self.add_axon(in_neuron, out_neuron, random.uniform(0, 1), innov)
            else:
                # otherwise, add the axon
                # determine the innov number
                self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                self.brain_history.innov_number += 1
                self.add_axon(in_neuron, out_neuron, random.uniform(0, 1), self.brain_history.axon_pool[axon_label])

        # adds new neuron and connects it on both sides
        if random.uniform(0, 1) <= MUTATION_RATE:
            new_neuron_id = f'h_{num_neurons}'
            self.add_neuron(new_neuron_id)
            
            # choose a random connection to insert a node into
            if active_axons:
                axon_to_replace = random.choice(active_axons)
                axon_to_replace.enabled = False
                
                # determine innov numbers
                axon_label = f'{axon_to_replace.in_neuron}->{new_neuron_id}'
                if axon_label not in self.brain_history.axon_pool:
                    self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                    self.brain_history.innov_number += 1
                self.add_axon(axon_to_replace.in_neuron, new_neuron_id, axon_to_replace.weight, self.brain_history.axon_pool[axon_label])

                axon_label = f'{new_neuron_id}->{axon_to_replace.out_neuron}'
                if axon_label not in self.brain_history.axon_pool:
                    self.brain_history.axon_pool[axon_label] = self.brain_history.innov_number
                    self.brain_history.innov_number += 1
                self.add_axon(new_neuron_id, axon_to_replace.out_neuron, 1, self.brain_history.axon_pool[axon_label])
        
        # change a random weight
        if random.uniform(0, 1) <= MUTATION_RATE:
            if active_axons:
                axon_to_change = random.choice(active_axons)
                axon_to_change.weight += random.uniform(-D_WEIGHT, D_WEIGHT)

    def cross_breed(self, other_brain) -> dict:
        t = random.uniform(0.25, 0.75)
        axon_data = []
        for innov, axon in self.axons.items():
            if innov in other_brain.axons:
                axon_data.append([
                    axon.in_neuron,
                    axon.out_neuron,
                    lerp(axon.weight, other_brain.get_axon_weight(axon.innov), t)
                ])
            else:
                axon_data.append([
                    axon.in_neuron,
                    axon.out_neuron,
                    axon.weight,
                ])
        for innov, axon in other_brain.axons.items():
            if innov not in self.axons:
                axon_data.append([
                    axon.in_neuron,
                    axon.out_neuron,
                    axon.weight
                ])

        brain_data = {
            'neurons': self.neurons,
            'axons': axon_data       
        }
        return brain_data
    
    # functionality
    def think(self, receptor_activations: np.ndarray, joint_activation: dict,
              muscle_activation: dict) -> dict:
        # when we think, we build the input layer
        receptor_input = {
            f'i_r{index}': activation
            for index, activation in enumerate(receptor_activations)
        }
        # joint_input = {
        #     f'i_{joint_id}': activation
        #     for joint_id, activation in joint_activation.items()
        # }
        # muscle_input = {
        #     f'i_{muscle_id}': activation
        #     for muscle_id, activation in muscle_activation.items()
        # }
        input_layer = {
            **receptor_input,
            # **joint_input,
            # **muscle_input
        }
        # create the output layer
        output_layer = {
            f'o_{muscle_id}': 0
            for muscle_id in muscle_activation
        }
        # update the list of all neuronds with their ids
        self.neuron_ids = set(input_layer.keys()).union(set(output_layer.keys())).union(self.neurons)

        # disable axons that are no longer used, an axon is no longer used if it
        # does not have an input or output neuron
        for axon in self.axons.values():
            if axon.in_neuron.split('_')[0] == 'i' and axon.in_neuron not in input_layer:
                axon.enabled = False
            elif axon.out_neuron.split('_')[0] == 'o' and axon.out_neuron not in output_layer:
                axon.enabled = False
        
        activated_neurons = {
            neuron_id: activation
            for neuron_id, activation in input_layer.items()
        }
        axons_to_fire = [axon for axon in self.axons.values() if axon.in_neuron in activated_neurons and axon.enabled]
        while axons_to_fire:
            new_neurons = {}
            for axon in axons_to_fire:
                if axon.out_neuron in output_layer:
                    output_layer[axon.out_neuron] += relu(activated_neurons[axon.in_neuron] * axon.weight)
                else:
                    new_neurons[axon.out_neuron] = relu(activated_neurons[axon.in_neuron] * axon.weight)
            activated_neurons = new_neurons
            axons_to_fire = [axon for axon in self.axons.values() if axon.in_neuron in activated_neurons and axon.enabled]

        output_activation = np.array(list(output_layer.values()))
        output_activation = softmax(output_activation)
        output_activation = np.clip(output_activation - 1 / output_activation.size, a_min=0, a_max=None)
        output_activation = output_activation * output_activation.size
        return {
            muscle_id.split('_')[1]: activation
            for muscle_id, activation in zip(output_layer.keys(), output_activation)
        }

    def get_energy_cost(self) -> float:
        return 0.5 * len([axon for axon in self.axons.values() if axon.enabled])

    # rendering
    def get_hidden_layers(self):
        layers = []
        current_layer = [axon.out_neuron for axon in self.axons.values() if axon.in_neuron.split('_')[0] == 'i' and axon.enabled and axon.out_neuron.split('_')[0] == 'h']
        while current_layer:
            layers.append(current_layer)
            current_layer = set(current_layer)
            current_layer = [axon.out_neuron for axon in self.axons.values() if axon.in_neuron in current_layer and axon.enabled and axon.out_neuron.split('_')[0] == 'h']
        return layers

    # data
    def get_df(self):
        return {
            axon_label: self.axons[innov].weight if innov in self.axons else np.nan
            for axon_label, innov in self.brain_history.axon_pool.items()
        }
    