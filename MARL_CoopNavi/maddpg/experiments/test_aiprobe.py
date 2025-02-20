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


def mlp_model(input, num_outputs, scope, reuse=False, num_units=64):
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
    for i, agent in enumerate(world.agents):
        agent.state.p_pos = np.array(custom_init_agents[i])
    # Ensure landmarks are consistent

    # Update world agent positions

    # Update world landmark positions

    for i, landmark in enumerate(world.landmarks):
        print(f"Landmark {i}: {landmark.state.p_pos}")


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


def test(arglist):
    with U.single_threaded_session():
        env = make_env(arglist.scenario)
        obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
        trainers = get_trainers(env, arglist.num_adversaries, obs_shape_n, arglist)
        U.initialize()
        if arglist.load_dir:
            U.load_state(arglist.load_dir)
        obs_n = env.reset()
        custom_init_agents = [[0.2, 0.5], [0.0, 0.3], [0., 0.5]]
        #custom_init_landmarks = [[0.0, -0.5], [0.0, 0.5], [-0.5, -0.5]]
        # After creating the environment, set the desired initial positions
        for i, agent in enumerate(env.world.agents):
            agent.state.p_pos = np.array(custom_init_agents[i])


        # for i, landmark in enumerate(env.world.landmarks):
        #     landmark.state.p_pos = np.array(custom_init_landmarks[i])

        for agent in env.world.agents:
            agent.state.p_vel = np.zeros_like(agent.state.p_vel)


        for i, agent in enumerate(env.world.agents):
            print(f"Agent {i} initial position: {agent.state.p_pos}")


        trajectories = [[] for _ in range(env.n)]
        print("Initial Landmark Positions:")
        for i, landmark in enumerate(env.world.landmarks):
            print(f"Landmark {i}: {landmark.state.p_pos}")



        targets = [[[landmark.state.p_pos[0], landmark.state.p_pos[1]] for landmark in env.world.landmarks] for _ in
                   range(arglist.max_episode_len)]

        for _ in range(arglist.max_episode_len):
            for i, obs in enumerate(obs_n):
                #print(obs)
                trajectories[i].append(obs[:2])
            action_n = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]

            total_collisions = 0  # Initialize collision counter
            obs_n, _, done_n, _ = env.step(action_n)

            for i, agent in enumerate(env.world.agents):
                for j, agent_other in enumerate(env.world.agents):

                    if i == j:
                        continue
                    delta_pos = agent.state.p_pos - agent_other.state.p_pos

                    dist = np.sqrt(np.sum(np.square(delta_pos)))
                    dist_min = (agent.size + agent_other.size)
                    if dist < dist_min:
                        total_collisions += 1
                        print(f"Collision detected: Agent {agent.name} with Landmark {landmark.name}")
            #env.render()

            if all(done_n):
                print("dONE")
                input("close")
                break

        #visualize_trajectory(trajectories, targets)


if __name__ == '__main__':
    arglist = parse_args()
    test(arglist)
