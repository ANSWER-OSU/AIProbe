import os
import sys
sys.path.append(os.path.abspath("/AIProbe/MARL_CoopNavi/multiagent_particle_envs"))
import argparse
import numpy as np
import tensorflow as tf
import csv
import multiprocessing
import xml.etree.ElementTree as ET
import maddpg.common.tf_util as U
from maddpg.trainer.maddpg import MADDPGAgentTester
import tensorflow.contrib.layers as layers
from multiagent.environment import MultiAgentEnv
import re
import pickle
import shutil
import time
from itertools import islice
from gym import spaces

sys.path.insert(0, "/AIProbe/MARL_CoopNavi/multiagent_particle_envs")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from multiagent.scenarios import load

lock = None

def parse_args():
    parser = argparse.ArgumentParser("Reinforcement Learning experiments for multiagent environments")
    parser.add_argument("--scenario", type=str, default="simple_spread")
    parser.add_argument("--max-episode-len", type=int, default=25)
    parser.add_argument("--num-episodes", type=int, default=60000)
    parser.add_argument("--num-adversaries", type=int, default=0)
    parser.add_argument("--good-policy", type=str, default="maddpg")
    parser.add_argument("--adv-policy", type=str, default="maddpg")
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--gamma", type=float, default=0.95)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--num-units", type=int, default=64)
    parser.add_argument("--exp-name", type=str, default=None)
    parser.add_argument("--save-dir", type=str, default="/tmp/policy/")
    parser.add_argument("--save-rate", type=int, default=1000)
    parser.add_argument("--load-dir", type=str, default="")
    parser.add_argument("--restore", action="store_true", default=False)
    parser.add_argument("--display", action="store_true", default=False)
    parser.add_argument("--benchmark", action="store_true", default=False)
    parser.add_argument("--benchmark-iters", type=int, default=100)
    parser.add_argument("--benchmark-dir", type=str, default="./benchmark_files/")
    parser.add_argument("--plots-dir", type=str, default="./learning_curves/")
    return parser.parse_args()

def chunked_iterable(iterable, size):
    it = iter(iterable)
    return iter(lambda: list(islice(it, size)), [])

def init_worker():
    global lock
    lock = multiprocessing.Lock()


def update_full_environment_xml(final_xml_path, env, current_step):
    """Update all values in the final XML using the current state of the environment."""
    tree = ET.parse(final_xml_path)
    root = tree.getroot()
    world = env.world

    # Update agents
    for i, agent in enumerate(world.agents):
        agent_id = str(i + 1)  # XML IDs start at 1
        agent_elem = root.find(f".//Agent[@id='{agent_id}']")
        if agent_elem is None:
            continue

        for attr in agent_elem.findall("Attribute"):
            name = attr.find("Name").get("value")
            value_elem = attr.find("Value")
            if value_elem is None:
                continue

            # Absolute positions
            if name == "X":
                value_elem.set("value", str(agent.state.p_pos[0]))
            elif name == "Y":
                value_elem.set("value", str(agent.state.p_pos[1]))

            # Velocities
            elif name == "Vel_X":
                value_elem.set("value", str(agent.state.p_vel[0]))
            elif name == "Vel_Y":
                value_elem.set("value", str(agent.state.p_vel[1]))

            # Relative to landmarks
            elif "Landmark" in name and "_DX" in name:
                landmark_id = int(name.split("_")[1])
                if landmark_id < len(world.landmarks):
                    dx = world.landmarks[landmark_id].state.p_pos[0] - agent.state.p_pos[0]
                    value_elem.set("value", str(dx))
            elif "Landmark" in name and "_DY" in name:
                landmark_id = int(name.split("_")[1])
                if landmark_id < len(world.landmarks):
                    dy = world.landmarks[landmark_id].state.p_pos[1] - agent.state.p_pos[1]
                    value_elem.set("value", str(dy))

            # Relative to other agents
            elif "Agent" in name and "_DX" in name:
                other_id = int(name.split("_")[1])
                if other_id < len(world.agents):
                    dx = world.agents[other_id].state.p_pos[0] - agent.state.p_pos[0]
                    value_elem.set("value", str(dx))
            elif "Agent" in name and "_DY" in name:
                other_id = int(name.split("_")[1])
                if other_id < len(world.agents):
                    dy = world.agents[other_id].state.p_pos[1] - agent.state.p_pos[1]
                    value_elem.set("value", str(dy))

            # Communication
            elif "Comm" in name:
                parts = name.split("_")
                if len(parts) == 3:
                    other_id = int(parts[1])
                    comm_channel = int(parts[2][1])
                    if (other_id < len(world.agents) and
                        comm_channel < len(world.agents[other_id].state.c)):
                        value = world.agents[other_id].state.c[comm_channel]
                        value_elem.set("value", str(value))

    # Update landmarks (if necessary)
    for obj in root.findall(".//Object"):
        obj_id = int(obj.get("id")) - 1  # XML starts at 1
        if obj_id >= len(world.landmarks):
            continue
        landmark = world.landmarks[obj_id]
        for attr in obj.findall("Attribute"):
            name = attr.find("Name").get("value")
            value_elem = attr.find("Value")
            if value_elem is None:
                continue
            if name == "X":
                value_elem.set("value", str(landmark.state.p_pos[0]))
            elif name == "Y":
                value_elem.set("value", str(landmark.state.p_pos[1]))

    # Update timestep count
    for attr in root.findall("./Attribute"):
        name = attr.find("Name").get("value")
        value_elem = attr.find("Value")
        if name == "Timestep_Count" and value_elem is not None:
            value_elem.set("value", str(current_step))

    tree.write(final_xml_path)

