import numpy as np

RECEPTOR_TYPES = ['circle', 'triangle', 'square', 'pentagon', 'hexagon']
OPT_DENS_TOLERANCE = 0.1
ANGLE_TOLERANCE = 0.1

def calculate_fitness(num_entities: int, health: np.ndarray, energy: np.ndarray, stats: dict,
                      brain_history, brains: list, stomachs: list, receptors: list) -> np.ndarray:
    # calculate the individual fitness for each creature
    # based on its health and energy
    individual_fitness = health + energy

    # calculate the fitness score of each stat per point
    # by averaging across all creatures
    fitness_per_stat_point = {
        stat_type: np.average(individual_fitness / stat_values)
            for stat_type, stat_values in stats.items()
    }
    # calculate the fitness score of each creature based
    # on their stats and the shared score per point
    # averaged value across all stats
    stat_fitness = np.zeros(shape=(num_entities,))
    for stat_type in stats:
        stat_fitness = stat_fitness + fitness_per_stat_point[stat_type] * stats[stat_type]
    stat_fitness = stat_fitness / 5

    # calculate the fitness of the creature's receptor structure
    # calculate the fitness for the creature based on the number of receptors
    num_receptors = [receptor.num_receptors() for receptor in receptors]
    num_receptors = {
        receptor_type: np.array([num[receptor_type] for num in num_receptors])
        for receptor_type in RECEPTOR_TYPES
    }
    fitness_num_receptors = np.zeros(shape=(num_entities,))
    for _, num_receptors_of_type in num_receptors.items():
        fitness_num_receptors = fitness_num_receptors + np.array([
            np.average(individual_fitness[num_receptors_of_type == num])
            for num in num_receptors_of_type
        ])
    fitness_num_receptors = fitness_num_receptors / 5

    # calculate the fitness for the creature based on the spread of receptors
    receptor_spreads = [receptor.receptor_spreads() for receptor in receptors]
    receptor_spreads = {
        receptor_type: np.array([spread[receptor_type] for spread in receptor_spreads])
        for receptor_type in RECEPTOR_TYPES
    }
    fitness_receptor_spreads = np.zeros(shape=(num_entities,))
    for _, receptor_spreads_of_type in receptor_spreads.items():
        fitness_receptor_spreads = fitness_receptor_spreads + np.array([
            np.average(individual_fitness[np.abs(spread - receptor_spreads_of_type) <= ANGLE_TOLERANCE])
            for spread in receptor_spreads_of_type
        ])
    fitness_receptor_spreads = fitness_receptor_spreads / 5

    # calculate the fitness for the creature based on the fov of receptors
    receptor_fovs = [receptor.receptor_fovs() for receptor in receptors]
    receptor_fovs = {
        receptor_type: np.array([fov[receptor_type] for fov in receptor_fovs])
        for receptor_type in RECEPTOR_TYPES
    }
    fitness_receptor_fovs = np.zeros(shape=(num_entities,))
    for _, receptor_fovs_of_type in receptor_fovs.items():
        fitness_receptor_fovs = fitness_receptor_fovs + np.array([
            np.average(individual_fitness[np.abs(fov - receptor_fovs_of_type) <= ANGLE_TOLERANCE])
            for fov in receptor_fovs_of_type
        ])
    fitness_receptor_fovs = fitness_receptor_fovs / 5
    receptor_fitness = fitness_num_receptors + fitness_receptor_spreads + fitness_receptor_fovs

    # calculate the fitness of the creature's brain structure
    # calculate the fitness of each axon by averaging all creatures
    # that have that axon enabled
    axon_fitness = {
        innov: np.average(individual_fitness[np.array([brain.has_axon_of_innov(innov) for brain in brains])])
        for innov in brain_history.axon_pool.values()
    }
    # calculate the fitness of brain structure using the fitness of each axon
    brain_fitness = np.array([
        np.average(np.array([axon_fitness[innov] for innov in brain.get_innov()]))
        for brain in brains
    ])

    # calculate the fitness of each creature's stomach structure
    # get the optimal densities of all stomachs
    opt_dens_of_stomachs = [stomach.optimal_dens for stomach in stomachs]
    opt_dens_of_stomachs = {
        receptor_type: np.array([opt_dens[receptor_type] for opt_dens in opt_dens_of_stomachs])
        for receptor_type in RECEPTOR_TYPES
    }
    # calculate the fitness for each creature by sharing its fitness with creature
    # in similar species
    stomach_fitness = np.zeros(shape=(num_entities,))
    for _, opt_dens_of_type in opt_dens_of_stomachs.items():
        stomach_fitness = stomach_fitness + np.array([
            np.average(individual_fitness[np.abs(opt_dens - opt_dens_of_type) <= OPT_DENS_TOLERANCE])
            for opt_dens in opt_dens_of_type
        ])
    stomach_fitness = stomach_fitness / 5

    return stat_fitness + receptor_fitness + brain_fitness + stomach_fitness


