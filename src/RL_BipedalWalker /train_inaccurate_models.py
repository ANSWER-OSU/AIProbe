import numpy as np
import gym
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.env_util import make_vec_env

# ---- Configuration ----
ENV_ID = "BipedalWalkerHardcore-v3"
MODEL_PATH = "src/RL_BipedalWalkerTraining/inaccurate_models/"
N_TIMESTEPS = 2000000
SEED = 42
NUM_WORKERS = 16


# ---- Modify Observation Space ----
class ModifyEnv(gym.ObservationWrapper):
    def __init__(self, env, trim_size=10):
        super().__init__(env)
        self.trim_size = trim_size
        original_shape = self.observation_space.shape
        new_shape = (original_shape[0] - self.trim_size,) if len(original_shape) == 1 else original_shape
        self.observation_space = gym.spaces.Box(
            low=self.observation_space.low[:-self.trim_size],
            high=self.observation_space.high[:-self.trim_size],
            dtype=self.observation_space.dtype
        )

    def observation(self, obs):
        return obs[:-self.trim_size]  # Remove the last 10 values corresponding to the LIDAR readings

    def reset(self):
        obs = self.env.reset()
        return self.observation(obs)


# ---- Modify Reward Function ----
class ModifyRewardWrapper(gym.RewardWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.last_observation = None

    def reward(self, reward):
        if self.last_observation is not None:
            hull_angle = self.last_observation[0]  # `state[0]` corresponds to hull angle
            reward += 5.0 * abs(hull_angle)  # Add back the penalization that was removed
        return reward

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.last_observation = obs  # Store the last observation for reward adjustment
        return obs, self.reward(reward), done, info

    def reset(self):
        obs = self.env.reset()
        self.last_observation = obs
        return obs


# ---- Train PPO Agent ----
def train_agent(env, model_save_path, timesteps=N_TIMESTEPS):
    """ Trains PPO on the given environment. """
    model = PPO("MlpPolicy", env, verbose=1, seed=SEED, tensorboard_log="./ppo_bipedalwalker/")
    model.learn(total_timesteps=timesteps)
    model.save(model_save_path)
    print(f"Model saved at {model_save_path}")


# ---- Experiment Runner ----
def run_experiment(env, model_path):
    """ Loads a trained model and runs it on the environment. """
    model = PPO.load(model_path)
    obs = env.reset()
    total_reward = 0
    done = False

    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        total_reward += reward

    print(f"Total Reward: {total_reward}")


# ---- Main Function ----
def main():
    set_random_seed(SEED)

    # ---- Training 1: Train with Modified Observation Space ----
    env = make_vec_env(lambda: ModifyEnv(gym.make(ENV_ID)), n_envs=NUM_WORKERS)
    train_agent(env, MODEL_PATH+"ppo_bipedalwalker_modified_obs")

    # # ---- Training 2: Train with Modified Reward Function ----
    env = make_vec_env(lambda: ModifyRewardWrapper(gym.make(ENV_ID)), n_envs=NUM_WORKERS)
    train_agent(env, MODEL_PATH+"ppo_bipedalwalker_modified_reward")

    # # ---- Training 3: Train with Modified Observation and Modified Reward ----
    env = make_vec_env(lambda: ModifyEnv(ModifyRewardWrapper(gym.make(ENV_ID))), n_envs=NUM_WORKERS)
    train_agent(env, MODEL_PATH+"ppo_bipedalwalker_modified_obs_modified_reward")

if __name__ == "__main__":
    main()
