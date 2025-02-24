import os
import argparse
import numpy as np
import tensorflow as tf
import time
import pickle
import matplotlib.pyplot as plt
from datetime import datetime
import maddpg.common.tf_util as U
from maddpg.trainer.maddpg import MADDPGAgentTester
import tensorflow.contrib.layers as layers

from multiagent.environment import MultiAgentEnv
import multiagent.scenarios as scenarios
import xml.etree.ElementTree as ET
import csv
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

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

        # Parse Objects
        for obj in root.findall(".//Object"):
            obj_id = obj.get("id")
            obj_type = obj.get("type")
            obj_data = {"id": obj_id, "type": obj_type}

            for attr in obj.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                obj_data[name] = value

            self.objects[obj_id] = obj_data

    def get_agent(self, agent_id):
        """Retrieve a specific agent's attributes."""
        return self.agents.get(agent_id, None)

    def get_object(self, obj_id):
        """Retrieve a specific object's attributes."""
        return self.objects.get(obj_id, None)

    def get_environment_attributes(self):
        """Retrieve environment-level attributes."""
        return self.attributes


def find_xml_files(base_folder):
    """
    Recursively find all 'finalState.xml' files inside nested subdirectories.
    Returns a list of (xml_file_path, env_folder, task_folder, seed_number, bin_number).
    """
    xml_files = []

    for root, dirs, files in os.walk(base_folder):  # Walk through all directories
        if "finalState.xml" in files:
            xml_file_path = os.path.join(root, "finalState.xml")

            # Extract folder names dynamically
            parts = root.split(os.sep)

            # Extract environment and task folder names correctly
            env_folder = "Unknown_Env"
            task_folder = "Unknown_Task"

            # Locate "Env_X" and "Task_Y" dynamically
            for part in parts:
                if part.startswith("Env_"):
                    env_folder = part
                if part.startswith("Task_"):
                    task_folder = part

            # Extract seed number and bin number
            seed_number = "Unknown"
            bin_number = "Unknown"

            for part in parts:
                cleaned_part = part.replace(" ", "")  # Remove extra spaces
                if cleaned_part.startswith("Result_ACAS_Xu"):
                    seed_parts = cleaned_part.split("_")

                    # Extract the last numeric value as seed number
                    if seed_parts[-1].isdigit():
                        seed_number = seed_parts[-1]

                    # Extract bin number and format it (removing 'bin')
                    for segment in seed_parts:
                        if "bin" in segment:
                            bin_number = segment.replace("bin", "")  # Convert '10bin' -> '10'

            xml_files.append((xml_file_path, env_folder, task_folder, seed_number, bin_number))

    return xml_files



def parse_args():
    parser = argparse.ArgumentParser("RL experiment with custom initial position")
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
    parser.add_argument("--load-dir", type=str, default="", help="Model load directory")
    return parser.parse_args()


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


def get_trainers(env, num_adversaries, obs_shape_n, arglist):
    trainers = []
    model = mlp_model
    trainer = MADDPGAgentTester
    for i in range(env.n):
        trainers.append(trainer("agent_%d" % i, model, obs_shape_n, env.action_space, i, arglist,
                                local_q_func=(arglist.good_policy == 'ddpg')))
    return trainers


def visualize_trajectory(trajectories, targets):
    plt.figure()
    for step, (agent_positions, target_positions) in enumerate(zip(zip(*trajectories), targets)):
        plt.clf()
        for agent_pos in agent_positions:
            plt.scatter(agent_pos[0], agent_pos[1], marker='o', label=f'Agent at step {step}')
        for target_pos in target_positions:
            plt.scatter(target_pos[0], target_pos[1], marker='x', color='red', label='Landmark')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.title(f'Agent and Landmark Positions at Step {step}')
        plt.legend()
        plt.pause(0.1)
    plt.show()


