import numpy as np
from models.load_model import read_onnx

# Define ACAS agent (ownship)
class ACASagent:
    def __init__(self, acas_speed):
        self.x = 0  # Starting position
        self.y = 0
        self.theta = np.pi / 2  # Initial heading (facing up)
        self.speed = acas_speed
        self.interval = 0.1  # Time step for movement

        # Load ONNX models for actions
        self.model_1 = read_onnx(1, 2)
        self.model_2 = read_onnx(2, 2)
        self.model_3 = read_onnx(3, 2)
        self.model_4 = read_onnx(4, 2)
        self.model_5 = read_onnx(5, 2)
        self.prev_action = 0  # Track the previous action
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

        # Normalize theta
        while self.theta > np.pi:
            self.theta -= np.pi * 2
        while self.theta < -np.pi:
            self.theta += np.pi * 2

        # Update position
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self, inputs):
        """Select an action based on model predictions."""
        inputs = np.array(inputs, dtype=np.float32)  # Convert inputs to tensor
        if self.prev_action == 0:
            model = self.model_1
            model_name = "ACASXU_run2a_1_2_batch_2000.onnx"
        elif self.prev_action == 1:
            model = self.model_2
            model_name = "ACASXU_run2a_2_2_batch_2000.onnx"
        elif self.prev_action == 2:
            model = self.model_3
            model_name = "ACASXU_run2a_3_2_batch_2000.onnx"
        elif self.prev_action == 3:
            model = self.model_4
            model_name = "ACASXU_run2a_4_2_batch_2000.onnx"
        elif self.prev_action == 4:
            model = self.model_5
            model_name = "ACASXU_run2a_5_2_batch_2000.onnx"


        print(f"Running model: {model_name}")
        action, active = model(inputs)
        self.current_active = [action.detach().numpy(), active.detach().numpy()]
        #self.prev_action = np.argmin(action)  # Choose the action with the smallest value
        self.prev_action = np.argmin(action.detach().numpy())
        return self.prev_action

    def act_proof(self, direction):
        """For debugging, use a predefined action."""
        return direction


# Define Intruder agent
class Autoagent:
    def __init__(self, x, y, auto_theta, speed=200):
        self.x = x
        self.y = y
        self.theta = auto_theta
        self.speed = speed
        self.interval = 0.1  # Time step

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

        # Normalize theta
        while self.theta > np.pi:
            self.theta -= np.pi * 2
        while self.theta < -np.pi:
            self.theta += np.pi * 2

        # Update position
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self):
        """Predefined intruder action."""
        return 0  # Move straight


# Define the Environment class
class env:
    def __init__(self, acas_speed, x2, y2, auto_theta,collision_threshold=200, boundary_limit=5000):
        self.ownship = ACASagent(acas_speed)
        self.intruder = Autoagent(x2, y2, auto_theta)

       
        self.collision_threshold = collision_threshold  # Minimum distance for collision
        self.boundary_limit = boundary_limit  # Maximum position before termination
        self.terminated = False  # Track termination state

        # Initialize environment variables
        self.update_params()

    def update_params(self):
        """Update distance and angles between the agents."""
        self.row = np.linalg.norm([self.ownship.x - self.intruder.x, self.ownship.y - self.intruder.y])

        # Calculate the relative angle (alpha)
        if self.row != 0:
            self.alpha = np.arcsin((self.intruder.y - self.ownship.y) / self.row)
            if self.intruder.x - self.ownship.x > 0:
                self.alpha -= self.ownship.theta
            else:
                self.alpha = np.pi - self.alpha - self.ownship.theta

            while self.alpha > np.pi:
                self.alpha -= np.pi * 2
            while self.alpha < -np.pi:
                self.alpha += np.pi * 2

        # Calculate the relative heading (phi)
        self.phi = self.intruder.theta - self.ownship.theta
        while self.phi > np.pi:
            self.phi -= np.pi * 2
        while self.phi < -np.pi:
            self.phi += np.pi * 2

        # Check termination conditions
        self.check_termination()

    def check_termination(self):
        """Check if the simulation should terminate based on various conditions."""
        # Check collision
        if self.row < self.collision_threshold:
            print(f"Collision detected at Distance: {self.row:.2f}")
            self.terminated = True

        # Check step limit
        # if self.step_count >= self.max_steps:
        #     print(f"Simulation reached max steps ({self.max_steps}). Terminating.")
        #     self.terminated = True

        # Check boundary limit
        if abs(self.ownship.x) > self.boundary_limit or abs(self.ownship.y) > self.boundary_limit:
            print(f"Ownship exceeded boundary at . Terminating.")
            self.terminated = True


    def step(self):
        """Simulate one time step for both agents."""
        acas_act = self.ownship.act([self.row, self.alpha, self.phi, self.ownship.speed, self.intruder.speed])
        auto_act = self.intruder.act()

        # Step both agents
        self.ownship.step(acas_act)
        self.intruder.step(auto_act)

        # Update environment parameters
        self.update_params()

    def step_proof(self, direction):
        """Simulate one time step with a predefined action for debugging."""
        acas_act = self.ownship.act_proof(direction)
        auto_act = self.intruder.act()

        # Step both agents
        self.ownship.step(acas_act)
        self.intruder.step(auto_act)

        # Update environment parameters
        self.update_params()