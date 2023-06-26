import numpy as np
import pygame as pg
import random

from ...util import lerp, sigmoid

# mut
MUTATION_RATE = 0.1
D_WEIGHT = 0.1

# neurons
RECEPTOR_NAMES = np.array([
    'c', 'ca',
    't', 'ta',
    's', 'sa',
    'p', 'pa',
    'h', 'ha'
])
ACTIONS = ['rot', 'mvf', 'mvr', 'mvb', 'mvl']
SIGMOID_SQUEEZE = 5


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
    
    def get_label(self):
        return f'{self.in_neuron}->{self.out_neuron}'

# helper
def sum_actv(axons: dict[int, Axon], in_neurons: list, activations: dict[str, float]) -> float:
    actv = 0
    for nid in in_neurons:
        if nid not in activations:
            in_neurons_for_nid = [axon.in_neuron for axon in axons.values() if axon.enabled and axon.out_neuron == nid]
            activations[nid] = None
            activations[nid] = sigmoid(sum_actv(axons, in_neurons_for_nid, activations), 1, SIGMOID_SQUEEZE)
        
        if activations[nid] is not None:
            actv += activations[nid]
    return actv

def render_neuron(display: pg.Surface, x: float, y: float, font, nid: str, actv: float,
                  radius=5, font_size=10, text_loc : str | None=None):
    color = (max(-255 * actv, 0), max(255 * actv, 0), 0)
    pg.draw.circle(display, color, (x, y), radius)
    if text_loc is None:
        return
    if text_loc == 'left':
        font.render(display, nid, x - 1.25 * (len(nid) + 1) * font_size, y, (255, 255, 255), size=font_size, style='left')
    else:
        font.render(display, nid, x + 2.25 * font_size, y, (255, 255, 255), size=font_size, style='left')

def render_axon(display: pg.Surface, inn: tuple, outn: tuple, weight: float):
    norm = sigmoid(weight, 255, 1)
    color = (max(-norm, 0), max(norm, 0), 0)
    pg.draw.line(display, color, inn, outn)

class Brain:
    def __init__(self, brain_data: dict, brain_history: BrainHistory):
        self.brain_history = brain_history

        # set of hidden neurons
        self.hidden_neurons = set(brain_data['neurons'])

        # axons
        self.axons : dict[int, Axon] = {}
        for axon_data in brain_data['axons']:
            axon_label = f'{axon_data[0]}->{axon_data[1]}'
            self.add_axon(axon_data[0], axon_data[1], axon_data[2], 
                          self.brain_history.get_innov(axon_label))

    def adv_init(self):   
        # activations
        self.activations = {
            **{f'i_{inn}': 0
               for inn in RECEPTOR_NAMES},
            **{hn: 0
               for hn in self.hidden_neurons},
            **{f'o_{action}': 0
               for action in ACTIONS},
            'i_tick': 0
        }

    def add_neuron(self, neuron_id: str):
        self.hidden_neurons.add(neuron_id)
        self.hidden_neurons.add(neuron_id)

    def add_axon(self, in_neuron: str, out_neuron: str, weight: float, innov: int):
        self.axons[innov] = Axon(in_neuron, out_neuron, weight)
    
    # evo
    def mutate(self, itl_stat: float):
        # determine the number of neurons and enabled axons
        num_neurons = len(self.hidden_neurons)
        active_axons = [axon for axon in self.axons.values() if axon.enabled]

        # adds a new random connection or changes its weight if it exists
        if random.uniform(0, 1) <= MUTATION_RATE:
            # find an in and out neuron
            in_neuron = random.choice([f'i_{sensor}' for sensor in RECEPTOR_NAMES] +
                                      ['i_tick'] +
                                      list(self.hidden_neurons))
            out_neuron = random.choice([f'o_{action}' for action in ACTIONS])
            
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

    def reproduce(self) -> dict:
        return {
            'neurons': list(self.hidden_neurons),
            'axons': [[axon.in_neuron, axon.out_neuron, axon.weight] 
                      for axon in self.axons.values()]
        }

    # functionality
    def think(self, receptor_activations: np.ndarray, clock_actv: float) -> dict:
        # create the output layer
        output_layer = {
            f'o_{action}': 0
            for action in ACTIONS
        }

        # propagate activations
        activations = {
            **{
                f'i_{sensor}': activation
                for sensor, activation in zip(RECEPTOR_NAMES, receptor_activations)
            },
            'i_tick': clock_actv,
        }

        for action in output_layer:
            in_neurons = [axon.in_neuron for axon in self.axons.values() if axon.enabled and axon.out_neuron == action]
            output_layer[action] = sigmoid(sum_actv(self.axons, in_neurons, activations), 1, 5)

        self.activations = {
            **activations,
            **output_layer,
        }
        return {
            action[2:]: actv for action, actv in output_layer.items()
        }

    def get_energy_cost(self) -> float:
        return 0.5 * len([axon for axon in self.axons.values() if axon.enabled])

    # render
    def render_monitor(self, display: pg.Surface, font):
        input_layer = {
            nid: actv
            for nid, actv in self.activations.items()
            if nid.split('_')[0] == 'i'
        }
        output_layer = {
            nid: actv
            for nid, actv in self.activations.items()
            if nid.split('_')[0] == 'o'
        }
        hidden_neurons = {
            nid: actv
            for nid, actv in self.activations.items()
            if nid.split('_')[0] == 'h'
        }

        viz_loc = {}

        input_size = len(input_layer.keys())
        y = 100 - 15 * (input_size - 1) / 2
        for nid, actv in input_layer.items():
            render_neuron(display, 100, y, font, nid, actv, text_loc='left')
            viz_loc[nid] = (100,y)
            y += 15
        
        output_size = len(output_layer.keys())
        y = 100 - 15 * (output_size - 1) / 2
        for nid, actv in output_layer.items():
            render_neuron(display, 540, y, font, nid, actv, text_loc='right')
            viz_loc[nid] = (540,y)
            y += 15
        
        hidden_size = len(hidden_neurons.keys())
        if hidden_size > 0:
            angle = np.pi
            angle_step = 2 * np.pi / hidden_size
            for nid, actv in hidden_neurons.items():
                x, y = 80 * np.cos(angle), 80 * np.sin(angle)
                render_neuron(display, x, y, font, nid, actv)
                viz_loc[nid] = (x,y)
                angle += angle_step
        
        for axon in self.axons.values():
            render_axon(display, viz_loc[axon.in_neuron],
                        viz_loc[axon.out_neuron], axon.weight)


    # data
    def get_model(self):
        '''JSON format'''
        return {
            axon.get_label(): axon.weight
            for axon in self.axons.values()
        }
    
    def get_sim_data(self):
        '''JSON format'''
        return self.activations