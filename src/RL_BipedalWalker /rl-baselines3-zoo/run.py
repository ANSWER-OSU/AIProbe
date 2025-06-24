import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import torch as th
import gym
from stable_baselines3 import PPO , SAC , TD3 , A2C
from stable_baselines3.common.utils import set_random_seed
from utils import create_test_env
import matplotlib.pyplot as plt
import csv
import multiprocessing
from gym import spaces
import pickle
import time
from sb3_contrib import TQC
# ---- Configuration ----
BASE_DIR = "src/RL_BipedalWalker/<PATH_TO_XML_FILES>"
ENV_ID = "BipedalWalkerHardcore-v3"

import torch as th
th.set_num_threads(1)

# Paths to different models
MODEL_PATHS = {
    # Base models
    "ppo": "src/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/ppo/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    "sac": "src/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/sac/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    "tqc": "src/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/tqc/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    "a2c": "src/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/a2c/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",
    "td3": "src/RL_BipedalWalker/rl-baselines3-zoo/rl-trained-agents/td3/BipedalWalkerHardcore-v3_1/BipedalWalkerHardcore-v3.zip",

    # Inaccurate PPO models
     "modified_obs": "src/RL_BipedalWalker/BipedalInaccuratePPOModels/ppo_bipedalwalker_modified_obs.zip",
     "modified_reward": "src/RL_BipedalWalker/BipedalInaccuratePPOModels/ppo_bipedalwalker_modified_reward.zip",
     "modified_obs_reward": "src/RL_BipedalWalker/BipedalInaccuratePPOModels/ppo_bipedalwalker_modified_obs_modified_reward.zip",
}

OUTPUT_CSVS = {
   "ppo": os.path.join(BASE_DIR, "ppo_simulation_results_test_actions.csv"),
   "sac": os.path.join(BASE_DIR, "sac_simulation_results.csv"),
    "tqc": os.path.join(BASE_DIR, "tqc_simulation_results.csv"),
    "a2c": os.path.join(BASE_DIR, "a2c_simulation_results.csv"),
    "td3": os.path.join(BASE_DIR, "td3_simulation_results.csv"),
    "modified_obs": os.path.join(BASE_DIR, "simulation_results_modified_obs.csv"),
    "modified_reward": os.path.join(BASE_DIR, "simulation_results_modified_reward.csv"),
    "modified_obs_reward": os.path.join(BASE_DIR, "simulation_results_modified_obs_reward.csv"),
}

NUM_EPISODES = 1
N_TIMESTEPS = 2000
SEED = 42
NUM_WORKERS = 35


LOCK = multiprocessing.Lock()

import logging

# Setup logging
logging.basicConfig(
    filename=os.path.join(BASE_DIR, "simulation_log_ppo.txt"),
    filemode='a',  # Append to existing log
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)

logger = logging.getLogger()

# ---- Modify Observation Space ----
class ModifyEnv(gym.ObservationWrapper):
    def __init__(self, env, trim_size=10, testing=False):
        """
        Modify the observation space by removing the last `trim_size` values.
        During testing, allows resetting with a specified `states` parameter.

        Args:
        - env: The base environment.
        - trim_size (int): Number of values to remove from the observation.
        - testing (bool): Whether the environment is in testing mode.
        """
        super().__init__(env)
        self.trim_size = trim_size
        self.testing = testing  # Enables `states` parameter only for testing
        original_shape = self.observation_space.shape
        new_shape = (original_shape[0] - self.trim_size,) if len(original_shape) == 1 else original_shape
        self.observation_space = gym.spaces.Box(
            low=self.observation_space.low[:-self.trim_size],
            high=self.observation_space.high[:-self.trim_size],
            dtype=self.observation_space.dtype
        )

    def observation(self, obs):
        return obs[:-self.trim_size]  # Remove the last 10 values corresponding to the LIDAR readings

    def reset(self, **kwargs):
        """
        Reset environment. If `testing` mode is enabled, allow the `states` parameter.
        """
        if self.testing and "states" in kwargs:
            obs = self.env.reset(states=kwargs["states"])
        else:
            obs = self.env.reset()
        return self.observation(obs)


# ---- Modify Reward Function ----
class ModifyRewardWrapper(gym.RewardWrapper):
    def __init__(self, env, testing=False):
        """
        Modify the reward function to remove the penalty on hull angle.
        During testing, allows resetting with a specified `states` parameter.

        Args:
        - env: The base environment.
        - testing (bool): Whether the environment is in testing mode.
        """
        super().__init__(env)
        self.last_observation = None
        self.testing = testing  # Enables `states` parameter only for testing

    def reward(self, reward):
        if self.last_observation is not None:
            hull_angle = self.last_observation[0]  # `state[0]` corresponds to hull angle
            reward += 5.0 * abs(hull_angle)  # Add back the penalization that was removed
        return reward

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.last_observation = obs  # Store the last observation for reward adjustment
        return obs, self.reward(reward), done, info

    def reset(self, **kwargs):
        """
        Reset environment. If `testing` mode is enabled, allow the `states` parameter.
        """
        if self.testing and "states" in kwargs:
            obs = self.env.reset(states=kwargs["states"])
        else:
            obs = self.env.reset()
        self.last_observation = obs
        return obs


