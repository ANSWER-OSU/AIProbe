import torch
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import torch.backends.cudnn as cudnn
torch.cuda.empty_cache()
cudnn.benchmark = True  # Enables faster inference
from environment import env as SimulateEnv

# Set device to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

class CustomACASEnv(gym.Env):
    def __init__(self, setting, acas_speed=600, x2=100, y2=100, auto_theta=0, intruder_x=0, intruder_y=0, intruder_theta=0, intruder_speed=300):
        super(CustomACASEnv, self).__init__()
        self.sim_env = SimulateEnv(ownship_x = x2, ownship_y=y2, ownship_theta=auto_theta, acas_speed = acas_speed,
                 intruder_x=intruder_x, intruder_y=intruder_y, intruder_theta=intruder_theta, intruder_speed=intruder_speed, setting=setting)
        self.setting = setting
        self.action_space = gym.spaces.Discrete(5)
        print(setting, "----------------------")
        if setting == "incomplete_state_rep" or setting=="incomplete_state_and_reward":
            self.observation_space = gym.spaces.Box(low=-1e6, high=1e6, shape=(4,), dtype=np.float32)
        else:
            self.observation_space = gym.spaces.Box(low=-1e6, high=1e6, shape=(5,), dtype=np.float32)

    def step(self, action):
        if action != 0:
            self.sim_env.ownship.step(action)
        self.sim_env.inturder.step(0)

        if self.setting == "incomplete_state_rep" or setting=="incomplete_state_and_reward":
            state = self.sim_env.incomplete_state()
        else:
            state = [self.sim_env.row, self.sim_env.alpha, self.sim_env.phi, self.sim_env.Vown, self.sim_env.Vint]

        if self.setting == "incomplete_reward":
            reward, collide_flag, _ = self.sim_env.incomplete_reward_func()
        elif self.setting == "incomplete_state_and_reward":
            reward, collide_flag, _ = self.sim_env.incomplete_reward_func()
        else:
            reward, collide_flag, _ = self.sim_env.reward_func()

        done = collide_flag
        truncated = False

        return np.array(state, dtype=np.float32), reward, done, truncated, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.sim_env = SimulateEnv(600, 100, 100, 0)

        if self.setting == "incomplete_state_rep" or setting=="incomplete_state_and_reward":
            state = self.sim_env.incomplete_state()
        else:
            state = [self.sim_env.row, self.sim_env.alpha, self.sim_env.phi, self.sim_env.Vown, self.sim_env.Vint]

        return np.array(state, dtype=np.float32), {}

    def render(self, mode="human"):
        pass

# setting = "incomplete_state"

# if setting == 'inaccurate_reward':
#     ppo_model_path = "inaccuracy_models/ppo_incomplete_reward.zip"
# elif setting == 'inaccurate_state':
#     ppo_model_path = "inaccuracy_models/ppo_incomplete_state_rep.zip"
# else:
#     ppo_model_path = "inaccuracy_models/ppo_incomplete_state_and_reward.zip"

# '''
# LOADS THE MODEL BASED ON THE SETTING CHOSEN
# '''

# print(f"Loading trained PPO model from {ppo_model_path}")
# model = PPO.load(ppo_model_path, device=device)

# '''
# BELOW IS HOW AN ENVIRONMENT IS CREATED FOR EVALUATION
# '''

# print("Creating evaluation environment...")
# eval_env = DummyVecEnv([lambda: CustomACASEnv(setting=setting)])

# '''
# COMMENT OUT BELOW WHEN RUNNING THE FUZZER CODE. THIS IS USED ONLY TO EVALUATE THE MODEL TRAINED
# '''

# num_episodes = 10
# total_rewards = []

# for ep in range(num_episodes):
#     obs = eval_env.reset()
#     done = False
#     episode_reward = 0
#     step_count = 0

#     while not done:
#         action, _ = model.predict(obs, deterministic=True)
#         obs, reward, done, truncated, info = eval_env.step(action)
#         episode_reward += reward
#         step_count += 1

#     total_rewards.append(episode_reward)
#     print(f"Episode {ep+1}: Total Reward = {episode_reward}, Steps Taken = {step_count}")

# # Compute average reward
# average_reward = np.mean(total_rewards)
# print(f"Average Reward over {num_episodes} episodes: {average_reward}")
