

import os
import time
import json
import hashlib
import copy
import random
import pandas as pd
from multiprocessing import Pool, Manager
from tqdm import tqdm
from MinigridWrapper import run_minigrid_with_single_action
from enviroment_parser import parse_xml_to_dict
import argparse


# Constants
ACTION_SPACE = ["left", "right", "forward"]
MAX_DEPTH = 200
BINS = 100
K_SAMPLE = 10
TRIAL_SEEDS = [825, 386, 543, 230, 40, 925, 325, 361, 494, 720]

def compute_hash(env):
    env_dict = json.loads(json.dumps(env, default=lambda o: getattr(o, '__dict__', str(o))))
    agent_attrs = env_dict['Agents']['AgentList'][0]['Attributes']
    attr_map = {attr['Name']['Value']: attr['Value']['Content'] for attr in agent_attrs}
    x = attr_map.get('X')
    y = attr_map.get('Y')
    hash_input = {"X": float(x), "Y": float(y)}
    return hashlib.sha256(json.dumps(hash_input, sort_keys=True).encode()).hexdigest()

def step_fn(env, action):
    env_copy = copy.deepcopy(env)
    updated_env, terminated = run_minigrid_with_single_action(env_copy, action)
    return updated_env, not terminated

def is_crashing(env):
    _, terminated = run_minigrid_with_single_action(copy.deepcopy(env), "left")
    return terminated

