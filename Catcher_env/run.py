import gym, sys
import domains
from VI import valueIteration
from env_helper_functions import get_num_undesired_states
from pprint import pprint

env = gym.make(sys.argv[1])
env.set_obstacle(True, x1=250, x2=300)
env.set_agent_side('left')
env.reset()
pprint(vars(env))
# print(env.get_states())
# valid regions: [0, 50, 100, 150, 200, 250, 300, 350, 400, 450]
# env.badfruit_region = [50, 150, 250, 350, 450]


v, pi = valueIteration(env)
good_fruits_per_trial, bad_fruits_per_trial, mean_reward, reward_sd, start_states = get_num_undesired_states(env, pi, 10)
print('good fruits caught: ', good_fruits_per_trial)
print('bad fruits: ', bad_fruits_per_trial)
