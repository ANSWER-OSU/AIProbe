import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import random
import pickle
import hashlib
from copy import deepcopy
from helper_functions import (create_flappy_bird_env_from_dict,flappy_bird_xml_to_dict,flappy_bird_env_to_dict)
import warnings
import csv
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
import pandas as pd
import json
import time
from helper_functions import flappy_bird_xml_to_dict
from multiprocessing import Pool, cpu_count, Manager, Lock
import datetime
import logging
import sys
import argparse

# Configuration parameters
max_depth = 200  
seeds = [10 , 23, 66, 32, 73, 881, 71203, 93572, 28514, 60497,123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021,2223]
action_space = [1,0]
b = 100
k = 10


# Helper functions
def make_env(state_dict):
    return create_flappy_bird_env_from_dict(state_dict)

def step_fn(env, action):
    obs, reward, terminated, truncated, info = env.step(action)
    #print("obs:", obs)
    #env.render()
    safe = not (terminated or truncated or info.get("game_stats", {}).get("crashed", False))
    return env, safe

def get_timestep(env):
    state_dict = flappy_bird_env_to_dict(env)
    return state_dict.get("Timestep_Count", 0)

def hash_fn(env):
    dic = flappy_bird_env_to_dict(env)
    x = dic['agent_params']['X']
    y = dic['agent_params']['Y']
    t = dic['env_params']['Timestep']

    state_str = f"x={x:.2f},y={y:.2f},t={int(t)}"
    return hashlib.sha256(state_str.encode('utf-8')).hexdigest()

def is_crashing_fn(env):
    obs, reward, terminated, truncated, info = env.step(0)
    return terminated or truncated or info.get("game_stats", {}).get("crashed", False)

def deepcopy_env(env):
    from helper_functions import flappy_bird_env_to_dict, create_flappy_bird_env_from_dict
    state = flappy_bird_env_to_dict(env)
    return create_flappy_bird_env_from_dict(state)

def compute_steps_fn(env_curr, target_timesteps, b):
    from helper_functions import flappy_bird_env_to_dict
    curr_timestep = flappy_bird_env_to_dict(env_curr).get("env_params", {}).get("Timestep_Count", 0)
    remaining = max(0, target_timesteps - curr_timestep)
    return max(remaining, b)


def generate_instruction(env, action_space, target_timesteps, b, compute_steps_fn, k_max):
    k_sample = min(k_max, int(compute_steps_fn(env, target_timesteps, b)))
    return tuple(random.choices(action_space, k=k_sample))

# Heuristic guided search  
def run_dfs_survive_to_timesteps_k_sampling(S_i, target_timesteps, env_constructor, hash_fn, step_fn, is_crashing_fn,compute_steps_fn, max_depth, action_space, b=5, k=3, seed=0):
    import random
    from copy import deepcopy
    from helper_functions import flappy_bird_env_to_dict

    random.seed(seed)
    visited = {} 

    def get_timestep(env):
        dic = flappy_bird_env_to_dict(env)
        return dic['env_params']['Timestep']

    def dfs(S_curr_dict, instr_so_far, depth):
        env = env_constructor(S_curr_dict)
    
        for action in instr_so_far:
            env, is_safe = step_fn(env, action)
            if not is_safe:
                return False, []
        
        curr_time = get_timestep(env)
        print(f"Print targetstep :{target_timesteps}")
        if curr_time >= target_timesteps:
            return True, instr_so_far
        if depth > max_depth:
            return False, []

        curr_hash = hash_fn(env)
        if curr_hash not in visited:
            visited[curr_hash] = set()

        attempts = 0
        max_attempts =  k  

        while attempts < max_attempts:
            path = generate_instruction(env, action_space, target_timesteps, b, compute_steps_fn, k)

            if path in visited[curr_hash]:
                attempts += 1
                continue

            visited[curr_hash].add(path)
            attempts += 1
            
            env_next = deepcopy_env(env)
            valid = True
            for act in path:
                env_next, is_safe = step_fn(env_next, act)
                if not is_safe:
                    valid = False
                    break

            if not valid:
                continue

            full_instr = instr_so_far + list(path)
            print(f"[Depth {depth}] Trying path: {full_instr} → total steps: {len(full_instr)}")

            found, result = dfs(S_i, full_instr, depth + 1)
            if found:
                return True, result
        return False, []

    return dfs(S_i, [], 0)

def run_custom_action_sequence(S_i, action_sequence, env_constructor, step_fn):
    env = env_constructor(S_i)
    actual_path = []

    for step_id, action in enumerate(action_sequence):
        env, is_safe = step_fn(env, action)
        actual_path.append(action)

        if not is_safe:
            print(f"Crash occurred at step {step_id}, action={action}")
            return False, actual_path, step_id

    print("Sequence completed without crashing.")
    return True, actual_path, None

