from pathlib import Path
import os

def write_metrics(num_trials, env_id, undesired_states_per_trial, times_goal_reached, avg_reward, reward_sd, to_write, output_path):
    filename = Path(output_path)
    filename.parent.mkdir(parents=True, exist_ok=True)
    format_string = ", ".join(["{}"] * len(to_write)) + "\n"
    with open(filename, 'a') as f:
        if os.stat(filename).st_size == 0:
            f.write(format_string.format(*to_write))
        f.write(format_string.format(num_trials, env_id, undesired_states_per_trial, times_goal_reached, avg_reward, reward_sd))
        f.close()
