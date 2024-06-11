import gym, sys
import domains
from VI import valueIteration
from env_helper_functions import get_num_undesired_states
# from loggers import write_metrics
from pprint import pprint
import numpy as np

env = gym.make(sys.argv[1])
states = env.get_states()
env.reset()
# pprint(vars(env))
# print(env.get_states())
v, pi = valueIteration(env)
num_past_pipe_per_trial, num_crashes_per_trial, mean_reward, reward_sd, traj_lens, times_goal_reached = get_num_undesired_states(env, pi, 10, is_flappy=True)
print('pipes crossed: ', num_past_pipe_per_trial, 'mean: ', np.mean(num_past_pipe_per_trial), 'sd: ', np.std(num_past_pipe_per_trial))
print('# crashes: ', num_crashes_per_trial, 'mean: ', np.mean(num_crashes_per_trial), 'sd: ', np.std(num_crashes_per_trial))
print('no. of times goal was reached = ', times_goal_reached)
