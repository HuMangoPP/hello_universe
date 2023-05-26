# from random import uniform, randint

# class Behaviour:
#     def __init__(self, behaviour_data):
#         # float from -1 to 1. 
#         # 1. very aggressive, always fights
#         # -1. not aggressive, always flees
#         # 0 neutral
#         # a number is kept for each entity in the game
#         self.aggression = behaviour_data['aggression']

#         # float from 0 to 1
#         # 0. very lonely, does not try to herd
#         # 1. very social, herds always
#         # a number is kept for each entity in the game
#         self.herding = behaviour_data['herding']

#     def update_aggression(self, i, new_score):
#         if i<len(self.aggression):
#             self.aggression[i:i+1] = [new_score]
#         else:
#             self.aggression.append(new_score)
    
#     def update_herd_behaviour(self, i, new_score):
#         if i<len(self.herding):
#             self.herding[i:i+1] = [new_score]
#         else:
#             self.herding.append(new_score)

#     def shift(self):
#         for i in range(len(self.aggression)):
#             aggro_score = self.aggression[i]+uniform(0, 1)/100*randint(-1, 1)
#             herd_score = self.herding[i]+uniform(0, 1)/100*randint(-1, 1)
#             self.update_aggression(i, aggro_score)
#             self.update_herd_behaviour(i, herd_score)
