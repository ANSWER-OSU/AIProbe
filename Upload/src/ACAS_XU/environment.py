import numpy as np
from models.load_model import read_onnx
import copy

class ACASagent:
    def __init__(self, x, y, theta, acas_speed, setting='accurate'):
        self.x = x
        self.y = y
        self.theta = theta
        self.speed = acas_speed
        self.interval = 0.1
        self.setting = setting

        if self.setting == 'accurate':
            self.model_1 = read_onnx(1, 9)
            self.model_2 = read_onnx(2, 9)
            self.model_3 = read_onnx(3, 9)
            self.model_4 = read_onnx(4, 9)
            self.model_5 = read_onnx(5, 9)
        else:
            from stable_baselines3 import PPO
            import torch
            if self.setting == 'inaccurate_reward':
                ppo_model_path = "inaccurate_models/ppo_incomplete_reward"
            elif self.setting == 'incomplete_state_rep':
                ppo_model_path = "inaccurate_models/ppo_incomplete_state_rep"
            else:
                ppo_model_path = "inaccurate_models/ppo_incomplete_state_and_reward"
            self.model = PPO.load(ppo_model_path, device="cpu", custom_objects={"clip_range": 0.1, "lr_schedule": 0.0003})
            self.model_1 = self.model_2 = self.model_3 = self.model_4 = self.model_5 = self.model

        self.prev_action = 0
        self.current_active = None

    def step(self, action):
        """Update the agent's position based on the action."""
        if action == 1:
            self.theta += (1.5 / 180) * np.pi * self.interval
        elif action == 2:
            self.theta -= (1.5 / 180) * np.pi * self.interval
        elif action == 3:
            self.theta += (3.0 / 180) * np.pi * self.interval
        elif action == 4:
            self.theta -= (3.0 / 180) * np.pi * self.interval

        # Normalize theta to keep within -π to π
        self.theta = (self.theta + np.pi) % (2 * np.pi) - np.pi

        # Update X and Y positions
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self, inputs):
        """Select an action based on model predictions."""
        inputs = np.array(inputs, dtype=np.float32)
        model_list = [self.model_1, self.model_2, self.model_3, self.model_4, self.model_5]
        model = model_list[self.prev_action]

        if self.setting == 'accurate':
            action, active = model(inputs)
            self.current_active = [action.detach().numpy(), active.detach().numpy()]
            self.prev_action = np.argmin(action.detach().numpy())
        else:
            action, _ = model.predict(inputs, deterministic=True)
            self.prev_action = action
        return self.prev_action

class Autoagent:
    def __init__(self, x, y, theta, speed=200):
        self.x = x
        self.y = y
        self.theta = theta
        self.speed = speed
        self.interval = 0.1

    def step(self, action):
        """Update the intruder's position based on action."""
        if action == 1:
            self.theta += (1.5 / 180) * np.pi * self.interval
        elif action == 2:
            self.theta -= (1.5 / 180) * np.pi * self.interval
        elif action == 3:
            self.theta += (3.0 / 180) * np.pi * self.interval
        elif action == 4:
            self.theta -= (3.0 / 180) * np.pi * self.interval

        # Normalize theta to keep within -π to π
        self.theta = (self.theta + np.pi) % (2 * np.pi) - np.pi

        # Update X and Y positions
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self):
        """Predefined intruder action (straight movement)."""
        return 0

