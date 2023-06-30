import sys

from src.game import Game
from src.simulation import Simulation

if __name__ == '__main__':
    game = Game()
    if game.run():
        sim = Simulation(collection_type=2)
        while True:
            sim.update()
    sys.exit()