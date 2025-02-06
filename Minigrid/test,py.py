import os
import xml.etree.ElementTree as ET
import pygame
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.grid import Grid
from minigrid.core.world_object import Wall, Lava, Goal, Ball
from minigrid.core.actions import Actions
from minigrid.core.mission import MissionSpace

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"


# Core Classes
class Attribute:
    def __init__(self, name, data_type, value):
        self.name = name
        self.data_type = data_type
        self.value = value


class Agent:
    def __init__(self, agent_id, position, angle):
        self.agent_id = agent_id
        self.position = position
        self.angle = angle


class Object:
    def __init__(self, object_id, obj_type, position):
        self.object_id = object_id
        self.obj_type = obj_type
        self.position = position


class Environment:
    def __init__(self, name, env_type, agents, objects, properties):
        self.name = name
        self.env_type = env_type
        self.agents = agents
        self.objects = objects
        self.properties = properties


# Custom MiniGrid Environment
class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, environment_data, **kwargs):
        self.environment_data = environment_data

        # Extract grid size from properties
        grid_size_attr = next((prop for prop in environment_data.properties if prop.name == "Grid"), None)
        if grid_size_attr is None:
            raise ValueError("Grid size attribute (Grid) is missing in environment properties.")

        grid_size = int(grid_size_attr.value)

        # Initialize mission space
        mission_space = MissionSpace(lambda: "Reach the goal while avoiding obstacles")

        super().__init__(grid_size=grid_size, mission_space=mission_space, **kwargs)

    def _gen_grid(self, width, height):
        # Create an empty grid and set boundaries
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        # Place objects in the grid
        for obj in self.environment_data.objects:
            x = int(obj.position['X'])
            y = int(obj.position['Y'])

            if obj.obj_type == "Wall":
                self.grid.set(x, y, Wall())
            elif obj.obj_type == "Lava":
                self.grid.set(x, y, Lava())
            elif obj.obj_type == "Goal":
                self.grid.set(x, y, Goal())
            elif obj.obj_type == "Ball":
                self.grid.set(x, y, Ball())

            print(f"Added Object: {obj.obj_type} at Position ({x}, {y})")

        # Set agent's initial position and direction
        agent = self.environment_data.agents[0]
        self.agent_pos = (int(agent.position['X']), int(agent.position['Y']))
        self.agent_dir = int(agent.angle)

    def render(self):
        self.render_pygame()

    def render_pygames(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width * 30, self.height * 30))
        screen.fill((255, 255, 255))

        # Draw the cells and the grid
        for y in range(self.height):
            for x in range(self.width):
                obj = self.grid.get(x, y)
                color = (200, 200, 200)  # Default color for empty cells

                if isinstance(obj, Wall):
                    color = (100, 100, 100)  # Gray for walls
                elif isinstance(obj, Lava):
                    color = (255, 0, 0)  # Red for lava
                elif isinstance(obj, Goal):
                    color = (0, 255, 0)  # Green for goals
                elif isinstance(obj, Ball):
                    color = (0, 0, 255)  # Blue for balls

                # Draw the cell
                pygame.draw.rect(screen, color, pygame.Rect(x * 32, y * 32, 32, 32))

                # Draw grid lines
                pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(x * 32, y * 32, 32, 32), 1)

        # Draw the agent
        pygame.draw.circle(screen, (255, 255, 0),
                           (self.agent_pos[0] * 32 + 16, self.agent_pos[1] * 32 + 16), 10)

        pygame.display.flip()

    def render_pygame(self):
        import pygame
        pygame.init()
        screen = pygame.display.set_mode((self.width * 30, self.height * 30))
        screen.fill((255, 255, 255))

        # Define the direction mapping
        index_map = {
            0: "south",  # 0 corresponds to East
            1: "west",  # 1 corresponds to South
            2: "north",  # 2 corresponds to West
            3: "east"  # 3 corresponds to North
        }

        # Draw the cells and the grid
        for y in range(self.height):
            for x in range(self.width):
                obj = self.grid.get(x, y)
                color = (200, 200, 200)  # Default color for empty cells

                if isinstance(obj, Wall):
                    color = (100, 100, 100)  # Gray for walls
                elif isinstance(obj, Lava):
                    color = (255, 0, 0)  # Red for lava
                elif isinstance(obj, Goal):
                    color = (0, 255, 0)  # Green for goals
                elif isinstance(obj, Ball):
                    color = (0, 0, 255)  # Blue for balls

                # Draw the cell
                pygame.draw.rect(screen, color, pygame.Rect(x * 32, y * 32, 32, 32))

                # Draw grid lines
                pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(x * 32, y * 32, 32, 32), 1)

        # Draw the agent as a triangle based on its direction
        agent_x = self.agent_pos[0] * 32
        agent_y = self.agent_pos[1] * 32

        # Determine the direction from index_map
        direction = index_map[self.agent_dir]

        # Define the triangle points based on the direction
        if direction == "south":  # Facing south
            triangle = [(agent_x + 16, agent_y + 32),  # Bottom center
                        (agent_x + 8, agent_y),  # Top-left
                        (agent_x + 24, agent_y)]  # Top-right
        elif direction == "west":  # Facing west
            triangle = [(agent_x, agent_y + 16),  # Left center
                        (agent_x + 32, agent_y + 8),  # Top-right
                        (agent_x + 32, agent_y + 24)]  # Bottom-right
        elif direction == "north":  # Facing north
            triangle = [(agent_x + 16, agent_y),  # Top center
                        (agent_x + 8, agent_y + 32),  # Bottom-left
                        (agent_x + 24, agent_y + 32)]  # Bottom-right
        elif direction == "east":  # Facing east
            triangle = [(agent_x + 32, agent_y + 16),  # Right center
                        (agent_x, agent_y + 8),  # Top-left
                        (agent_x, agent_y + 24)]  # Bottom-left

        # Draw the triangle
        pygame.draw.polygon(screen, (255, 255, 0), triangle)

        pygame.display.flip()



