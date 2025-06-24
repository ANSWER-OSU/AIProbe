
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
from lxml import etree as ET
from multiprocessing import Pool
from tqdm import tqdm
from os.path import abspath
import gc

from src.Minigrid.VI import valueIteration
from src.Minigrid.helper_functions import get_num_undesired_states
from src.Minigrid.loggers import write_metrics
import MinigridEnv_custom as MinigridEnv


def parse_xml_to_dict(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    def parse_attr(attr):
        return {
            'Name': {'Value': attr.find('Name').get('value')},
            'DataType': {'Value': attr.find('DataType').get('value')},
            'Value': {'Content': attr.find('Value').get('value')},
            'Mutable': {'Value': attr.find('Mutable') is not None and attr.find('Mutable').get('value') == "true"},
            'Constraint': {
                'Min': attr.find('Constraint').get('Min') if attr.find('Constraint') is not None else None,
                'Max': attr.find('Constraint').get('Max') if attr.find('Constraint') is not None else None
            }
        }

    data = {
        'Name': root.get('name'),
        'Type': root.get('type'),
        'Agents': {'AgentList': []},
        'Objects': {'ObjectList': []},
        'Attributes': [parse_attr(attr) for attr in root.findall('Attribute')]
    }

    for agent in root.findall('./Agents/Agent'):
        data['Agents']['AgentList'].append({
            'Id': int(agent.get('id')),
            'Type': agent.get('type'),
            'Attributes': [parse_attr(attr) for attr in agent.findall('Attribute')]
        })

    for obj in root.findall('./Objects/Object'):
        data['Objects']['ObjectList'].append({
            'Id': int(obj.get('id')),
            'Type': obj.get('type'),
            'Attributes': [parse_attr(attr) for attr in obj.findall('Attribute')]
        })

    return data


def evaluate_single_model(xml_file, goal_xml_file, env_number, seed, task_id, num_sim_trials, inaccuracy_type, model_name):
    try:
        env_data = parse_xml_to_dict(abspath(xml_file))
        goal_data = parse_xml_to_dict(abspath(goal_xml_file))

        goal_x = int(goal_data['Agents']['AgentList'][0]['Attributes'][0]['Value']['Content'])
        goal_y = int(goal_data['Agents']['AgentList'][0]['Attributes'][1]['Value']['Content'])
        goal_dir = int(goal_data['Agents']['AgentList'][0]['Attributes'][2]['Value']['Content'])
        goal_pos = (goal_x, goal_y)

        accurate_model = (inaccuracy_type == 0)

        env = MinigridEnv.CustomMiniGridEnv(
            environment_data=env_data,
            accurate_model=accurate_model,
            task='escLava',
            inaccuracy_type=inaccuracy_type,
            goal_pos=goal_pos,
            goal_dir=goal_dir
        )
        env.reset()

        v, pi = valueIteration(env)

        output_csv = f'lava_results_custom_fixed/{model_name}_results.csv'
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)

        avg_undesired, times_goal_reached, avg_reward, reward_sd = get_num_undesired_states(env, pi, trials=num_sim_trials)
        write_metrics(num_sim_trials, avg_undesired, times_goal_reached, avg_reward, reward_sd, output_csv, seed, env_number, task_id)

        # Clean up
        del env, env_data, goal_data, v, pi
        gc.collect()

    except Exception as e:
        print(f"Failed for Seed {seed} | Env {env_number} | Task {task_id} | Model {model_name}: {e}")


def get_num_workers():
    # Default number of workers
    return 42
    # Uncomment the following lines if using HPC
    # slurm_cpus = os.environ.get("SLURM_CPUS_PER_TASK")
    # if slurm_cpus:
    #     return int(slurm_cpus)
    # return max(1, min(cpu_count(), 50))

def run_evaluation(base_dir):
    num_sim_trials = 1
    inaccuracy_models = {
        0: 'accurate_reward_accurate_state_rep',
        1: 'inaccurate_reward_accurate_state_rep',
        2: 'accurate_reward_inaccurate_state_rep',
        3: 'inaccurate_reward_inaccurate_state_rep'
    }

    seed_dirs = [
        os.path.join(base_dir, seed) for seed in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, seed))
    ]

    num_workers = get_num_workers()
    print(f"Running evaluation for {len(seed_dirs)} selected seeds using {num_workers} workers...")

    all_jobs = []
    for seed_dir in seed_dirs:
        seed = os.path.basename(seed_dir)
        for env in os.listdir(seed_dir):
            env_path = os.path.join(seed_dir, env)
            if not os.path.isdir(env_path) or not env.startswith("Env_"):
                continue

            env_number = int(env.split("_")[1])
            for task in os.listdir(env_path):
                task_path = os.path.join(env_path, task)
                if not os.path.isdir(task_path) or not task.startswith("Task_"):
                    continue

                task_id = int(task.split("_")[1])
                xml_file = os.path.join(task_path, 'initialState.xml')
                goal_xml_file = os.path.join(task_path, 'finalState.xml')

                if os.path.exists(xml_file) and os.path.exists(goal_xml_file):
                    for inacc_type, model_name in inaccuracy_models.items():
                        all_jobs.append((
                            xml_file, goal_xml_file, env_number, seed,
                            task_id, num_sim_trials, inacc_type, model_name
                        ))

    print(f"Total tasks queued: {len(all_jobs)}")
    with Pool(processes=num_workers) as pool:
        list(tqdm(pool.starmap(evaluate_single_model, all_jobs), total=len(all_jobs)))

if __name__ == "__main__":
    run_evaluation("/PATH/TO/GENERATED/XML/FILES")




  
