from pathlib import Path
import os
import numpy as np


def write_metrics(good_fruits_per_trial, bad_fruits_per_trial, traj_lens, config, output_path):
    val_fn = Path(output_path+'values.csv')
    val_fn.parent.mkdir(parents=True, exist_ok=True)
    config_fn = Path(output_path+'config.csv')
    config_fn.parent.mkdir(parents=True, exist_ok=True)
    to_write = ['avg_goodfruit', 'goodfruit_sd', 'avg_badfruit', 'badfruit_sd', 'avg_trial_len', 'trial_len_sd']
    format_string = ", ".join(["{}"] * len(to_write)) + "\n"
    with open(val_fn, 'a') as f:
        if os.stat(val_fn).st_size == 0:
            f.write(format_string.format(*to_write))
        f.write(format_string.format(np.mean(good_fruits_per_trial), np.std(good_fruits_per_trial), np.mean(bad_fruits_per_trial), np.std(bad_fruits_per_trial), np.mean(traj_lens), np.std(traj_lens)))
        f.close()

    config_to_write = ['inaccuracy_type', 'is_obstacle', 'obj_x2', 'obj_x2', 'agent_side', 'is_accurate_model', 'badfruit_region']
    format_config_string = ", ".join(["{}"] * len(config_to_write)) + "\n"
    with open(config_fn, 'a') as f1:
        if os.stat(config_fn).st_size == 0:
            f1.write(format_config_string.format(*config_to_write))
        f1.write(format_config_string.format(*config))
        f1.close()
