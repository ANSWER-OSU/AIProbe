import numpy as np
from models.load_model import read_onnx

# Define ACAS agent (Ownship)
class ACASagent:
    def __init__(self, x, y, theta, acas_speed):
        self.x = x  # Initial X position
        self.y = y  # Initial Y position
        self.theta = theta  # Initial heading angle
        self.speed = acas_speed
        self.interval = 0.1  # Time step interval

        # Load ONNX models for different actions
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

        # Normalize theta to keep within -π to π
        self.theta = (self.theta + np.pi) % (2 * np.pi) - np.pi

        # Update X and Y positions
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self, inputs):
        """Select an action based on model predictions."""
        inputs = np.array(inputs, dtype=np.float32)  # Convert inputs to numpy array
        model_list = [self.model_1, self.model_2, self.model_3, self.model_4, self.model_5]
        model = model_list[self.prev_action]  # Select model based on previous action

        action, active = model(inputs)
        self.current_active = [action.detach().numpy(), active.detach().numpy()]
        self.prev_action = np.argmin(action.detach().numpy())  # Choose the action with the smallest value
        return self.prev_action


# Define Intruder agent
class Autoagent:
    def __init__(self, x, y, theta, speed=200):
        self.x = x  # Initial X position
        self.y = y  # Initial Y position
        self.theta = theta  # Initial heading angle
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

        # Normalize theta to keep within -π to π
        self.theta = (self.theta + np.pi) % (2 * np.pi) - np.pi

        # Update X and Y positions
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self):
        """Predefined intruder action (straight movement)."""
        return 0


# Define the Simulation Environment
class env:
    def __init__(self, ownship_x, ownship_y, ownship_theta, acas_speed,
                 intruder_x, intruder_y, intruder_theta, intruder_speed=200,
                 collision_threshold=200, boundary_limit=5000):
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
        """
        self.ownship = ACASagent(ownship_x, ownship_y, ownship_theta, acas_speed)
        self.intruder = Autoagent(intruder_x, intruder_y, intruder_theta, intruder_speed)

        self.collision_threshold = collision_threshold
        self.boundary_limit = boundary_limit
        self.terminated = False

        self.update_params()

    def update_params(self):
        """Update distance and angles between the agents."""
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

        # if abs(self.ownship.x) > self.boundary_limit or abs(self.ownship.y) > self.boundary_limit:
        #     print(f"Ownship exceeded boundary limits. Terminating.")
        #     self.terminated = True

    def step(self):
        """Simulate one time step for both agents."""
        acas_act = self.ownship.act([self.row, self.alpha, self.phi, self.ownship.speed, self.intruder.speed])
        auto_act = self.intruder.act()

        self.ownship.step(acas_act)
        self.intruder.step(auto_act)

        self.update_params()

    def step_proof(self, direction):
        """Simulate one time step with a predefined action for debugging."""
        acas_act = direction
        auto_act = self.intruder.act()

        self.ownship.step(acas_act)
        self.intruder.step(auto_act)

        self.update_params()