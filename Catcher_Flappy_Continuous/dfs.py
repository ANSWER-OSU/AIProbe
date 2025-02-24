import numpy as np
import random
import time
import json
import multiprocessing
from collections import deque
from multiprocessing import Manager, Pool
from gym_pygame.envs.base import BaseEnv
import xml.etree.ElementTree as ET




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
    print("=== Parsed Parameters ===")
    print("Agent Parameters:", agent_params)
    print("Object Parameters:", obj_params)
    print("Environment Parameters:", env_params)


    # Create the Flappy Bird environment
    env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params)

    return env



def test_action_sequence(env, action_sequence, seed):
    """
    Simulates Flappy Bird with a given action sequence and returns survival time.
    """
    random.seed(seed)
    np.random.seed(seed)

    obs, _ = env.reset(seed=seed)
    terminated = False
    survival_time = 0

    for action in action_sequence:
        if terminated:
            break
        obs, reward, terminated, _, _ = env.step(action)
        survival_time += 1

    return survival_time, action_sequence


def breadth_first_search_parallel(env, max_depth=2000, seed=42, num_workers=4):
    """
    Runs a parallelized BFS to find the best action sequence.

    :param env: Flappy Bird environment.
    :param max_depth: Max timesteps for survival.
    :param seed: Fixed seed for reproducibility.
    :param num_workers: Number of parallel processes.
    :return: Best action sequence found.
    """
    manager = Manager()
    best_action_sequence = manager.list()
    longest_survival = manager.Value('i', 0)  # Shared variable for best survival time
    queue = manager.Queue()
    pool = Pool(processes=num_workers)  # Use multiple processes

    # ✅ Initialize BFS queue with empty sequence
    queue.put([])

    start_time = time.time()
    iterations = 0

    while not queue.empty():
        iterations += 1
        current_batch = []

        # Collect sequences for parallel execution
        while not queue.empty() and len(current_batch) < num_workers:
            current_batch.append(queue.get())

        # ✅ Run parallel simulations
        results = pool.starmap(test_action_sequence, [(env, seq, seed) for seq in current_batch])

        # ✅ Process results
        for survival_time, action_sequence in results:
            if survival_time > longest_survival.value:
                print(f"🔹 New Best: Survived {survival_time}/{max_depth} timesteps")
                longest_survival.value = survival_time
                best_action_sequence[:] = action_sequence

            # ✅ Stop early if we reach max depth
            if longest_survival.value >= max_depth:
                print(f"\n✅ Early stopping: Survived {max_depth} timesteps!")
                pool.terminate()
                pool.join()
                return list(best_action_sequence)

            # ✅ Expand new action sequences if not terminated
            if survival_time < max_depth:
                queue.put(action_sequence + [0])  # Try adding 'Do Nothing'
                queue.put(action_sequence + [1])  # Try adding 'Flap'

    elapsed_time = time.time() - start_time
    print(f"\n✅ Parallel BFS completed in {elapsed_time:.2f} seconds")
    print(f"🔹 Total Sequences Tested: {iterations}")
    print(f"✅ Best survival time: {longest_survival.value}/{max_depth} timesteps")
    print(f"\n✅ Best action sequence (truncated):\n{list(best_action_sequence)[:100]} ...\n")

    pool.close()
    pool.join()
    return list(best_action_sequence)


# ✅ Initialize Flappy Bird environment
xml_file = "/scratch/projects/AIProbe/Test_Enviroment/FlappyBird/Bin5/Result_Flappybird_7027/Env_1/Task_1/initialState.xml"
env = create_flappy_bird_env_from_xml(xml_file)

# ✅ Run Parallel BFS
best_action_sequence = breadth_first_search_parallel(env, max_depth=2000, seed=42, num_workers=4)

# ✅ Save and Test the Best Sequence
save_best_action_sequence(best_action_sequence)
test_best_sequence(env, best_action_sequence, seed=42)