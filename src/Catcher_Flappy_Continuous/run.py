import os
import csv
import pickle
import torch
import numpy as np
import torch.nn as nn
from time import time
from multiprocessing import get_context
from helper_functions import create_flappy_bird_env_from_xml

# === GLOBALS (shared per worker)
AGENT = None
DEVICE = None
INACC_TYPE = None
OUTPUT_DIR = "inaccurate_reward/"

# === PPO Agent Definition ===
class Agent(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.critic = nn.Sequential(
            nn.Linear(np.array(env.observation_space.shape).prod(), 64),
            nn.Tanh(), nn.Linear(64, 64),
            nn.Tanh(), nn.Linear(64, 1),
        )
        self.actor = nn.Sequential(
            nn.Linear(np.array(env.observation_space.shape).prod(), 64),
            nn.Tanh(), nn.Linear(64, 64),
             nn.Tanh(), nn.Linear(64, env.action_space.n),
        )

    def get_action(self, x):
        logits = self.actor(x)
        probs = torch.distributions.Categorical(logits=logits)
        return probs.sample()

# === Init each worker once
def init_worker(checkpoint_path, inaccuracy_type, output_dir, dummy_xml):
    global AGENT, DEVICE, INACC_TYPE, OUTPUT_DIR
    INACC_TYPE = inaccuracy_type
    OUTPUT_DIR = output_dir
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dummy_env, _ = create_flappy_bird_env_from_xml(dummy_xml, dummy_xml, inaccuracy_type)
    AGENT = Agent(dummy_env).to(DEVICE)
    AGENT.load_state_dict(torch.load(checkpoint_path, map_location=DEVICE))
    AGENT.eval()
    dummy_env.close()

# === Worker function
def evaluate_worker(paths):
    initial_xml, final_xml = paths
    try:
        env, max_timesteps = create_flappy_bird_env_from_xml(initial_xml, final_xml, INACC_TYPE)
        obs_np, _ = env.reset(seed=42)
        obs = torch.from_numpy(np.array(obs_np)).to(dtype=torch.float32, device=DEVICE)
        done, steps, crashes = False, 0, 0
        episode_data = []

        while not done and steps < max_timesteps:
            with torch.no_grad():
                action = AGENT.get_action(obs)
                action_index = int(action)
            next_obs, reward, terminated, truncated, info = env.step(action_index)
            crashed = info.get("game_stats", {}).get("crashed", False)
            if crashed: crashes += 1

            episode_data.append({
                "state": tuple(next_obs),
                "action": action_index,
                "crash": crashed,
                "timeout": False
            })

            obs = torch.from_numpy(np.array(next_obs)).to(dtype=torch.float32, device=DEVICE)
            done = terminated or truncated
            steps += 1

        if steps >= max_timesteps and episode_data:
            episode_data[-1]["timeout"] = True
        env.close()

        # Metadata
        parts = initial_xml.split(os.sep)
        bin_, seed, env_id, task_id = parts[-5], parts[-4], parts[-3], parts[-2]
        metadata = {
            "Environment": env_id,
            "Task": task_id,
            "Seed": seed,
            "Bin": bin_,
            "InaccuracyType": INACC_TYPE,
            "Steps": steps,
            "TerminationReason": "Crashed" if crashes > 0 else "Complete",
            "BugFound": crashes > 0
        }

        rel_path = os.path.join(bin_, seed, env_id, task_id)
        os.makedirs(os.path.join(OUTPUT_DIR, rel_path), exist_ok=True)
        pkl_path = os.path.join(OUTPUT_DIR, rel_path, f"{INACC_TYPE}_data.pkl")
        with open(pkl_path, "wb") as pf:
            pickle.dump(episode_data, pf, protocol=pickle.HIGHEST_PROTOCOL)
        return metadata

    except Exception as e:
        return {"error": str(e), "path": initial_xml}

def collect_all_configs(bin_dir, selected_seeds):
    configs = []
    for seed in selected_seeds:
        seed_path = os.path.join(bin_dir, seed)
        if not os.path.isdir(seed_path):
            print(f"Warning: Seed folder '{seed}' not found in {bin_dir}")
            continue

        for root, dirs, files in os.walk(seed_path):
            if "initialState.xml" in files and "finalState.xml" in files:
                initial_path = os.path.join(root, "initialState.xml")
                final_path = os.path.join(root, "finalState.xml")
                configs.append((initial_path, final_path))
    return configs

if __name__ == "__main__":
    bin_dir = "AIProbe/Result/FlappyBird/100_Bin"
    dummy_xml = os.path.join(bin_dir, "534/Env_1/Task_1/initialState.xml")
    selected_seeds = ['534', '789', '78901', '54321', '12876', '4532', '98765', '21456', '3768', '5698', '11223', '67890', '32456', '90785', '15098', '74321', '8967', '22589', '61987', '37012']
    inaccuracy_types = ["accurate", "inaccurate_state", "inaccurate_reward", "inaccurate_state_and_reward"]
    checkpoints = {
                    "accurate": "src/Catcher_Flappy_Continuous/inaccurate_models/acc_state_acc_r.pt",
                    "inaccurate_state": "src/Catcher_Flappy_Continuous/inaccurate_models/inacc_state_acc_r.pt",
                    "inaccurate_reward": "src/Catcher_Flappy_Continuous/inaccurate_models/acc_state_inacc_r.pt",
                    "inaccurate_state_and_reward": "src/Catcher_Flappy_Continuous/inaccurate_models/inacc_state_inacc_r.pt",
                }

    for type in inaccuracy_types:
        output_dir = f"{type}/"
        checkpoint = checkpoints[type]
        inacc_type = type

        csv_path = f"summary_{type}.csv"
        all_configs = collect_all_configs(bin_dir, selected_seeds)
        print(f"Found {len(all_configs)} configs in bin {bin_dir} for type {type}")
        ctx = get_context("forkserver")


    output_dir = "inaccurate_state_and_reward/"
    checkpoint = "src/Catcher_Flappy_Continuous/inaccurate_models/inacc_state_inacc_r.pt"
    inacc_type = "inaccurate_state_and_reward"
    dummy_xml = os.path.join(bin_dir, "534/Env_1/Task_1/initialState.xml")

    csv_path = "summary_inaccurate_state_and_reward.csv"
    all_configs = collect_all_configs(bin_dir, selected_seeds)
    print(f"Found {len(all_configs)} configs in bin {bin_dir}")

    ctx = get_context("forkserver")
    with ctx.Pool(processes=16, initializer=init_worker,
                  initargs=(checkpoint, inacc_type, output_dir, dummy_xml)) as pool:

        fieldnames = ["Environment", "Task", "Seed", "Bin", "InaccuracyType",
                      "Steps", "TerminationReason", "BugFound"]
        write_header = not os.path.exists(csv_path)

        with open(csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
                f.flush()

            buffer = []
            batch_size = 50

            for result in pool.imap_unordered(evaluate_worker, all_configs, chunksize=20):
                if "error" in result:
                    print(f"Error: {result['error']} at {result['path']}")
                else:
                    buffer.append(result)

                if len(buffer) >= batch_size:
                    writer.writerows(buffer)
                    f.flush()
                    buffer = []

            # Write any remaining
            if buffer:
                writer.writerows(buffer)
                f.flush()
