import os
import argparse
import numpy as np
import tensorflow as tf
import csv
import multiprocessing
from datetime import datetime
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import maddpg.common.tf_util as U
from maddpg.trainer.maddpg import MADDPGAgentTester
import tensorflow.contrib.layers as layers
from multiagent.environment import MultiAgentEnv
import multiagent.scenarios as scenarios
import multiprocessing

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

class Environment:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.agents = {}
        self.objects = {}
        self.attributes = {}

        # Load and parse the XML
        self.load_environment()

    def load_environment(self):
        """Loads and parses the XML environment file."""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # Parse Environment Attributes (like Timestep_Count)
        for attr in root.findall("Attribute"):
            name = attr.find("Name").get("value")
            value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
            self.attributes[name] = value

        # Parse Agents
        for agent in root.findall(".//Agent"):
            agent_id = agent.get("id")
            agent_data = {"id": agent_id}

            for attr in agent.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                agent_data[name] = value

            self.agents[agent_id] = agent_data

    def get_environment_attributes(self):
        """Retrieve environment-level attributes."""
        return self.attributes

def mlp_model(input, num_outputs, scope, reuse=tf.AUTO_REUSE, num_units=64):
    with tf.variable_scope(scope, reuse=reuse):
        out = layers.fully_connected(input, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_outputs, activation_fn=None)
        return out


def make_env(scenario_name):
    scenario = scenarios.load(scenario_name + ".py").Scenario()
    world = scenario.make_world()

    # Set custom initial positions for agents and landmarks
    custom_init_agents = [[-0.5, 0.0], [0.5, 0.0], [0.5, 0.5]]
    #custom_init_landmarks = [[0.0, -0.5], [0.0, 0.5], [-0.5, -0.5]]

    # Update world agent positions
    # for i, agent in enumerate(world.agents):
    #     agent.state.p_pos = np.array(custom_init_agents[i])
    # Ensure landmarks are consistent

    # Update world agent positions

    # Update world landmark positions

    # for i, landmark in enumerate(world.landmarks):
    #     print(f"Landmark {i}: {landmark.state.p_pos}")


    # Create environment
    env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation, scenario.benchmark_data)
    return env


def find_xml_files(base_folder):
    """Finds all 'finalState.xml' files recursively."""
    xml_files = []
    for root, _, files in os.walk(base_folder):
        if "finalState.xml" in files:
            xml_files.append(os.path.join(root, "finalState.xml"))
    return xml_files


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser("Parallel RL experiment")
    parser.add_argument("--scenario", type=str, default="simple_spread", help="Scenario script name")
    parser.add_argument("--max-episode-len", type=int, default=20000, help="Max episode length")
    parser.add_argument("--num-adversaries", type=int, default=0, help="Number of adversaries")
    parser.add_argument("--good-policy", type=str, default="maddpg", help="Good agents' policy")
    parser.add_argument("--adv-policy", type=str, default="maddpg", help="Adversaries' policy")
    parser.add_argument("--lr", type=float, default=1e-2, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.95, help="Discount factor")
    parser.add_argument("--batch-size", type=int, default=1024, help="Batch size")
    parser.add_argument("--num-units", type=int, default=64, help="Number of MLP units")
    parser.add_argument("--save-dir", type=str, default="../checkpoints/", help="Checkpoint directory")
    return parser.parse_args()


def make_env(scenario_name):
    """Creates the multi-agent environment."""
    scenario = scenarios.load(scenario_name + ".py").Scenario()
    world = scenario.make_world()
    return MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation, scenario.benchmark_data)


def run_test_for_file_parallel(xml_file, arglist):
    """Runs the test for a single XML file in a separate process."""
    print(f"Processing: {xml_file}")

    env = Environment(xml_file)
    env_attributes = env.get_environment_attributes()

    # Adjust max episode length based on environment attributes
    if 'Timestep_Count' in env_attributes:
        arglist.max_episode_len = env_attributes['Timestep_Count']

    custom_init_agents = [[agent_data['X'], agent_data['Y']] for agent_data in env.agents.values() if 'X' in agent_data and 'Y' in agent_data]
    print(f"Agent initial positions: {custom_init_agents}")

    # Run the test in an isolated session
    collisions, steps = test(arglist, custom_init_agents)

    # Parse XML path for metadata
    env_folder, task_folder, seed_number, bin_number = parse_xml_path(xml_file)

    # Reset TensorFlow graph to prevent conflicts in multiprocessing
    tf.compat.v1.reset_default_graph()

    return {
        'Environment': env_folder,
        'Task': task_folder,
        'Seed': seed_number,
        'Bin': bin_number,
        'Test Cases': steps,
        'Collisions': collisions
    }


def test(arglist, custom_init_agents):
    """Runs the reinforcement learning test."""
    total_collisions = 0
    steps = 0

    with U.single_threaded_session():
        env = make_env(arglist.scenario)
        obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
        trainers = [MADDPGAgentTester(f"agent_{i}", mlp_model, obs_shape_n, env.action_space, i, arglist) for i in range(env.n)]
        U.initialize()

        obs_n = env.reset()
        for i, agent in enumerate(env.world.agents):
            if i < len(custom_init_agents):
                agent.state.p_pos = np.array(custom_init_agents[i])

        for step in range(arglist.max_episode_len):
            steps += 1
            action_n = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]
            obs_n, _, done_n, _ = env.step(action_n)

            # Count collisions
            for i, agent in enumerate(env.world.agents):
                for j, agent_other in enumerate(env.world.agents):
                    if i != j and np.linalg.norm(agent.state.p_pos - agent_other.state.p_pos) < (agent.size + agent_other.size):
                        total_collisions += 1

            if all(done_n):
                break
    print(f"Test completed. Total collisions: {total_collisions} in {steps} steps.")
    return total_collisions, steps


def parse_xml_path(xml_file_path):
    """Extracts metadata from the XML file path."""
    parts = xml_file_path.split(os.sep)
    env_folder = next((p for p in parts if p.startswith("Env_")), "Unknown_Env")
    task_folder = next((p for p in parts if p.startswith("Task_")), "Unknown_Task")
    seed_number = next((p.split("_")[-1] for p in parts if p.startswith("Result_ACAS_Xu_") and p.split("_")[-1].isdigit()), "Unknown")
    bin_number = next((p[3:] for p in parts if p.startswith("bin")), "5")
    return env_folder, task_folder, seed_number, bin_number


def save_results_to_csv(results, output_file):
    """Saves test results to a CSV file."""
    keys = results[0].keys() if results else []
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)


def parallel_processing(xml_files, arglist, num_workers=4):
    """Runs tests in parallel using multiprocessing."""
    print(f"Starting parallel processing with {num_workers} workers...")
    
    with multiprocessing.Pool(num_workers) as pool:
        results = pool.starmap(run_test_for_file_parallel, [(xml_file, arglist) for xml_file in xml_files])

    return results


if __name__ == "__main__":
    base_folder = "/scratch/projects/AIProbe/MARL_CoopNavi/er/Result_MARL_Coop_Navi_5bin_7027"

    xml_files = find_xml_files(base_folder)
    print(f"Number of XML files found: {len(xml_files)}")

    arglist = parse_args()
    num_workers = min(multiprocessing.cpu_count(), len(xml_files))
    #num_workers = min(, len(xml_files))  # Use up to 8 workers or available files

    results_list = parallel_processing(xml_files, arglist, num_workers)
    save_results_to_csv(results_list, "resultsparalle.csv")

    print("Results saved to results.csv")