def find_xml_files(base_folder, seed_number):
    """Finds all 'finalState.xml' files recursively."""
    full_path = os.path.join(base_folder, seed_number)
    initialState_xml_files, finalState_xml_files = [], []
    for root, _, files in os.walk(full_path):
        if "finalState.xml" in files:
            finalState_xml_files.append(os.path.join(root, "finalState.xml"))
        if "initialState.xml" in files:
            initialState_xml_files.append(os.path.join(root, "initialState.xml"))
    return initialState_xml_files, finalState_xml_files

class InaccurateStateEnv(MultiAgentEnv):
    def __init__(self, world, reset_callback, reward_callback, observation_callback, done_callback):
        """ Modify the state representation by removing other agents' positions """
        super().__init__(world, reset_callback, reward_callback, observation_callback, done_callback=done_callback)
        self.observation_space = []
        for agent in self.agents:
            obs_dim = len(self._get_obs(agent))
            self.observation_space.append(spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32))

    def _get_obs(self, agent):
        """ Override observation function to exclude other agents' positions """
        entity_pos = [entity.state.p_pos - agent.state.p_pos for entity in self.world.landmarks]
        comm = [other.state.c for other in self.world.agents if other is not agent]
        return np.concatenate([agent.state.p_vel, agent.state.p_pos] + entity_pos + comm)

class InaccurateRewardEnv(MultiAgentEnv):
    def __init__(self, world, reset_callback, reward_callback, observation_callback):
        """ Modify reward by removing collision penalties """
        super().__init__(world, reset_callback, reward_callback, observation_callback)

    def _get_reward(self, agent):
        """ Override reward function to ignore collision penalties """
        rew = 0
        for landmark in self.world.landmarks:
            dists = [np.linalg.norm(a.state.p_pos - landmark.state.p_pos) for a in self.world.agents]
            rew -= min(dists)  # Only keep distance-based reward
        return rew

class InaccurateStateRewardEnv(MultiAgentEnv):
    def __init__(self, world, reset_callback, reward_callback, observation_callback, done_callback):
        """ Modify both state and reward functions """
        super().__init__(world, reset_callback, reward_callback, observation_callback, done_callback=done_callback)
        self.observation_space = []
        for agent in self.agents:
            obs_dim = len(self._get_obs(agent))
            self.observation_space.append(spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32))

    def _get_obs(self, agent):
        """ Modify observation to remove other agents' positions """
        entity_pos = [entity.state.p_pos - agent.state.p_pos for entity in self.world.landmarks]
        comm = [other.state.c for other in self.world.agents if other is not agent]
        return np.concatenate([agent.state.p_vel, agent.state.p_pos] + entity_pos + comm)

    def _get_reward(self, agent):
        """ Modify reward function to remove collision penalties """
        rew = 0
        for landmark in self.world.landmarks:
            dists = [np.linalg.norm(a.state.p_pos - landmark.state.p_pos) for a in self.world.agents]
            rew -= min(dists)
        return rew

class Environment:
    def __init__(self, initial_xml, final_xml):
        self.initial_xml = initial_xml
        self.final_xml = final_xml
        self.agents = {}
        self.objects = {}
        self.attributes = {}
        self.load_environment()

    def load_environment(self):
        """Loads and parses XML environment configurations"""
        init_tree = ET.parse(self.initial_xml)
        init_root = init_tree.getroot()
        final_tree = ET.parse(self.final_xml)
        final_root = final_tree.getroot()

        # Load global environment attributes
        for attr in final_root.findall("Attribute"):
            name = attr.find("Name").get("value")
            value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
            self.attributes[name] = value

        # Load agent attributes
        for agent in init_root.findall(".//Agent"):
            agent_id = agent.get("id")
            agent_data = {"id": agent_id}
            for attr in agent.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                agent_data[name] = value
            self.agents[agent_id] = agent_data

        # Load object attributes (e.g., landmarks)
        for obj in init_root.findall(".//Object"):
            obj_id = obj.get("id")
            obj_data = {"id": obj_id}
            for attr in obj.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                obj_data[name] = value
            self.objects[obj_id] = obj_data


