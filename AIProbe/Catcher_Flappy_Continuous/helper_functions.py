import xml.etree.ElementTree as ET
from gym_pygame.envs.base import BaseEnv
import time

class FlappyBirdEnv(BaseEnv):
    def __init__(self, normalize=False, display=False, agent_params=None, obj_params=None, env_params=None, **kwargs):
        self.game_name = 'FlappyBird'
        self.init(normalize, display, agent_params, obj_params, env_params, **kwargs)

    def get_ob_normalize(cls, state):
        state_normal = cls.get_ob(state)
        return state_normal

def parse_flappy_bird_xml(xml_file):
    """
    Parses the XML file and extracts the parameters for Flappy Bird Environment.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Parse agents
    agent_params = {}
    for agent_node in root.find("Agents").findall("Agent"):
        for attr_node in agent_node.findall("Attribute"):
            name = attr_node.find("Name").get("value")
            value = float(attr_node.find("Value").get("value"))
            agent_params[name] = value

    # Parse objects
    obj_params = {}
    for object_node in root.find("Objects").findall("Object"):
        for attr_node in object_node.findall("Attribute"):
            name = attr_node.find("Name").get("value")
            value = float(attr_node.find("Value").get("value"))
            obj_params[name] = value

    # Parse environment attributes
    env_params = {}
    for attr_node in root.findall("Attribute"):
        name = attr_node.find("Name").get("value")
        value = float(attr_node.find("Value").get("value"))
        env_params[name] = value

    return agent_params, obj_params, env_params


def create_flappy_bird_env_from_xml(xml_file):
    """
    Creates a Flappy Bird environment using parameters parsed from the XML file.
    """
    # Parse the XML file
    agent_param, obj_param, env_param = parse_flappy_bird_xml(xml_file)

    # Extract X and Y for init_pos
    x = agent_param.get("X", 100)  # Default to 100 if not found
    y = agent_param.get("Y", 100)  # Default to 100 if not found

    # Define parameters for the environment
    agent_params = {
        'FLAP_POWER': agent_param.get("FLAP_POWER", 12),  # Default to 12 if not found
        'MAX_DROP_SPEED': agent_param.get("MAX_DROP_SPEED", 100),  # Default to 100
        'init_pos': (x, y)  # Use parsed X and Y
    }
    obj_params = {
        'pipe_gap': obj_param.get("pipe_gap", 10),  # Default to 10
    }
    env_params = {
        'Gravity': env_param.get("Gravity", 5),  # Default to 5
        'Scale': env_param.get("Scale", 1),  # Default to 5

    }
    # Print the parameters for verification
    # print("=== Parsed Parameters ===")
    # print("Agent Parameters:", agent_params)
    # print("Object Parameters:", obj_params)
    # print("Environment Parameters:", env_params)


    # Create the Flappy Bird environment
    env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params)

    return env
