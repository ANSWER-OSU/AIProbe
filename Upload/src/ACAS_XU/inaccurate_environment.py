import torch
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from environment import env as SimulateEnv
from stable_baselines3.common.vec_env import DummyVecEnv

import torch.backends.cudnn as cudnn
torch.cuda.empty_cache()
cudnn.benchmark = True
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class CustomACASEnv(gym.Env):
    def __init__(self, setting, acas_speed=600, x2=100, y2=100, auto_theta=0, intruder_x=0, intruder_y=0, intruder_theta=0, intruder_speed=300):
        super(CustomACASEnv, self).__init__()
        self.sim_env = SimulateEnv(ownship_x = x2, ownship_y=y2, ownship_theta=auto_theta, acas_speed = acas_speed,
                 intruder_x=intruder_x, intruder_y=intruder_y, intruder_theta=intruder_theta, intruder_speed=intruder_speed, setting=setting)
        self.setting = setting
        self.action_space = gym.spaces.Discrete(5)
        if setting == "incomplete_state_rep" or setting=="incomplete_state_and_reward":
            self.observation_space = gym.spaces.Box(low=-1e6, high=1e6, shape=(4,), dtype=np.float32)
        else:
            self.observation_space = gym.spaces.Box(low=-1e6, high=1e6, shape=(5,), dtype=np.float32)

    def step(self, action):
        if action != 0:
            self.sim_env.ownship.step(action)
        self.sim_env.inturder.step(0)

        if self.setting == "incomplete_state_rep" or self.setting=="incomplete_state_and_reward":
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

        if self.setting == "incomplete_state_rep" or self.setting=="incomplete_state_and_reward":
            state = self.sim_env.incomplete_state()
        else:
            state = [self.sim_env.row, self.sim_env.alpha, self.sim_env.phi, self.sim_env.Vown, self.sim_env.Vint]

        return np.array(state, dtype=np.float32), {}

    def render(self, mode="human"):
        pass