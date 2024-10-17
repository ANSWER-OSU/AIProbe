import os
import pygame
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.grid import Grid
from minigrid.core.world_object import Wall, Lava, Goal, Ball
from minigrid.core.actions import Actions
from minigrid.core.mission import MissionSpace
from PIL import Image
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

# Custom environment based on the parsed XML data
class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, environment_data, **kwargs):
        # First, assign the environment_data to self.environment_data
        self.environment_data = environment_data

        # Extract grid size from XML file's EnvironmentalProperties (Boundary width/height)
        boundary = next(prop for prop in self.environment_data.properties if prop['name'] == 'Boundary')
        grid_width = int(boundary['attributes'][0].value)  # Width
        grid_height = int(boundary['attributes'][1].value)  # Height

        # Set self.width and self.height for the grid
        self.width = grid_width
        self.height = grid_height

        # Make sure to pass only one value for grid_size (assuming the grid is square)
        assert self.width == self.height, "Grid width and height must be the same for MiniGridEnv"

        # Initialize the mission space and grid size based on the XML data
        mission_space = MissionSpace(mission_func=lambda: "Reach the goal while avoiding obstacles")

        # Call the superclass initializer
        super().__init__(grid_size=self.width, mission_space=mission_space, **kwargs)

        self.step_count = 0

    def _gen_grid(self, width, height):
        # Create an empty grid and set boundaries
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        # Place walls, landmines, and other objects based on the parsed XML data
        for obj in self.environment_data.objects:
            self.add_object_to_grid(obj)

        # Set agent's initial position
        agent = self.environment_data.agents[0]
        x_pos = int(agent.position[0].value)
        y_pos = int(agent.position[1].value)
        self.agent_pos = (x_pos, y_pos)

        # Set agent direction (convert angle to MiniGrid's direction)
        direction = int(agent.direction[0].value)
        self.agent_dir = direction  # Using the direction index (0: East, 1: South, etc.)

    def add_object_to_grid(self, obj):
        # Extract the object's position
        x = int(obj.position[0].value)
        y = int(obj.position[1].value)

        # Add objects like walls and landmines based on the parsed XML data
        if obj.name == "Wall":
            self.grid.set(x, y, Wall())
        elif obj.name == "Lava":
            self.grid.set(x, y, Lava())
        elif obj.name == "Goal":
            self.grid.set(x, y, Goal())
        elif obj.name == "Ball":
            self.grid.set(x, y, Ball())

    def step(self, action):
        self.step_count += 1

        # Update the agent's direction based on the action

        # Step through the environment and capture the results
        result = super().step(action)

        # Unpack the first four values (obs, reward, done, info) and ignore any extras
        obs, reward, done, info, *extra = result

        # Handle landmine (Lava) condition
        if isinstance(self.grid.get(*self.agent_pos), Lava):
            done = True
            reward = -1

        return obs, reward, done, info


def map_user_input_to_action(user_input):
    action_map = {
        'forward': Actions.forward,
        'left': Actions.left,
        'right': Actions.right,
        'pickup': Actions.pickup,
        'drop': Actions.drop,
        'toggle': Actions.toggle
    }
    return action_map.get(user_input, None)