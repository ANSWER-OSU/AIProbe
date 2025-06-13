import xml.etree.ElementTree as ET
from initialize_flappyBird import FlappyBirdEnv

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


def create_flappy_bird_env_from_xml(xml_file, final_xml_file, inaccuracy_type):
    """
    Creates a Flappy Bird environment using parameters parsed from the XML file.
    """
    # Parse the XML file
    agent_param, obj_param, _ = parse_flappy_bird_xml(xml_file)
    _, _, final_env_param = parse_flappy_bird_xml(final_xml_file)

    # Extract X and Y for init_pos
    x = agent_param.get("X", 100)  # Default to 100 if not found
    y = agent_param.get("Y", 100)  # Default to 100 if not found

    # Define parameters for the environment
    agent_params = {
        'init_pos': (x, y)  # Use parsed X and Y
    }
    obj_params = {
        'pipe_gap': obj_param.get("pipe_gap", 10),  # Default to 10
    }
    env_params = {
        'Timestep': final_env_param.get("Timestep_Count", 100),  # Default to 0.01
    }
    max_timesteps = int(env_params['Timestep'])
    # Create the Flappy Bird environment
    env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params, inaccuracy_type=inaccuracy_type)

    return env, max_timesteps


def create_flappy_bird_env_from_dict(state_dict):
    """
    Creates a FlappyBirdEnv instance from a state dictionary.
    """
    agent = state_dict.get("agent_params", {})
    obj = state_dict.get("obj_params", {})
    env = state_dict.get("env_params", {})
    agent_params = {
        'init_pos': (agent.get("X", 100.0), agent.get("Y", 100.0))
    }

    obj_params = {
        'pipe_gap': obj.get("pipe_gap", 10.0)
    }

    env_params = {
        'Timestep': env.get("Timestep", 100.0)
    }

    return FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params,
                         inaccuracy_type='accurate')


def set_state_from_dict(self, state_dict):
    """
    Resets the current FlappyBirdEnv using a state dictionary.
    """
    agent = state_dict.get("agent_params", {})
    obj = state_dict.get("obj_params", {})
    env = state_dict.get("env_params", {})

    self.reset(
        agent_params={'init_pos': (agent.get("X", 100.0), agent.get("Y", 100.0))},
        obj_params={'pipe_gap': obj.get("pipe_gap", 10.0)},
        env_params={'Timestep': env.get("Timestep", 100.0)}
    )


def flappy_bird_xml_to_dict(xml_file):
    """
    Converts a Flappy Bird XML file into a state dictionary.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    agent_params = {}
    for agent_node in root.find("Agents").findall("Agent"):
        for attr_node in agent_node.findall("Attribute"):
            name = attr_node.find("Name").get("value")
            value = float(attr_node.find("Value").get("value"))
            agent_params[name] = value

    obj_params = {}
    for object_node in root.find("Objects").findall("Object"):
        for attr_node in object_node.findall("Attribute"):
            name = attr_node.find("Name").get("value")
            value = float(attr_node.find("Value").get("value"))
            obj_params[name] = value

    env_params = {}
    for attr_node in root.findall("Attribute"):
        name = attr_node.find("Name").get("value")
        value = float(attr_node.find("Value").get("value"))
        env_params[name] = value

    return {
        "agent_params": agent_params,
        "obj_params": obj_params,
        "env_params": env_params
    }


def flappy_bird_env_to_dict(env, dict=None):
    """
    Converts a FlappyBirdEnv instance into a state dictionary.
    This captures agent position, pipe gap, and timestep.
    """


    (agent_x, agent_y) = env.gameOb.game.init_pos

    state_dict = {
        "agent_params": {
            "X": float(agent_x),
            "Y": float(agent_y)
        },
        "obj_params": {
            "pipe_gap": env.gameOb.game.pipe_gap # If env stores it
        },
        "env_params": {
            "Timestep": env.gameOb.game.player.game_tick  # If env stores it
        }
    }

    return state_dict