def make_env(scenario_name, xml_path, inaccurate_model="original"):
    """Creates environment with selected inaccuracy model and XML-based configurations"""
    scenario = load(scenario_name + ".py").Scenario()
    world = scenario.make_world()

    env_config = Environment(xml_path["initial"], xml_path["final"])
    max_episode_len = env_config.attributes.get("Timestep_Count", 100)

    for i, agent in enumerate(world.agents):
        agent_idx = i+1
        if str(agent_idx) in env_config.agents:
            agent.state.p_pos = np.array([env_config.agents[str(agent_idx)]["X"], env_config.agents[str(agent_idx)]["Y"]])

    if inaccurate_model == "state":
        return InaccurateStateEnv(world, scenario.reset_world, scenario.reward, scenario.observation, scenario.done_flag)
    elif inaccurate_model == "state-reward":
        return InaccurateStateEnv(world, scenario.reset_world, scenario.reward, scenario.observation, scenario.done_flag)
    else:
        return MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation, done_callback=scenario.done_flag)

def mlp_model(input, num_outputs, scope, reuse=False, num_units=64):
    with tf.compat.v1.variable_scope(scope, reuse=tf.compat.v1.AUTO_REUSE):
        out = layers.fully_connected(input, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_outputs, activation_fn=None)
        return out

def test_policy_parallel(arglist, xml_config, model_type, trained_model, output_file):
    """Runs a trained policy on an inaccurate environment and logs results."""
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    tf.compat.v1.reset_default_graph()

    with U.single_threaded_session():
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        config.gpu_options.per_process_gpu_memory_fraction = 0.5
        sess = tf.compat.v1.Session(config=config)
        tf.compat.v1.keras.backend.set_session(sess)
        U.initialize()
        tf.compat.v1.disable_eager_execution()

        file_name_without_extension = os.path.splitext(os.path.basename(output_file))[0]
        env = make_env(arglist.scenario, xml_config, inaccurate_model=model_type)

        obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
        trainers = [MADDPGAgentTester(f"agent_{i}", mlp_model, obs_shape_n, env.action_space, i, arglist) for i in range(env.n)]
        U.initialize()
        U.load_state(trained_model)

        ep_reward = 0
        total_collisions = 0
        bug_found = False
        termination_reason = "Task Completed"

        obs_n = env.reset()
        episode_data = []

        for step_id in range(arglist.max_episode_len):
            actions = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]
            new_obs_n, rew_n, done_n, _ = env.step(actions)

            step_collision = 0
            for i, agent in enumerate(env.world.agents):
                for j, agent_other in enumerate(env.world.agents):
                    if i < j:  # Only check each unique pair once
                        if np.linalg.norm(agent.state.p_pos - agent_other.state.p_pos) < (agent.size + agent_other.size):
                            step_collision = 1
                            total_collisions += 1

            episode_data.append({
                "state": obs_n,
                "action": actions,
                "collision": step_collision,
                "timeout": 0
            })

            obs_n = new_obs_n

            # Check for termination conditions
            if total_collisions > 5:
                bug_found = True
                termination_reason = "High Collision"
                break

            ep_reward += sum(rew_n)
            if all(done_n):
                bug_found = False
                termination_reason = "Task Completed"
                break

        if step_id >= arglist.max_episode_len:
            bug_found = True
            termination_reason = "Timeout"

        # Update last step for timeout
        if termination_reason == "Timeout":
            episode_data[-1]["timeout"] = 1

        environment, task, seed, bin_number = extract_metadata_from_path(xml_config["initial"])

        result = {
            "Environment": environment,
            "Task": task,
            "Seed": seed,
            "Bin": bin_number,
            "InaccuracyType": model_type,
            "Steps": step_id + 1,
            "Collisions": total_collisions,
            "TerminationReason": termination_reason,
            "BugFound": bug_found
        }
        write_result_to_csv(output_file, result)
        save_pickle(xml_config["initial"], model_type, episode_data)
        
        # Update finalState.xml or crash.xml
        final_xml_path = xml_config["final"]
        if bug_found and termination_reason == "High Collision":
            crash_xml_path = os.path.join(os.path.dirname(final_xml_path), f"{file_name_without_extension}_crash.xml")
            shutil.copyfile(final_xml_path, crash_xml_path)
            update_full_environment_xml(crash_xml_path, env, step_id + 1)
        else:
            non_crash_xml_path = os.path.join(os.path.dirname(final_xml_path), f"{file_name_without_extension}_simulation_final.xml")
            shutil.copyfile(final_xml_path, non_crash_xml_path)
            update_full_environment_xml(non_crash_xml_path, env, step_id + 1)