# ---- Function to Extract Terrain Data from XML ----
def parse_terrain(xml_file):
    """Extract terrain values from an XML file where Terrain is a top-level Attribute."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Default fallback
        terrain_values = np.array([0])
        
        # Look for top-level Attribute tags
        for attr in root.findall("Attribute"):
            name_elem = attr.find("Name")
            value_elem = attr.find("Value")
            
            if name_elem is not None and name_elem.attrib.get("value") == "Terrain":
                terrain_str = value_elem.attrib.get("value", "").strip("[]").strip()
                
                if not terrain_str:
                    print(f"Warning: Empty terrain data in {xml_file}, using default [0]")
                    return terrain_values
                
                try:
                    terrain_values = np.array(list(map(int, terrain_str.split(","))))
                    return terrain_values
                except ValueError:
                    print(f"Error parsing terrain in {xml_file}, using default [0]")
                    return np.array([0])
                
        # If no terrain attribute found
        print(f"Warning: Terrain attribute not found in {xml_file}, using default [0]")
        return terrain_values
    
    except ET.ParseError:
        print(f"Failed to parse XML: {xml_file}")
        return np.array([0])


# ---- Function to Run Simulation ----
def run_simulation(args):
    """Runs a single simulation and logs the result."""
    xml_file, model_type = args
    print(f"\nProcessing: {xml_file} for model {model_type}")
    logger.info(f"\nProcessing: {xml_file} for model {model_type}")

    # Extract terrain
    CUSTOM_TERRAIN = parse_terrain(xml_file)

    # Extract Env and Task IDs
    path_parts = xml_file.replace(BASE_DIR, "").strip("/").split("/")
    seed_id = path_parts[0] if len(path_parts) > 1 else "Unknown_seed"
    env_id = path_parts[1] if len(path_parts) > 1 else "Unknown_Env"
    task_id = path_parts[2] if len(path_parts) > 2 else "Unknown_Task"

    # ---- Setup Environment ----
    set_random_seed(SEED)
    env_kwargs = {}
    log_dir = None

    base_env = gym.make(ENV_ID)

    if model_type == "modified_obs":
        base_env = ModifyEnv(base_env, testing=True)
    elif model_type == "modified_obs_reward":
        base_env = ModifyEnv(base_env, testing=True)  # Keep observation modification
        #base_env = ModifyRewardWrapper(base_env, testing=True)

    obs_size = 14 if "obs" in model_type else 24  # If observation is modified, use 14, else 24
    observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32)
    action_space = spaces.Box(low=-1, high=1, shape=(4,), dtype=np.float32)

    model_cls_map = {
        "ppo": PPO,
        "sac": SAC,
        "tqc": TQC,
        "a2c": A2C,
        "td3": TD3
    }

    if model_type in model_cls_map:
        model_class = model_cls_map[model_type]
        model = model_class.load(MODEL_PATHS[model_type], device="cpu")
    else:
        # For modified PPO models (with modified obs or reward)
        model = PPO.load(MODEL_PATHS[model_type], env=None, device="cpu",custom_objects={
            "observation_space": observation_space,
            "action_space": action_space
        })
    for episode in range(NUM_EPISODES):
        ep_terminated = False
        crashed = False
        termination_reason = "Time Limit"
        bug_detected = False
        print(f"\nRunning episode {episode + 1} in {env_id}/{task_id} using {model_type}")

        obs = base_env.reset(states=CUSTOM_TERRAIN)

        episode_reward = 0.0

        for i in range(N_TIMESTEPS):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _ = base_env.step(action)
            episode_reward += reward

            if done:
                if reward<=-100:
                    ep_terminated = True
                    crashed = True
                else:
                    ep_terminated = True
                    crashed = False
                break

        if base_env.game_over:
            termination_reason = "Agent Fell"
            bug_detected = True
            with open("low_reward_observations.pkl", "wb") as f:
                pickle.dump(obs, f)

        elif (ep_terminated and not crashed):
            if episode_reward<300:
                termination_reason = "Low reward"
                bug_detected = True
                with open("low_reward_observations.pkl", "wb") as f:
                    pickle.dump(obs, f)
            else:
                termination_reason = "Task Completed"
                bug_detected = False

        print(f"Episode Terminated: {termination_reason} with reward {episode_reward}")

        with LOCK:
            with open(OUTPUT_CSVS[model_type], "a", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([seed_id,env_id, task_id, episode_reward, i, termination_reason, bug_detected])

    base_env.close()
    print(f"Completed: {xml_file} using {model_type}")

# ---- Get All XML Files ----
all_xmls = glob.glob(os.path.join(BASE_DIR, "**/finalState.xml"), recursive=True)
xml_files = [f for f in all_xmls if os.path.basename(os.path.dirname(f)) == "Task_1"]
print(f"Filtered to {len(xml_files)} Task_1 XML files.")
print(f"Found {len(xml_files)} XML files.")
print(xml_files[0])



# ---- Initialize CSV Files ----
for model_type, output_csv in OUTPUT_CSVS.items():
    with open(output_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Seed", "Env", "Task", "Total Reward", "Steps", "Termination Reason", "Bug Detected"])

# ---- Run Simulations in Parallel ----
if __name__ == "__main__":
    import datetime
    start_time = time.time()
    readable_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting parallel simulations at {readable_start}")

    args_list = [(xml_file, model_type) for xml_file in xml_files for model_type in MODEL_PATHS.keys()]
    with multiprocessing.Pool(NUM_WORKERS) as pool:
        pool.map(run_simulation, args_list)

    end_time = time.time()
    readable_end = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed_minutes = (end_time - start_time) / 60

    logger.info(f"All parallel simulations complete at {readable_end}")
    logger.info(f"Total time taken: {elapsed_minutes:.2f} minutes")
    logger.info(f"Results saved to: {OUTPUT_CSVS}")
    