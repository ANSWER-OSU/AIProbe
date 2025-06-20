import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import torch as th
import gym
import csv
import multiprocessing
import pickle

from gym import spaces
from stable_baselines3 import PPO, SAC, TD3, A2C
from stable_baselines3.common.utils import set_random_seed
from sb3_contrib import TQC

# ---- Configuration ----
BASE_DIR = "/scratch/projects/AIProbe-Main/Result/BIpedal/5_bin"
ENV_ID = "BipedalWalkerHardcore-v3"
NUM_EPISODES = 1
N_TIMESTEPS = 2000
SEED = 42
NUM_WORKERS = 100

# ---- Model Paths ----
MODEL_PATHS = {
    "ppo": "/scratch/projects/AIProbe-Main/AIProbe/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/ppo/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    #"tqc": "/scratch/projects/AIProbe-Main/AIProbe/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/tqc/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    #"sac": "/scratch/projects/AIProbe-Main/AIProbe/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/sac/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    #"td3": "/scratch/projects/AIProbe-Main/AIProbe/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/td3/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    #"a2c": "/scratch/projects/AIProbe-Main/AIProbe/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/a2c/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip"
}


MODEL_LOADERS = {
    "ppo": PPO,
    #"tqc": TQC,
    #"sac": SAC,
    #"td3": TD3,
    #"a2c": A2C
}

LOCK = multiprocessing.Lock()

class ModifyEnv(gym.ObservationWrapper):
    def __init__(self, env, trim_size=10, testing=False):
        super().__init__(env)
        self.trim_size = trim_size
        self.testing = testing
        original_shape = self.observation_space.shape
        new_shape = (original_shape[0] - self.trim_size,)
        self.observation_space = gym.spaces.Box(
            low=self.observation_space.low[:-self.trim_size],
            high=self.observation_space.high[:-self.trim_size],
            dtype=self.observation_space.dtype
        )

    def observation(self, obs):
        return obs[:-self.trim_size]

    def reset(self, **kwargs):
        if self.testing and "states" in kwargs:
            obs = self.env.reset(states=kwargs["states"])
        else:
            obs = self.env.reset()
        return self.observation(obs)

def parse_terrain(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    terrain_values = np.array([0])
    for obj in root.findall(".//Object[@type='Terrain']"):
        for attr in obj.findall("Attribute"):
            if attr.find("Name").attrib["value"] == "Terrain":
                terrain_str = attr.find("Value").attrib["value"].strip("[]").strip()
                if not terrain_str:
                    return terrain_values
                try:
                    terrain_values = np.array(list(map(int, terrain_str.split(","))))
                except ValueError:
                    return np.array([0])
    return terrain_values

def run_simulation(args):
    xml_file, model_type, output_csv = args
    print(f"Running: {xml_file} [{model_type}]")

    terrain = parse_terrain(xml_file)

    path_parts = xml_file.replace(BASE_DIR, "").strip("/").split("/")
    seed_id = path_parts[0] if len(path_parts) > 1 else "Unknown_Seed"
    env_id = path_parts[1] if len(path_parts) > 1 else "Unknown_Env"
    task_id = path_parts[2] if len(path_parts) > 2 else "Unknown_Task"

    set_random_seed(SEED)

    base_env = gym.make(ENV_ID)
    if "obs" in model_type:
        base_env = ModifyEnv(base_env, testing=True)

    obs_size = 14 if "obs" in model_type else 24
    observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32)
    action_space = spaces.Box(low=-1, high=1, shape=(4,), dtype=np.float32)

    model_cls = MODEL_LOADERS[model_type]
    model = model_cls.load(MODEL_PATHS[model_type], env=None, device='cpu', custom_objects={
    "observation_space": observation_space,
    "action_space": action_space
})

    for episode in range(NUM_EPISODES):
        obs = base_env.reset(states=terrain)
        total_reward = 0
        done = False
        for i in range(N_TIMESTEPS):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _ = base_env.step(action)
            total_reward += reward
            if done:
                break

        termination_reason = "Completed" if not done else "Crashed"
        bug = True if (done and reward <= -100) or (not done and total_reward < 300) else False

        with LOCK:
            with open(output_csv, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([seed_id ,env_id, task_id, total_reward, i, termination_reason, bug])

    base_env.close()

if __name__ == "__main__":
    xml_files = glob.glob(os.path.join(BASE_DIR, "**/finalState.xml"), recursive=True)
    print(f"Found {len(xml_files)} XML files.")

    #MODELS_TO_RUN = ["ppo", "tqc", "sac", "td3", "a2c"]
    MODELS_TO_RUN = ["ppo"]

    for model_type in MODELS_TO_RUN:
        print(f"\n=== Running full simulation for model: {model_type} ===")

        output_csv = os.path.join(BASE_DIR, f"testing_simulation_results_{model_type}.csv")
        with open(output_csv, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Seed", "Env", "Task", "Total Reward", "Steps", "Termination Reason", "Bug Detected"])

        args_list = [(xml, model_type, output_csv) for xml in xml_files]

        with multiprocessing.Pool(NUM_WORKERS) as pool:
            pool.map(run_simulation, args_list)

        print(f"Finished running model {model_type} — results saved to {output_csv}")