def get_buggy_paths(csv_file):
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()
    if "BugFound" not in df.columns:
        raise ValueError(f"'BugFound' column missing in {csv_file}")
    buggy_rows = df[df["BugFound"] == True]
    return set(
        os.path.join(base_dir, str(row["Seed"]), row["Environment"], f"{row['Task']}")
        for _, row in buggy_rows.iterrows()
    )

def process_task(task_path):
    initial_xml = os.path.join(task_path, "initialState.xml")
    final_xml = os.path.join(task_path, "finalState.xml")
    instruction_json = os.path.join(task_path, "instruction.json")

    if not os.path.exists(initial_xml) or not os.path.exists(final_xml):
        print(f"{initial_xml} : File path  Not found ")
        return (task_path, False, 0.0)
    try:
        S_i = flappy_bird_xml_to_dict(initial_xml)
        S_f = flappy_bird_xml_to_dict(final_xml)
        target_timesteps = int(S_f["env_params"]["Timestep_Count"])
    except Exception:
        return (task_path, False, 0.0)

    start = time.time()

    for seed in seeds:
        success, path = run_dfs_survive_to_timesteps_k_sampling(
            S_i=S_i,
            target_timesteps=target_timesteps,
            env_constructor=make_env,
            hash_fn=hash_fn,
            step_fn=step_fn,
            is_crashing_fn=is_crashing_fn,
            compute_steps_fn=compute_steps_fn,
            max_depth=max_depth,
            action_space=action_space,
            b=b,
            k=k,
            seed=seed
        )
        if success:
            time_taken = round(time.time() - start, 2)
            with open(instruction_json, "w") as f:
                json.dump(path, f)
            return (task_path, True, time_taken)

    return (task_path, False, round(time.time() - start, 2))

def safe_write_to_csv(lock, file_path, row):
    with lock:
        file_exists = os.path.exists(file_path)
        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Task_Dir", "Solved", "Time_Taken"])
            writer.writerow(row)

def wrapped_process(task_path, lock, output_csv):
    result = process_task(task_path)
    safe_write_to_csv(lock, output_csv, result)
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run instruction generation on buggy tasks")
    parser.add_argument("--base_dir", type=str, required=True, help="Root directory of the tasks")
    parser.add_argument("--csv_path", type=str, required=True, help="Path to low_timestep_bugs.csv")
    parser.add_argument("--processes", type=int, default=1, help="Number of parallel processes to use")
    args = parser.parse_args()
    
    base_dir = args.base_dir
    low_timestep_csv = args.csv_path
    num_processes = args.processes

    log_file = "instruction_generation.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            
        ]
    )
    log = logging.getLogger()

    start_time = datetime.datetime.now()
    log.info("Running instruction generation in parallel with immediate logging...")
    output_csv = "heuristic_guided_search_summary.csv"
    if os.path.exists(output_csv):
        os.remove(output_csv)
    
    df = pd.read_csv(low_timestep_csv)
    df.columns = df.columns.str.strip()
    df["BugFound"] = df["BugFound"].astype(str).str.strip().str.lower()
    df = df[df["BugFound"] == "true"]

    # build a list of paths to buggy tasks based on the CSV content
    common_buggy_paths = sorted([
        os.path.join(base_dir, str(row["Seed"]), row["Environment"], f"{row['Task']}")
        for _, row in df.iterrows()
    ])
    log.info(f"Loaded {len(common_buggy_paths)} buggy task paths from {low_timestep_csv}")

    with open(low_timestep_csv, "r") as f:
        next(f)
        common_buggy_paths = [os.path.join(base_dir, line.split(",")[0].strip()) for line in f]
        common_buggy_paths = ([line.strip() for line in f if line.strip()])
        
    log.info(f"Loaded {len(common_buggy_paths)} buggy task paths from {low_timestep_csv}")
    print(f"Loaded {len(common_buggy_paths)} buggy task paths from {low_timestep_csv}")

    # process tasks in parallel 
    manager = Manager()
    lock = manager.Lock()
    args = [(task_path, lock, output_csv) for task_path in common_buggy_paths]

    with Pool(processes=min(cpu_count(), num_processes)) as pool:
        pool.starmap(wrapped_process, args)

    end_time = datetime.datetime.now()
    elapsed = end_time - start_time

    log.info(f"Instruction generation complete.")
    log.info(f"Total duration: {elapsed}")
    log.info(f"Summary saved to {output_csv}")