# Parsing Functions
def parse_attribute(attr_node):
    name = attr_node.find('Name').get('value')
    data_type = attr_node.find('DataType').get('value')
    value = attr_node.find('Value').get('value')
    return Attribute(name, data_type, value)


def parse_agent(agent_node):
    agent_id = agent_node.get('id')
    position = {}
    angle = 0

    for attr in agent_node.findall('Attribute'):
        name = attr.find('Name').get('value')
        value = int(attr.find('Value').get('value'))

        if name in ['X', 'Y']:
            position[name] = value
        elif name == 'Angle':
            angle = value

    return Agent(agent_id, position, angle)


def parse_object(obj_node):
    object_id = obj_node.get('id')
    obj_type = obj_node.get('type', "default")  # Get type directly from the attribute
    position = {}

    # Parse position attributes
    for attr in obj_node.findall('Attribute'):
        name = attr.find('Name').get('value')
        value = int(attr.find('Value').get('value'))
        position[name] = value

    print(f"Parsed Object: ID={object_id}, Type={obj_type}, Position={position}")  # Debug output
    return Object(object_id, obj_type, position)


def parse_environment(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Parse agents
    agents = [parse_agent(agent) for agent in root.find('Agents').findall('Agent')]

    # Parse objects
    objects = [parse_object(obj) for obj in root.find('Objects').findall('Object')]

    # Parse properties as a list of Attribute objects
    properties = [parse_attribute(attr) for attr in root.findall('Attribute')]

    return Environment(root.get('name'), root.get('type'), agents, objects, properties)


# Main Functionality
def main():

    xml_file = "/Users/rahil/Downloads/Task_1 2/initialState.xml"  # Update with your XML file path
    environment = parse_environment(xml_file)
    print("Parsing the environment")
    env = CustomMiniGridEnv(environment_data=environment)
    print("Parsed the environment")
    print("reset the environment")

    env.reset()
    print("render the environment")
    env.render()
    print("saving the environment")
    # Save a screenshot
    pygame.image.save(pygame.display.get_surface(), "screenshotInital.png")
    print("Saved the environment")

    env.close()


if __name__ == "__main__":
    main()