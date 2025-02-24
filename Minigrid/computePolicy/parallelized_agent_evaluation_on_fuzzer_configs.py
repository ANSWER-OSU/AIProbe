import os
import sys
import time
import xml.etree.ElementTree as ET
import numpy as np
import multiprocessing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from computePolicy.VI import valueIteration
from computePolicy.helper_functions import get_num_undesired_states
from computePolicy.loggers import write_metrics

import MinigridEnv


def parse_xml_to_dict(xml_file):
    """Parses an XML file and returns a structured dictionary."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    env_dict = {
        'Name': root.get('name'),
        'Type': root.get('type'),
        'Agents': {'AgentList': []},
        'Objects': {'ObjectList': []},
        'Attributes': []
    }

    def parse_attribute(attr_node):
        return {
            'Name': {'Value': attr_node.find('Name').get('value')},
            'DataType': {'Value': attr_node.find('DataType').get('value')},
            'Value': {'Content': attr_node.find('Value').get('value')},
            'Mutable': {'Value': attr_node.find('Mutable').get('value') == "true"} if attr_node.find('Mutable') is not None else None,
            'Constraint': {
                'Min': attr_node.find('Constraint').get('Min') if attr_node.find('Constraint') is not None else None,
                'Max': attr_node.find('Constraint').get('Max') if attr_node.find('Constraint') is not None else None
            }
        }

    agents_node = root.find('Agents')
    if agents_node is not None:
        for agent in agents_node.findall('Agent'):
            agent_dict = {
                'Id': int(agent.get('id')),
                'Type': agent.get('type'),
                'Attributes': [parse_attribute(attr) for attr in agent.findall('Attribute')]
            }
            env_dict['Agents']['AgentList'].append(agent_dict)

    objects_node = root.find('Objects')
    if objects_node is not None:
        for obj in objects_node.findall('Object'):
            obj_dict = {
                'Id': int(obj.get('id')),
                'Type': obj.get('type'),
                'Attributes': [parse_attribute(attr) for attr in obj.findall('Attribute')]
            }
            env_dict['Objects']['ObjectList'].append(obj_dict)

    for attr in root.findall('Attribute'):
        env_dict['Attributes'].append(parse_attribute(attr))

    return env_dict


def process_task(args):
    """Process a single fuzzer task in parallel."""
    xml_file, goal_xml_file, inaccuracy_type, model, env_number, seed, task, num_sim_trials = args
    print(f"Processing task {task} (Env: {env_number}, Seed: {seed})...")

    try:
        accurate_model = True if inaccuracy_type == 0 else False
        output_path = f'results_for_fuzzer_gen_configs/Env_{env_number}{model}.csv'

        # Parse environment
        environment_data = parse_xml_to_dict(xml_file)
        final_env_data = parse_xml_to_dict(goal_xml_file)

        # Extract goal position from final state
        goal_x = int(final_env_data['Agents']['AgentList'][0]['Attributes'][0]['Value']['Content'])
        goal_y = int(final_env_data['Agents']['AgentList'][0]['Attributes'][1]['Value']['Content'])
        goal_dir = int(final_env_data['Agents']['AgentList'][0]['Attributes'][2]['Value']['Content'])
        goal_xy = (goal_x, goal_y)

        # Get environment properties
        attr_dict = {attr['Name']['Value']: int(attr['Value']['Content']) for attr in environment_data['Attributes']}
        grid_size = attr_dict.get("Grid", 10)  # Default 10 if not found
        lava_count = attr_dict.get("Lava", 0)  # Default 0 if not found

        # Instantiate environment
        env = MinigridEnv.CustomMiniGridEnv(
            environment_data=environment_data,
            accurate_model=accurate_model,
            task='escLava',
            inaccuracy_type=inaccuracy_type,
            goal_pos=goal_xy,
            goal_dir=goal_dir
        )
        env.reset()

        # Run Value Iteration
        v, pi = valueIteration(env)

        # Get evaluation metrics
        if env.task == 'keyToGoal':
            avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(
                env, pi, trials=num_sim_trials
            )
            write_metrics(num_sim_trials, env_number, avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward, reward_sd, output_path)
        else:
            avg_undesired_states, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(env, pi, trials=num_sim_trials)
            write_metrics(num_sim_trials, avg_undesired_states, times_goal_reached, avg_reward, reward_sd, output_path, seed, env_number, task)

    except Exception as e:
        print(f"Error processing task {task} (Env: {env_number}, Seed: {seed}): {e}")


def evaluate_fuzzer_config():
    """Main function to evaluate fuzzer config in parallel."""
    start_time = time.time()
    inaccuracy = {
        0: '_accurate_reward_accurate_state_rep',
        1: '_inaccurate_reward_accurate_state_rep',
        2: '_accurate_reward_inaccurate_state_rep',
        3: '_inaccurate_reward_inaccurate_state_rep'
    }

    env_config_dir = sys.argv[1]
    num_sim_trials = 1  # Number of simulation trials
    tasks = []

    for env_for_seed in os.listdir(env_config_dir):
        env_seed_path = os.path.join(env_config_dir, env_for_seed)
        if not os.path.isdir(env_seed_path):
            continue

        for env_num in os.listdir(env_seed_path):
            filepath = os.path.join(env_seed_path, env_num)
            if not os.path.isdir(filepath):
                continue

            for task in os.listdir(filepath):
                task_path = os.path.join(filepath, task)
                if task in {"random_values.csv", "improvedLHS_values.csv"} or not os.path.isdir(task_path):
                    continue
                xml_file = os.path.join(task_path, 'initialState.xml')
                goal_xml_file = os.path.join(task_path, 'finalState.xml')

                env_number = int(xml_file.split('/')[-3].split('_')[1])
                seed = int(xml_file.split('/')[-4].split('_')[2])
                task_id = int(xml_file.split('/')[-2].split('_')[1])

                for inaccuracy_type, model in inaccuracy.items():
                    tasks.append((xml_file, goal_xml_file, inaccuracy_type, model, env_number, seed, task_id, num_sim_trials))

    # Run tasks in parallel
    num_workers = min(multiprocessing.cpu_count(), len(tasks))  # Use all available CPU cores
    print(f"Running {len(tasks)} tasks with {num_workers} workers...")

    with multiprocessing.Pool(processes=num_workers) as pool:
        pool.map(process_task, tasks)

    total_time = (time.time() - start_time)/60
    print(f"Total time taken: {total_time:.2f} mins")

if __name__ == "__main__":

    evaluate_fuzzer_config()
