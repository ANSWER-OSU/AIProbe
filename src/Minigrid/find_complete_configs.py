import os
import pandas as pd

def get_all_configurations(base_dir):
    all_configs = set()
    for seed in os.listdir(base_dir):
        seed_path = os.path.join(base_dir, seed)
        if not os.path.isdir(seed_path):
            continue
        for env in os.listdir(seed_path):
            if not env.startswith("Env_"):
                continue
            env_path = os.path.join(seed_path, env)
            env_num = int(env.split("_")[1])
            for task in os.listdir(env_path):
                if not task.startswith("Task_"):
                    continue
                task_path = os.path.join(env_path, task)
                task_num = int(task.split("_")[1])
                init_xml = os.path.join(task_path, "initialState.xml")
                final_xml = os.path.join(task_path, "finalState.xml")
                if os.path.exists(init_xml) and os.path.exists(final_xml):
                    all_configs.add((int(seed), env_num, task_num))
    return all_configs

def get_completed_configurations(csv_file):
    df = pd.read_csv(csv_file)
    completed = set(zip(df['Seed'], df[' Env#'], df[' Task#']))
    return completed

def find_missing_configs(base_dir, csv_file, output_file="missing_configs.csv"):
    all_configs = get_all_configurations(base_dir)
    completed_configs = get_completed_configurations(csv_file)
    missing_configs = sorted(all_configs - completed_configs)

    df_missing = pd.DataFrame(missing_configs, columns=["Seed", "Env#", "Task#"])
    df_missing.to_csv(output_file, index=False)
    print(f"🔍 Missing configurations saved to {output_file} ({len(df_missing)} entries).")

# Replace with your actual paths
base_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50/100_Bin"
csv_file = "lava_results_custom_new/accurate_reward_accurate_state_rep_results.csv"

find_missing_configs(base_dir, csv_file)
