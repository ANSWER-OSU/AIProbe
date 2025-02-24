import numpy as np
import random
import time
import json
import xml.etree.ElementTree as ET
from gym_pygame.envs.base import BaseEnv
import os
import gym

# Optional: Fix rendering issues on macOS
os.environ['PYGLET_SHADOW_WINDOW'] = '1'


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
        'Scale': env_param.get("Scale", 1),  # Default to 1
    }
    # Print the parameters for verification
    print("=== Parsed Parameters ===")
    print("Agent Parameters:", agent_params)
    print("Object Parameters:", obj_params)
    print("Environment Parameters:", env_params)

    # Create the Flappy Bird environment
    env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params)

    return env


def evaluate_sequence(env, action_sequence, seed=42):
    """ Evaluates how long an action sequence survives in the environment. """
    np.random.seed(seed)
    random.seed(seed)

    obs, _ = env.reset(seed=seed)
    survival_time = 0

    for action in action_sequence:
        obs, reward, terminated, _, _ = env.step(action)
        if terminated:
            break
        survival_time += 1

    return survival_time


def mutate_sequence(sequence, mutation_rate=0.1):
    """ Mutates a given action sequence by flipping actions randomly. """
    return [1 - action if random.random() < mutation_rate else action for action in sequence]


def monte_carlo_rollout(env, max_time=600, max_timesteps=2000, seed=42, mutation_rate=0.1):
    """
    Runs Monte Carlo simulations for a fixed time **sequentially**
    to find an action sequence that maximizes survival time.
    """
    best_action_sequence = [random.choice([0, 1]) for _ in range(max_timesteps)]
    longest_survival = 0

    random.seed(seed)
    np.random.seed(seed)

    start_time = time.time()
    simulation_count = 0

    while (time.time() - start_time) < max_time:
        simulation_count += 1

        # Mutate the best sequence slightly
        action_sequence = mutate_sequence(best_action_sequence, mutation_rate)

        # Evaluate the sequence
        survival_time = evaluate_sequence(env, action_sequence, seed)

        # Update the best sequence if it improves
        if survival_time > longest_survival:
            print(f"🔹 New best survival time: {survival_time}/{max_timesteps} timesteps")
            longest_survival = survival_time
            best_action_sequence = action_sequence[:]

            # Stop early if we reach the max survival goal
            if longest_survival >= max_timesteps:
                print(f"\n✅ Early stopping: Survived {max_timesteps} timesteps!")
                return best_action_sequence

    elapsed_time = time.time() - start_time
    print(f"\n✅ Monte Carlo Rollout completed in {elapsed_time:.2f} seconds")
    print(f"🔹 Total Simulations Run: {simulation_count}")
    print(f"✅ Best survival time: {longest_survival}/{max_timesteps} timesteps")

    return best_action_sequence


def save_best_action_sequence(best_action_sequence, filename="best_action_sequence.json"):
    """ Saves the best action sequence to a JSON file. """
    with open(filename, "w") as json_file:
        json.dump(best_action_sequence, json_file, indent=4)
    print(f"✅ Best action sequence saved to {filename}")


def load_best_action_sequence(filename="best_action_sequence.json"):
    """ Loads the best action sequence from a JSON file. """
    try:
        with open(filename, "r") as json_file:
            best_action_sequence = json.load(json_file)
        print(f"✅ Best action sequence loaded from {filename}")
        return best_action_sequence
    except FileNotFoundError:
        print(f"❌ Error: {filename} not found.")
        return None


def test_best_sequence(env, best_sequence, seed=42):
    """ Tests the best action sequence in the Flappy Bird environment. """
    obs, _ = env.reset(seed=seed)
    for timestep, action in enumerate(best_sequence):
        obs, reward, terminated, _, _ = env.step(action)
        env.render()
        time.sleep(0.05)
        if terminated:
            print(f"❌ Terminated early at timestep {timestep + 1}.")
            break
    env.close()


# ✅ Initialize Flappy Bird environment
xml_file = "AIProbe/Test_Enviroment/FlappyBird/Bin5/Result_Flappybird_534/Env_1/Task_1/finalState.xml"  # Change this path to your XML file
env = create_flappy_bird_env_from_xml(xml_file)

# ✅ Run Monte Carlo Rollout **sequentially**
best_action_sequence = monte_carlo_rollout(env, max_time=600, max_timesteps=2000, seed=42)

# ✅ Save and Test the Best Sequence
save_best_action_sequence(best_action_sequence)
test_best_sequence(env, best_action_sequence, seed=42)