def compute_steps(env1, env2, b=BINS):
    def get_agent_info(env_dict):
        attr_list = env_dict['Agents']['AgentList'][0]['Attributes']
        attr_map = {attr['Name']['Value']: int(attr['Value']['Content']) for attr in attr_list}
        return attr_map['X'], attr_map['Y'], attr_map['Angle']
    x1, y1, d1 = get_agent_info(env1)
    x2, y2, d2 = get_agent_info(env2)
    dist = abs(x1 - x2) + abs(y1 - y2)
    if dist > 100:
        bin_size = b * 2
    elif dist > 50:
        bin_size = b
    else:
        bin_size = max(1, b // 2)
    return max(1, dist // bin_size)

def run_dfs_k_sampling_with_retries(S_i, S_f, hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
                                    max_depth, action_space, b=5, k=10, seed=0):
    random.seed(seed)
    visited = set()

    def dfs_recursive(S_curr, instr, depth):
        if depth > max_depth:
            return False, []

        curr_hash = hash_fn(S_curr)
        if curr_hash == hash_fn(S_f):
            return True, instr

        if is_crashing_fn(S_curr) or curr_hash in visited:
            return False, []

        visited.add(curr_hash)

        k_sample = compute_steps_fn(S_curr, S_f, b)
        sample_actions = random.choices(action_space, k=max(k_sample, len(action_space)))

        for action in sample_actions:
            candidate_path = instr + [action]
            S_next, is_safe = step_fn(S_curr, action)
            if not is_safe:
                continue

            extra_steps = []
            S_temp = S_next
            for _ in range(k_sample - 1):
                next_action = random.choice(action_space)
                extra_steps.append(next_action)
                S_temp2, is_safe2 = step_fn(S_temp, next_action)
                if not is_safe2:
                    break
                S_temp = S_temp2

            full_candidate_path = candidate_path + extra_steps

            found, path = dfs_recursive(S_temp, full_candidate_path, depth + 1)
            if found:
                return True, path

        return False, []

    return dfs_recursive(S_i, [], 0)



def try_seed(args):
    seed, S_i, S_f, stop_event, mode = args
    if stop_event.is_set():
        return None

    random.seed(seed)

    if mode == "new":
        success, path = run_dfs_k_sampling_with_retries(
            S_i, S_f,
            hash_fn=compute_hash,
            step_fn=step_fn,
            is_crashing_fn=is_crashing,
            compute_steps_fn=compute_steps,
            max_depth=MAX_DEPTH,
            action_space=ACTION_SPACE,
            b=BINS,
            k=K_SAMPLE,
            seed=seed,
        )
    else:
        success, path, _ = run_dfs_with_retries(
            S_i, S_f,
            hash_fn=compute_hash,
            step_fn=step_fn,
            is_crashing_fn=is_crashing,
            compute_steps_fn=compute_steps,
            max_depth=MAX_DEPTH,
            action_space=ACTION_SPACE,
            b=BINS,
            seed=seed,
        )

    if success:
        stop_event.set()
        return (True, seed, path)
    else:
        return (False, seed, None)



def try_one_task(initial_path, final_path, mode):
    try:
        S_i = parse_xml_to_dict(initial_path)
        S_f = parse_xml_to_dict(final_path)
    except Exception as e:
        print(f"Error parsing {initial_path}: {e}")
        return (initial_path, False, 0)

    manager = Manager()
    stop_event = manager.Event()

    seed_args = [(seed, S_i, S_f, stop_event, mode) for seed in TRIAL_SEEDS]

    start_time = time.time()

    with Pool(processes=min(len(TRIAL_SEEDS), os.cpu_count())) as seed_pool:
        for result in seed_pool.imap_unordered(try_seed, seed_args):
            if result is None:
                continue

            status, seed, path = result

            if status == True:
                elapsed = time.time() - start_time
                print(f"Task {initial_path} solved with seed {seed} in {elapsed:.2f} seconds")

                # Save instruction
                instruction_save_path = os.path.join(os.path.dirname(initial_path), "instruction.json")
                try:
                    with open(instruction_save_path, 'w') as f_out:
                        json.dump({"instruction": path}, f_out, indent=2)
                    print(f" Instruction saved to {instruction_save_path}")
                except Exception as e:
                    print(f"Failed to save instruction JSON: {e}")

                seed_pool.terminate()
                seed_pool.join()
                return (initial_path, True, elapsed)

    elapsed = time.time() - start_time
    print(f"Task {initial_path} unsolved after {elapsed:.2f} seconds")
    return (initial_path, False, elapsed)

def run_from_csv(csv_path, base_dir, mode="new"):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    print("Available columns:", df.columns.tolist())

    df_filtered = df[(df['#Lava'] == 1) & (df['#AgentToGoal'] == 0)]
    print(f"Total tasks to try: {len(df_filtered)}")

    # Prepare args for each task
    task_args = []
    for _, row in df_filtered.iterrows():
        seed = int(row['Seed'])
        env = int(row['Env#'])
        task = int(row['Task#'])

        initial_path = os.path.join(base_dir, f"{seed}", f"Env_{env}", f"Task_{task}", "initialState.xml")
        final_path = os.path.join(base_dir, f"{seed}", f"Env_{env}", f"Task_{task}", "finalState.xml")

        task_args.append((initial_path, final_path, mode))

    # Now parallelize tasks
    output_data = []
    with Pool(processes=min(os.cpu_count(), 4)) as pool:  # limit to 64 or cpu_count
        for result in tqdm(pool.imap_unordered(try_one_task_wrapper, task_args), total=len(task_args), desc="🛠️ Tasks"):
            output_data.append({
                "Task_Dir": result[0],
                "Solved": result[1],
                "Time_Taken": round(result[2], 2)
            })

    # Save all results
    output_df = pd.DataFrame(output_data)
    output_path = "minigrid_parallel_task.csv"
    output_df.to_csv(output_path, index=False)

    total_solved = output_df['Solved'].sum()
    print(f"\nDone. {total_solved}/{len(output_data)} tasks solved.")
    print(f"Results saved to: {output_path}")

def try_one_task_wrapper(args):
    initial_path, final_path, mode = args
    return try_one_task(initial_path, final_path, mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run policy evaluation from CSV")
    parser.add_argument("--csv_path", type=str, required=True, help="Path to the CSV result file")
    parser.add_argument("--base_dir", type=str, required=True, help="Base directory for XML results")
    
    args = parser.parse_args()
    run_from_csv(
        csv_path=args.csv_path,
        base_dir=args.base_dir,
        mode="new"
    )