from pathlib import Path
import os

def write_metrics(num_trials, undesired_states_per_trial, times_goal_reached, avg_reward, reward_sd, output_path, seed, env, task):
    headers = ['Seed', 'Env#', 'Task#', '#Lava', '#AgentToGoal', '#Reward']
    filename = os.path.join('/scratch/projects/AIProbe-Main/AIProbe/Minigrid', output_path)

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    file_exists = os.path.isfile(filename)
    is_empty = not file_exists or os.stat(filename).st_size == 0

    format_string = ", ".join(["{}"] * len(headers)) + "\n"

    with open(filename, 'a') as f:
        if is_empty:
            f.write(format_string.format(*headers))
        f.write(format_string.format(seed, env, task, undesired_states_per_trial, times_goal_reached, avg_reward))