class env:
    def __init__(self, ownship_x, ownship_y, ownship_theta, acas_speed,
                 intruder_x, intruder_y, intruder_theta, intruder_speed=200,
                 collision_threshold=200, boundary_limit=12000, setting='accurate'):
        """
        Initialize the environment with aircraft positions and properties.

        :param ownship_x: Initial X position of Ownship
        :param ownship_y: Initial Y position of Ownship
        :param ownship_theta: Initial heading angle of Ownship
        :param acas_speed: Speed of Ownship
        :param intruder_x: Initial X position of Intruder
        :param intruder_y: Initial Y position of Intruder
        :param intruder_theta: Initial heading angle of Intruder
        :param intruder_speed: Speed of Intruder
        :param collision_threshold: Minimum distance for collision detection
        :param boundary_limit: Maximum allowed position before termination
        :param setting: Environment setting ('accurate', 'inaccurate_reward', 'incomplete_state_rep', 'incomplete_state_and_reward')
        """
        self.env_setting = setting
        self.ownship = ACASagent(ownship_x, ownship_y, ownship_theta, acas_speed, setting)
        self.intruder = Autoagent(intruder_x, intruder_y, intruder_theta, intruder_speed)

        self.collision_threshold = collision_threshold
        self.boundary_limit = boundary_limit
        self.terminated = False

        self.update_params()

    def update_params(self):
        self.row = np.linalg.norm([self.ownship.x - self.intruder.x, self.ownship.y - self.intruder.y])

        if self.row != 0:
            self.alpha = np.arcsin((self.intruder.y - self.ownship.y) / self.row)
            if self.intruder.x - self.ownship.x > 0:
                self.alpha -= self.ownship.theta
            else:
                self.alpha = np.pi - self.alpha - self.ownship.theta

            self.alpha = (self.alpha + np.pi) % (2 * np.pi) - np.pi

        self.phi = (self.intruder.theta - self.ownship.theta + np.pi) % (2 * np.pi) - np.pi

        self.check_termination()

    def check_termination(self):
        """Check if the simulation should terminate due to collision or boundary limits."""
        if self.row < self.collision_threshold:
            print(f"Collision detected at Distance: {self.row:.2f}")
            self.terminated = True

    def step(self):
        """Simulate one time step for both agents."""
        if self.env_setting == "incomplete_state_and_reward" or self.env_setting=="incomplete_state_rep":
            acas_act = self.ownship.act([self.alpha, self.phi, self.ownship.speed, self.intruder.speed])
        else:
            acas_act = self.ownship.act([self.row, self.alpha, self.phi, self.ownship.speed, self.intruder.speed])
        auto_act = self.intruder.act()

        self.ownship.step(acas_act)
        self.intruder.step(auto_act)

        self.update_params()
        return (acas_act)

    def step_proof(self, direction):
        acas_act = direction
        auto_act = self.intruder.act()

        self.ownship.step(acas_act)
        self.intruder.step(auto_act)

        self.update_params()

    def normalize_state(self, x):
        y = copy.deepcopy(x)
        y = np.array(y)
        y = y - np.array([1.9791091e+04, 0.0, 0.0, 650.0, 600.0])
        y = y / np.array([60261.0, 6.28318530718, 6.28318530718, 1100.0, 1200.0])
        return y.tolist()

    def reward_func(self):
        dis_threshold = 200
        gamma = 0.99
        min_dis1 = np.inf
        reward = 0
        collide_flag = False
        states_seq = []

        for j in range(100):
            self.step()
            reward = reward * gamma + self.row / 60261.0
            states_seq.append(self.normalize_state([self.row, self.alpha, self.phi, self.ownship.speed, self.intruder.speed]))
            if self.row < dis_threshold:
                collide_flag = True
                reward -= 100

        return reward, collide_flag, states_seq

    def incomplete_reward_func(self):
        """
        Incomplete reward function with incorrect scaling of distance.
        Keeps collision penalty but distorts the importance of distance.
        """
        dis_threshold = 200
        gamma = 0.99
        reward = 0
        collide_flag = False
        states_seq = []

        for j in range(100):
            self.step()

            # Introduce distorted distance scaling
            reward = reward * gamma + self.row / 1e6

            if self.env_setting == "incomplete_state_and_reward" or self.env_setting=="incomplete_state_rep":
                states_seq.append(self.normalize_state([self.alpha, self.phi, self.ownship.speed, self.intruder.speed]))
            else:
                states_seq.append(self.normalize_state([self.row, self.alpha, self.phi, self.ownship.speed, self.intruder.speed]))

            if self.row < dis_threshold:
                collide_flag = True
                reward -= 100

        return reward, collide_flag, states_seq

    def incomplete_state(self):
        """
        Incomplete state representation: Removes 'row' but keeps everything else.
        """
        return [self.alpha, self.phi, self.Vown, self.Vint]