def save_pickle(xml_file_path, model_type, episode_data):
    """Saves a single episode's state-action pairs with step-wise collision/timeout flags to a pickle file."""
    dir_path = os.path.dirname(xml_file_path)
    filename = "accurate"
    if model_type=="state":
        filename = "inaccurate_state"
    elif model_type=="state-reward":
        filename = "inaccurate_state_and_reward"
    elif model_type=="reward":
        filename = "inaccurate_reward"
    pickle_file_name = f"{filename}_data.pkl"
    pickle_file_path = os.path.join(dir_path, pickle_file_name)

    with open(pickle_file_path, "wb") as f:
        pickle.dump(episode_data, f)

def extract_metadata_from_path(xml_file_path):
    """Extracts Environment, Task, Seed, and Bin from the XML file path."""
    parts = xml_file_path.split(os.sep)
    environment = next((p for p in parts if p.startswith("Env_")), "Unknown_Env")
    task = next((p for p in parts if p.startswith("Task_")), "Unknown_Task")
    seed = next((p for p in parts if p.isdigit()), "Unknown_Seed")
    bin_number = next((p for p in parts if re.match(r"^\d+_Bin$", p)), "Unknown_Bin")
    return environment, task, seed, bin_number

def write_result_to_csv(output_file, result):
    """Writes a single result entry to the CSV file safely using a file lock."""
    keys = ["Environment", "Task", "Seed", "Bin", "InaccuracyType", "Steps", "Collisions", "TerminationReason", "BugFound"]
    file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0
    with lock:
        with open(output_file, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)
            csvfile.flush()

def init_worker():
    """Each worker gets its own lock (avoids pickling issues)."""
    global lock
    lock = multiprocessing.Lock()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    base_folders = ["AIProbe/Result/MARL_Coop_Navi/100_Bin"]

    for base_folder in base_folders:
        log_file_path = os.path.join(base_folder, "log.txt")
        seeds = ['534', '789', '78901', '54321', '12876', '4532', '98765', '21456', '3768', '5698', '11223', '67890', '32456', '90785', '15098', '74321', '8967', '22589', '61987', '37012']

        total_start = time.time()
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\n=== Run started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            log_file.flush()

            for seed_number in seeds:
                print(f"\nProcessing Seed: {seed_number}")
                seed_start = time.time()


                initialState_xml_files, finalState_xml_files = find_xml_files(base_folder, seed_number)
                print(f"Found {len(initialState_xml_files)} simulation cases.")
                log_file.write(f"Seed {seed_number}: {len(initialState_xml_files)} cases found\n")
                log_file.flush()

                arglist = parse_args()
                tasks = []
                for file_id in range(len(initialState_xml_files)):
                    xml_config = {"initial": initialState_xml_files[file_id], "final": finalState_xml_files[file_id]}
                    for model_type in ["accurate","state","state-reward","reward"]:
                        trained_model = ''
                        output_file = '' 
                        if model_type == "state":
                            trained_model = "/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/InaccurateModels/inaccurate_state/checkpoints/checkpoints"
                            output_file = f"{base_folder}/inaccurate_state_results.csv"
                        elif model_type == "state-reward":
                            trained_model = "/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/InaccurateModels/inaccurate_state_reward/checkpoints/checkpoints"
                            output_file = f"{base_folder}/inaccurate_state_and_reward_results.csv"
                        elif model_type == "reward":
                            trained_model = "/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/InaccurateModels/inaccurate_reward/checkpoints/checkpoints"
                            output_file = f"{base_folder}/inaccurate_reward_results.csv"
                        elif model_type == "accurate":
                            trained_model = "/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/maddpg/checkpoints/model.ckpt-1"
                            output_file = f"{base_folder}/accurate_model.csv"
                        else:
                            continue

                        tasks.append((arglist, xml_config, model_type, trained_model, output_file))

                ctx = multiprocessing.get_context("spawn")
                MAX_PROCESSES = 10

                for task_chunk in chunked_iterable(tasks, MAX_PROCESSES):
                    with ctx.Pool(MAX_PROCESSES, initializer=init_worker, maxtasksperchild=1) as pool:
                        pool.starmap(test_policy_parallel, task_chunk)

                seed_time = (time.time() - seed_start) / 60
                print(f"Seed {seed_number} completed in {seed_time:.2f} minutes.")
                log_file.write(f"✔ Seed {seed_number} completed in {seed_time:.2f} minutes.\n")
                log_file.flush()

            total_time = (time.time() - total_start) / 60
            print(f"\nAll seeds processed in {total_time:.2f} minutes.")
            log_file.write(f"All seeds processed in {total_time:.2f} minutes.\n")
            log_file.write(f"=== Run ended at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
            log_file.flush()