# def test(arglist):
#     with U.single_threaded_session():
#         env = make_env(arglist.scenario)
#         obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
#         trainers = get_trainers(env, arglist.num_adversaries, obs_shape_n, arglist)
#         U.initialize()
#         if arglist.load_dir:
#             U.load_state(arglist.load_dir)
#         obs_n = env.reset()
#         custom_init_agents = [[0.2, 0.5], [0.0, 0.3], [0., 0.5]]
#         #custom_init_landmarks = [[0.0, -0.5], [0.0, 0.5], [-0.5, -0.5]]
#         # After creating the environment, set the desired initial positions
#         for i, agent in enumerate(env.world.agents):
#             agent.state.p_pos = np.array(custom_init_agents[i])


#         # for i, landmark in enumerate(env.world.landmarks):
#         #     landmark.state.p_pos = np.array(custom_init_landmarks[i])

#         for agent in env.world.agents:
#             agent.state.p_vel = np.zeros_like(agent.state.p_vel)


#         for i, agent in enumerate(env.world.agents):
#             print(f"Agent {i} initial position: {agent.state.p_pos}")


#         trajectories = [[] for _ in range(env.n)]
#         print("Initial Landmark Positions:")
#         for i, landmark in enumerate(env.world.landmarks):
#             print(f"Landmark {i}: {landmark.state.p_pos}")



#         targets = [[[landmark.state.p_pos[0], landmark.state.p_pos[1]] for landmark in env.world.landmarks] for _ in
#                    range(arglist.max_episode_len)]

#         for _ in range(arglist.max_episode_len):
#             for i, obs in enumerate(obs_n):
#                 #print(obs)
#                 trajectories[i].append(obs[:2])
#             action_n = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]

#             total_collisions = 0  # Initialize collision counter
#             obs_n, _, done_n, _ = env.step(action_n)

#             for i, agent in enumerate(env.world.agents):
#                 for j, agent_other in enumerate(env.world.agents):

#                     if i == j:
#                         continue
#                     delta_pos = agent.state.p_pos - agent_other.state.p_pos

#                     dist = np.sqrt(np.sum(np.square(delta_pos)))
#                     dist_min = (agent.size + agent_other.size)
#                     if dist < dist_min:
#                         total_collisions += 1
#                         print(f"Collision detected: Agent {agent.name} with Landmark {landmark.name}")
#             #env.render()

#             if all(done_n):
#                 print("dONE")
#                 input("close")
#                 break

#         #visualize_trajectory(trajectories, targets)


def run_test_for_file(xml_file, arglist, results_list):
    print(f"Processing: {xml_file}")
    
    env = Environment(xml_file)
    custom_init_agents = []
    for agent_id, agent_data in env.agents.items():
        if 'X' in agent_data and 'Y' in agent_data:
            custom_init_agents.append([agent_data['X'], agent_data['Y']])
        else:
            print(f"Agent {agent_id} does not have valid 'X' and 'Y' attributes")

    print(f"Time Step: {arglist}")

    env_attributes = env.get_environment_attributes()
    if 'Timestep_Count' in env_attributes:
        arglist.max_episode_len = env_attributes['Timestep_Count']

    print(f"Agent initial positions: {custom_init_agents}")

    # Run the test in an isolated session
    collisions, steps = test(arglist, custom_init_agents)

    # Parse XML path into environment, task, seed, and bin
    env_folder, task_folder, seed_number, bin_number = parse_xml_path(xml_file)

    # Append results
    results_list.append({
        'Environment': env_folder,
        'Task': task_folder,
        'Seed': seed_number,
        'Bin': bin_number,
        'Test Cases': steps,
        'Collisions': collisions
    })

    # Explicitly reset the TensorFlow graph and close the session
    tf.compat.v1.reset_default_graph()
    print(f"Finished processing {xml_file}, session closed.")

