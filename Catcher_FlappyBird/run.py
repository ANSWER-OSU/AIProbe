import gym, sys
import domains
from VI import valueIteration
from env_helper_functions import get_num_undesired_states
from loggers import write_metrics
from pprint import pprint
import numpy as np
from argparse import ArgumentParser, ArgumentTypeError

def str2bool(value):
    if value.lower() in {'true', 'yes', '1'}:
        return True
    elif value.lower() in {'false', 'no', '0'}:
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')

parser = ArgumentParser(description="Process some parameters.")
parser.add_argument("-c", "--catcher_name", type=str, default='SourceCatcher-v0',
                    help="SourceCatcher-v0 or TargetCatcher-v0")
parser.add_argument("-o", "--is_obstacle", type=str2bool, choices=[True, False], default=False,
                    help="Indicate if there is an obstacle (True/False).")
parser.add_argument("-b", "--badfruits", type=str2bool, choices=[True, False], default=False,
                    help="Indicate if there are bad fruits (True/False).")
parser.add_argument("-a", "--is_accurate_model", type=str2bool, choices=[True, False], default=False,
                    help="Indicate if the model is accurate (True/False).")
parser.add_argument("-i", "--inaccuracy_type", type=int, choices=range(4), default=0,
                    help="Specify the type of inaccuracy (0-3).")
args = parser.parse_args()

is_obstacle = bool(args.is_obstacle)
badfruits = bool(args.badfruits)
is_accurate_model = bool(args.is_accurate_model)
inaccuracy_type = int(args.inaccuracy_type)
catcher_name = args.catcher_name

ob_x1, ob_x2 = 250, 300
agent_side = 'left'
badfruit_region = [50, 150, 250, 350, 450]
# [50, 150, 250, 350, 450]
# [250,300,350,400,450]
inaccuracy = {0: '_accurate_reward_accurate_state_rep', 1: '_inaccurate_reward_accurate_state_rep', 2: '_accurate_reward_inaccurate_state_rep', 3: '_inaccurate_reward_inaccurate_state_rep'}
config = [inaccuracy_type, is_obstacle, ob_x1, ob_x2, agent_side, is_accurate_model, badfruit_region if is_obstacle else None]

ob = '_obstacle' if is_obstacle else '_no_obstacle'
bf = '_with_badfruits_mixed/' if badfruits else '_without_badfruits/'
output_path = 'Catcher_FlappyBird/test_rew_state_inacc/inaccurate_model_test/'+catcher_name+ob+bf

env = gym.make(catcher_name)
env.set_obstacle(is_obstacle, ob_x1, ob_x2)
env.set_agent_side(agent_side)
print(badfruits, type(badfruits))
if badfruits:
    env.set_badfruit_region(badfruit_region)
env.set_is_accurate_model(is_accurate_model)
env.inaccuracy_type = inaccuracy_type
env.reset()
pprint(vars(env))

# print(env.get_states())
# valid regions: [0, 50, 100, 150, 200, 250, 300, 350, 400, 450]


# v, pi = valueIteration(env)
# good_fruits_per_trial, bad_fruits_per_trial, mean_reward, reward_sd, traj_lens = get_num_undesired_states(env, pi, 10)
# print('good fruits caught: ', good_fruits_per_trial, 'mean: ', np.mean(good_fruits_per_trial), 'sd: ', np.std(good_fruits_per_trial))
# print('bad fruits: ', bad_fruits_per_trial, 'mean: ', np.mean(bad_fruits_per_trial), 'sd: ', np.std(bad_fruits_per_trial))
# write_metrics(good_fruits_per_trial, bad_fruits_per_trial, traj_lens, config, output_path)
