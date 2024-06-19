# script.py
import sys
import os

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


from env import CustomMiniGridEnv
from Minigrid.LoadConfig import load_InitialState
from Minigrid.computePolicy.VI import valueIteration
from Minigrid.computePolicy.helper_functions import simulate_trajectory, get_num_undesired_states
from Minigrid.computePolicy.loggers import write_metrics
import os

# parameters to change
accurate_model=False
# env_config_dir = './Env Configs/7 lava Tile'
env_config_dir = 'Minigrid/Env Configs/4Rooms_7Tile'
num_sim_trials = 10

# output path
num_envs = len(next(os.walk(env_config_dir))[1])
to_write = ['#Trials', 'envID', '#Lava', '#Goal', '#AvgReward', '#RewardSD']
start_idx = env_config_dir.rfind('/') + 1
end_idx = env_config_dir.rfind('')
filename = str(env_config_dir[start_idx:end_idx].replace(' ', '_'))
model = '_accurate_model' if accurate_model else '_inaccurate_model'
output_path = 'Minigrid/computePolicy/outputs/'+filename+model+'.csv'

for env_id in range(1, num_envs+1):
    file_path = os.path.join(env_config_dir+'/Env '+str(env_id), 'Config.xml')
    grid, grid_size = load_InitialState(file_path)
    env = CustomMiniGridEnv(grid, grid_size, accurate_model=accurate_model, task='keyToGoal', render_mode="human")
    env.reset()
    print(env)
    v, pi = valueIteration(env)
    avg_undesired_states, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(env, pi, trials=num_sim_trials)

    write_metrics(num_sim_trials, env_id, avg_undesired_states, times_goal_reached, avg_reward, reward_sd, to_write, output_path)