def test(arglist, custom_init_agents):
    total_collisions = 0
    steps = 0

    with U.single_threaded_session():
        env = make_env(arglist.scenario)

        obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
        trainers = get_trainers(env, arglist.num_adversaries, obs_shape_n, arglist)
        U.initialize()
        if arglist.load_dir:
            U.load_state(arglist.load_dir)

        obs_n = env.reset()

        # Update initial positions of agents based on the custom_init_agents array
        for i, agent in enumerate(env.world.agents):
            if i < len(custom_init_agents):
                agent.state.p_pos = np.array(custom_init_agents[i])

        trajectories = [[] for _ in range(env.n)]

        print("Starting test simulation...")

        for step in range(arglist.max_episode_len):
            steps += 1
            for i, obs in enumerate(obs_n):
                trajectories[i].append(obs[:2])

            action_n = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]
            obs_n, _, done_n, _ = env.step(action_n)
            


            # Count collisions
            step_collisions = 0
            for i, agent in enumerate(env.world.agents):
                for j, agent_other in enumerate(env.world.agents):
                    if i == j:
                        continue
                    delta_pos = agent.state.p_pos - agent_other.state.p_pos
                    dist = np.sqrt(np.sum(np.square(delta_pos)))
                    dist_min = (agent.size + agent_other.size)
                    if dist < dist_min:
                        step_collisions += 1
                        total_collisions += 1
                        break
            
            # Print collision count for the current step
            #print(f"Step {step+1}: {step_collisions} new collisions, Total Collisions: {total_collisions}")

            if all(done_n):
                break
            break
        

    
    
    print(f"Test completed. Total collisions: {total_collisions} in {steps} steps.")
    return total_collisions, steps

# def save_results_to_csv(results, output_file):
#     keys = results[0].keys() if results else []
#     with open(output_file, 'w', newline='') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=keys)
#         writer.writeheader()
        #writer.writerows(results)

def save_results_to_csv(results, output_file):
    """Appends test results to a CSV file after each run."""
    file_exists = os.path.isfile(output_file)

    with open(output_file, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=results[0].keys())

        if not file_exists:
            writer.writeheader()  # Write header only if file is newly created

        writer.writerows(results)  # Append results to CSV

def parse_xml_path(xml_file_path):
    """
    Extracts environment, task, seed number, and bin number from the given XML file path.
    """
    # Split the path into components
    path_parts = xml_file_path.split(os.sep)

    # Example logic to extract environment and task:
    # Assuming the path contains parts like "Env_X" and "Task_Y"
    env_folder = next((part for part in path_parts if part.startswith("Env_")), "Unknown_Env")
    task_folder = next((part for part in path_parts if part.startswith("Task_")), "Unknown_Task")

    # Example logic to extract seed and bin numbers:
    # Assuming the file structure is something like: .../bin<number>/Result_ACAS_Xu_<seed>.xml
    seed_number = "Unknown"
    bin_number = "Unknown"
    for part in path_parts:
        if part.startswith("bin"):
            bin_number = part[3:]  # Extract the number after "bin"
        if part.startswith("Result_ACAS_Xu_"):
            seed_parts = part.split("_")
            if seed_parts[-1].isdigit():
                seed_number = seed_parts[-1]

    return env_folder, task_folder, seed_number, bin_number

results_list = []
base_folder = "/scratch/projects/AIProbe/MARL_CoopNavi/Result_MARL_Coop_Navi_5bin_534"

# Step 1: Find all XML files
xml_files = find_xml_files(base_folder)

# Print the number of XML files found
print(f"Number of XML files found: {len(xml_files)}")

# Step 2: Parse command-line arguments
arglist = parse_args()
print(f"Parsed arguments: {arglist}")
output_csv = "results.csv"
# Step 3: Sequentially process each XML file
results_list = []
for xml_file in xml_files:
    run_test_for_file(xml_file[0], arglist, results_list)

    save_results_to_csv(results_list, output_csv)
    
    # Clear results_list to avoid duplicate entries
    results_list.clear()

# Step 4: Save all results to a CSV file

#save_results_to_csv(results_list, output_csv)

print(f"Results saved to {output_csv}")



