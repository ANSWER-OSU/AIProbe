# script.py
import sys
import os

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from env import CustomMiniGridEnv
from Minigrid.LoadConfig import load_InitialState
from Minigrid.computePolicy.VI import valueIteration
from Minigrid.computePolicy.helper_functions import get_num_undesired_states
from Minigrid.computePolicy.loggers import write_metrics
import os

# parameters to change
accurate_model=True if str(sys.argv[1])=='True' else False
inaccuracy_type=int(sys.argv[2])
if accurate_model:
    inaccuracy_type=0
inaccuracy = {0: '_accurate_reward_accurate_state_rep', 1: '_inaccurate_reward_accurate_state_rep', 2: '_accurate_reward_inaccurate_state_rep', 3: '_inaccurate_reward_inaccurate_state_rep'}

env_config_dir = 'Minigrid/Env Configs/Four room Env'
num_sim_trials = 1

# output path
num_envs = len(next(os.walk(env_config_dir))[1])
to_write = ['#Trials', 'envID', '#Landmine', '#WrongKey','#Goal', '#Reward']
start_idx = env_config_dir.rfind('/') + 1
end_idx = env_config_dir.rfind('')
filename = str(env_config_dir[start_idx:end_idx].replace(' ', '_'))
model = inaccuracy[inaccuracy_type]
output_path = 'Minigrid/computePolicy/outputs_for_new_config_2/'+filename+model+'.csv'

# for env_id in range(1, num_envs+1):
#     file_path = os.path.join(env_config_dir+'/Env-'+str(env_id), 'Config.xml')
for folder_name in os.listdir(env_config_dir):
    if folder_name.startswith('Env-'):
        file_path = os.path.join(env_config_dir, folder_name, 'Config.xml')
        env_id = folder_name.split('-')[1]
    grid, grid_size = load_InitialState(file_path)
    env = CustomMiniGridEnv(grid, grid_size, accurate_model=accurate_model, task='keyToGoal', inaccuracy_type=inaccuracy_type, render_mode="human")
    env.reset()
    print(env)
    # print(env.get_state_factor_rep())
    v, pi = valueIteration(env)
    avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(env, pi, trials=num_sim_trials)
    print(avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward)

    write_metrics(num_sim_trials, env_id, avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward, reward_sd, to_write, output_path)
