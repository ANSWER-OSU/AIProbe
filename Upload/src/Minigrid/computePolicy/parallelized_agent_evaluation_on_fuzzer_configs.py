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
        #output_path = f'results_for_fuzzer_gen_configs/Env_{env_number}{model}.csv'
        output_path = f'lava_test_results/Seed_{seed}/{model}_results.csv'

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
        print('starting VI')
        v, pi = valueIteration(env)
        print(f"Value Iteration completed for task {task} (Env: {env_number}, Seed: {seed})")
        final_x, final_y = env.agent_pos  # Or equivalent
        final_dir = env.agent_dir  # Or equivalent

        create_and_update_simulation_final_xml(goal_xml_file, (final_x, final_y), final_dir,model)

        # Get evaluation metrics
        if env.task == 'keyToGoal':
            avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(
                env, pi, trials=num_sim_trials
            )
            write_metrics(num_sim_trials, env_number, avg_undesired_states, avg_wrong_key, times_goal_reached, avg_reward, reward_sd, output_path)
        else:
            avg_undesired_states, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(env, pi, trials=num_sim_trials)
            if(times_goal_reached == 0):
                create_and_update_simulation_final_xml(goal_xml_file, (final_x, final_y), final_dir, model)
            print('writing metrics')
            write_metrics(num_sim_trials, avg_undesired_states, times_goal_reached, avg_reward, reward_sd, output_path, seed, env_number, task)

    except Exception as e:
        logger.error(f"Error processing task {task} (Env: {env_number}, Seed: {seed}): {e}")


def create_and_update_simulation_final_xml(original_xml_file, final_pos, final_dir,model):
    """
    Copies original_xml_file to simulationFinal.xml and updates agent position.
    final_pos: (x, y)
    final_dir: int (e.g., 0-North, 1-East, etc.)
    """
    import shutil

    new_xml_file = os.path.join(os.path.dirname(original_xml_file), f"{model}simulation_finalSate.xml")

    # Step 1: Copy original XML to new file
    shutil.copyfile(original_xml_file, new_xml_file)

    # Step 2: Parse and update the new XML
    tree = ET.parse(new_xml_file)
    root = tree.getroot()

    agents_node = root.find('Agents')
    if agents_node is None:
        logger.info("No Agents section found in XML.")
        return

    agent = agents_node.find('Agent')
    if agent is None:
        logger.info("No Agent node found.")
        return

    attrs = agent.findall('Attribute')
    if len(attrs) < 3:
        logger.info("Agent does not have enough attributes to update position.")
        return

    # Update x, y, dir
    attrs[0].find('Value').set('value', str(final_pos[0]))
    attrs[1].find('Value').set('value', str(final_pos[1]))
    attrs[2].find('Value').set('value', str(final_dir))

    # Save updated XML
    tree.write(new_xml_file)
    logger.info(f"Updated simulation final state saved to: {new_xml_file}")

# def evaluate_fuzzer_config(file_path):
#     """Main function to evaluate fuzzer config in parallel."""
#     start_time = time.time()
#     inaccuracy = {
#         #0: '_accurate_reward_accurate_state_rep',
#         #1: '_inaccurate_reward_accurate_state_rep',
#         2: '_accurate_reward_inaccurate_state_rep',
#         3: '_inaccurate_reward_inaccurate_state_rep'
#     }

#     env_config_dir = file_path
#     num_sim_trials = 1  # Number of simulation trials
#     tasks = []

#     for seed_dir in os.listdir(env_config_dir):
#         seed_path = os.path.join(env_config_dir, seed_dir)
#         if not os.path.isdir(seed_path): #or not seed_dir.startswith("Seed_"):
#             continue

#         seed = seed_dir

#         for env_dir in os.listdir(seed_path):
#             env_path = os.path.join(seed_path, env_dir)
#             if not os.path.isdir(env_path) or not env_dir.startswith("Env_"):
#                 continue

#             env_number = int(env_dir.split("_")[1])

#             for task_dir in os.listdir(env_path):
#                 task_path = os.path.join(env_path, task_dir)
#                 if task_dir in {"random_values.csv", "improvedLHS_values.csv"} or not os.path.isdir(task_path):
#                     continue

#                 if not task_dir.startswith("Task_"):
#                     continue

#                 task_id = int(task_dir.split("_")[1])

#                 xml_file = os.path.join(task_path, 'initialState.xml')
#                 goal_xml_file = os.path.join(task_path, 'finalState.xml')

#                 for inaccuracy_type, model in inaccuracy.items():
#                     tasks.append((xml_file, goal_xml_file, inaccuracy_type, model, env_number, seed, task_id, num_sim_trials))
#     # Run tasks in parallel
#     num_workers = min(160, len(tasks))  # Use all available CPU cores
#     logger.info(f"Running {len(tasks)} tasks with {num_workers} workers...")

#     with multiprocessing.Pool(processes=num_workers) as pool:
#         pool.map(process_task, tasks)
        

def evaluate_fuzzer_config(file_path):
    """Main function to evaluate fuzzer config sequentially."""
    start_time = time.time()
    inaccuracy = {
        0: '_accurate_reward_accurate_state_rep',
        1: '_inaccurate_reward_accurate_state_rep',
        2: '_accurate_reward_inaccurate_state_rep',
        3: '_inaccurate_reward_inaccurate_state_rep'
    }

    env_config_dir = file_path
    num_sim_trials = 1  # Number of simulation trials
    tasks = []

    for seed_dir in os.listdir(env_config_dir):
        seed_path = os.path.join(env_config_dir, seed_dir)
        if not os.path.isdir(seed_path):
            continue

        seed = seed_dir

        for env_dir in os.listdir(seed_path):
            env_path = os.path.join(seed_path, env_dir)
            if not os.path.isdir(env_path) or not env_dir.startswith("Env_"):
                continue

            env_number = int(env_dir.split("_")[1])

            for task_dir in os.listdir(env_path):
                task_path = os.path.join(env_path, task_dir)
                if task_dir in {"random_values.csv", "improvedLHS_values.csv"} or not os.path.isdir(task_path):
                    continue

                if not task_dir.startswith("Task_"):
                    continue

                task_id = int(task_dir.split("_")[1])

                xml_file = os.path.join(task_path, 'initialState.xml')
                goal_xml_file = os.path.join(task_path, 'finalState.xml')

                for inaccuracy_type, model in inaccuracy.items():
                    tasks.append((xml_file, goal_xml_file, inaccuracy_type, model, env_number, seed, task_id, num_sim_trials))

    logger.info(f"Running {len(tasks)} tasks sequentially...")

    for task_args in tasks:
        process_task(task_args)

    total_time = (time.time() - start_time) / 60.0
    logger.info(f"Total time taken: {total_time:.2f} mins")



import logging

# Setup logger
logging.basicConfig(
    filename='fuzzer_evaluation_log_approch1.txt',
    filemode='a',  # Append mode
    format='[%(asctime)s] %(levelname)s: %(message)s',
    level=logging.INFO
)

logger = logging.getLogger()

if __name__ == "__main__":

    evaluate_fuzzer_config("/scratch/projects/AIProbe-Main/test_lava")
