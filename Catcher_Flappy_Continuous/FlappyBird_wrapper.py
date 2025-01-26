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
            value = int(attr_node.find("Value").get("value"))
            agent_params[name] = value

    # Parse objects
    obj_params = {}
    for object_node in root.find("Objects").findall("Object"):
        for attr_node in object_node.findall("Attribute"):
            name = attr_node.find("Name").get("value")
            value = int(attr_node.find("Value").get("value"))
            obj_params[name] = value

    # Parse environment attributes
    env_params = {}
    for attr_node in root.findall("Attribute"):
        name = attr_node.find("Name").get("value")
        value = int(attr_node.find("Value").get("value"))
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
        'speed': obj_param.get("speed", 10),  # Default to 10
        #'start_gap': obj_param.get("start_gap", 1),  # Default to 1
        'start_gap': 10,  # Default to 1
        #'pipe_gap': obj_param.get("pipe_gap", 10),  # Default to 10
        'pipe_gap': 100,
        #'offset': obj_param.get("offset", 1)  # Default to 1
        'offset':  10  # Default to 1
    }
    env_params = {
        'gravity': env_param.get("Gravity", 5),  # Default to 5
        'max_drop_speed': env_param.get("max_drop_speed", 90)  # Default to 90
    }
    # Print the parameters for verification
    print("=== Parsed Parameters ===")
    print("Agent Parameters:", agent_params)
    print("Object Parameters:", obj_params)
    print("Environment Parameters:", env_params)


    # Create the Flappy Bird environment
    env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params)

    return env


if __name__ == '__main__':
    # Example XML file path
    xml_file = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Data/Flappybird.xml"

    # Create Flappy Bird environment
    env = create_flappy_bird_env_from_xml(xml_file)
    bird_should_flap = [1,1,1,1,1,0,1]
    print('Action space:', env.action_space)
    print('Action set:', env.action_set)
    print('Observation space:', env.observation_space)
    print('Observation space high:', env.observation_space.high)
    print('Observation space low:', env.observation_space.low)
    idt = 0
    seed = 42
    obs, _ = env.reset(seed)
    while True:
        print(idt)
        #action = env.action_space.sample()
        action = bird_should_flap[idt]
        obs, reward, terminated, _, _ = env.step(action)
        start_time = time.time()
        obs, reward, terminated, _, _ = env.step(action)
        time_taken = time.time() - start_time
        env.render('human')
        idt+=1

        print(f"Observation: {obs}")
        print(f"Reward: {reward}")
        print(f"Terminated: {terminated}")
        print(f"Time Taken for Step: {time_taken:.6f} seconds")

        if terminated:
            obs, _ = env.reset()
            continue
    env.close()