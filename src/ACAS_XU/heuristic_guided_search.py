

from environment import env as acas_env
from tqdm import tqdm
from multiprocessing import Pool
import pandas as pd
import os
import time
from datetime import timedelta
import random
import json
from environment_parser import parse_environment
import hashlib, json, random, copy
import multiprocessing

ACTION_SPACE = [0, 1, 2, 3, 4]
MAX_DEPTH = 200
BINS = 5
K_SAMPLE = 10
TRIAL_SEEDS = [10, 23, 66, 32, 73, 881, 71203, 93572, 28514, 60497, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021, 2223]

# ----------------- Helper functions --------------------
def compute_hash(environment):
    environment_copy = copy.deepcopy(environment)
    timestep_attr = None
    for attr in environment_copy.attributes:
        if attr.name.value == "Timestep_Count":
            timestep_attr = attr.value.content
            break
    if timestep_attr is None:
        raise ValueError("Timestep_Count attribute not found in environment")
    return hashlib.sha256(json.dumps({"Timestep_Count": timestep_attr}, sort_keys=True).encode()).hexdigest()

def is_crashing(env):
    return get_simulator(env).terminated

def get_simulator(environment):
    ownship = environment.agents.agent_list[0]
    intruder = environment.objects.object_list[0]
    def get(attr_list, name):
        return float(next((attr.value.content for attr in attr_list if attr.name.value == name), 0))
    return acas_env(
        ownship_x=get(ownship.attributes, 'X'),
        ownship_y=get(ownship.attributes, 'Y'),
        ownship_theta=get(ownship.attributes, 'Theta'),
        acas_speed=get(ownship.attributes, 'Ownship_Speed'),
        intruder_x=get(intruder.attributes, 'X'),
        intruder_y=get(intruder.attributes, 'Y'),
        intruder_theta=get(intruder.attributes, 'Auto_Theta'),
        intruder_speed=get(intruder.attributes, 'Intruder_Speed'),
        setting='accurate'
    )

def step_env(env, action):
    sim = get_simulator(env)
    sim.step_proof(action)
    updated = copy.deepcopy(env)
    ownship = updated.agents.agent_list[0]
    intruder = updated.objects.object_list[0]

    for attr in ownship.attributes:
        if attr.name.value == 'X': attr.value.content = str(sim.ownship.x)
        elif attr.name.value == 'Y': attr.value.content = str(sim.ownship.y)
        elif attr.name.value == 'Theta': attr.value.content = str(sim.ownship.theta)
        elif attr.name.value == 'Ownship_Speed': attr.value.content = str(sim.ownship.speed)

    for attr in intruder.attributes:
        if attr.name.value == 'X': attr.value.content = str(sim.intruder.x)
        elif attr.name.value == 'Y': attr.value.content = str(sim.intruder.y)
        elif attr.name.value == 'Auto_Theta': attr.value.content = str(sim.intruder.theta)
        elif attr.name.value == 'Intruder_Speed': attr.value.content = str(sim.intruder.speed)

    for attr in updated.attributes:
        if attr.name.value == 'Timestep_Count':
            attr.value.content = str(int(attr.value.content) + 1)

    return updated, not sim.terminated

# def compute_steps(env1, env2, b=BINS):
#     total = 0
#     for attr in env1.attributes:
#         match = next((a for a in env2.attributes if a.name.value == attr.name.value), None)
#         if match:
#             try:
#                 total += abs(float(attr.value.content) - float(match.value.content))
#             except:
#                 continue
#     return max(1, int(total / b))

def compute_steps(env1, env2, b=BINS):
    # Extract Timestep_Count from env1
    timestep1 = None
    for attr in env1.attributes:
        if attr.name.value == "Timestep_Count":
            timestep1 = float(attr.value.content)
            break
    if timestep1 is None:
        raise ValueError("Timestep_Count not found in env1")
    
    # Extract Timestep_Count from env2
    timestep2 = None
    for attr in env2.attributes:
        if attr.name.value == "Timestep_Count":
            timestep2 = float(attr.value.content)
            break
    if timestep2 is None:
        raise ValueError("Timestep_Count not found in env2")
    
    # Compute absolute difference
    diff = abs(timestep1 - timestep2)

    # Scale by bin size
    return max(1, int(diff / b))

def run_dfs_k_sampling_with_retries(S_i, S_f, hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
                                    max_depth, action_space, b=5, k=3, seed=0):
    random.seed(seed)
    visited = set()

    def dfs_recursive(S_curr, instr, depth):
        if depth > max_depth:
            return False, []

        curr_hash = hash_fn(S_curr)
        if curr_hash == hash_fn(S_f):
            return True, instr

        if is_crashing_fn(S_curr):
            return False, []

        if curr_hash in visited:
            return False, []

        visited.add(curr_hash)

        k_sample = compute_steps_fn(S_curr, S_f, b)
        sample_actions = random.choices(action_space, k=max(k_sample, len(action_space)))

        for action in sample_actions:
            candidate_path = instr + [action]


            S_next, is_safe = step_fn(S_curr, action)
            if not is_safe:
                continue

            # Take extra steps
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

            found, path = dfs_recursive(S_temp, full_candidate_path, depth +1)
            if found:
                return True, path

        return False, []

    return dfs_recursive(S_i, [], 0)

def process_task(row_mode_seed):
    """Process a single task (one CSV row), trying seeds serially."""
    row, mode, seeds = row_mode_seed
    final_path = row['File Path']
    task_dir = os.path.dirname(final_path)
    initial_path = os.path.join(task_dir, "initialState.xml")

    pid = multiprocessing.current_process().pid
    print(f"[PID {pid}] Starting: {task_dir}")

    if not os.path.exists(initial_path) or not os.path.exists(final_path):
        print(f"[PID {pid}] Missing initial or final XML for {task_dir}")
        return (task_dir, False, 0)

    try:
        with open(initial_path) as f1, open(final_path) as f2:
            S_i = parse_environment(f1.read())
            S_f = parse_environment(f2.read())
    except Exception as e:
        print(f"[PID {pid}] Parse error in {task_dir}: {e}")
        return (task_dir, False, 0)

    task_start = time.time()
    for seed in seeds:
        if mode == "old":
            success, path, _ = run_dfs_k_sampling_with_retries(
                S_i, S_f,
                hash_fn=compute_hash,
                step_fn=step_env,
                is_crashing_fn=is_crashing,
                compute_steps_fn=compute_steps,
                max_depth=MAX_DEPTH,
                action_space=ACTION_SPACE,
                b=BINS,
                seed=seed
            )
        elif mode == "new":
            success, path = run_dfs_k_sampling_with_retries(
                S_i, S_f,
                hash_fn=compute_hash,
                step_fn=step_env,
                is_crashing_fn=is_crashing,
                compute_steps_fn=compute_steps,
                max_depth=MAX_DEPTH,
                action_space=ACTION_SPACE,
                b=BINS,
                k=K_SAMPLE,
                seed=seed
            )
        else:
            raise ValueError(f"Unknown mode {mode}")

        if success:
            elapsed = time.time() - task_start
            print(f"[PID {pid}] Solved {task_dir} in {elapsed:.2f}s")

            # 💾 Save the instruction path as JSON
            instruction_path = os.path.join(task_dir, "instruction.json")
            try:
                with open(instruction_path, 'w') as f_out:
                    json.dump({"instruction": path}, f_out, indent=2)
                print(f"[PID {pid}] Instruction saved at {instruction_path}")
            except Exception as e:
                print(f"[PID {pid}] Failed to save instruction JSON: {e}")

            return (task_dir, True, elapsed)

    elapsed = time.time() - task_start
    print(f"[PID {pid}] Unsolved {task_dir} after {elapsed:.2f}s")
    return (task_dir, False, elapsed)

def run_single_task_direct(initial_path, final_path, mode="new", seeds=None):
    """Run DFS for a single task using provided XML paths directly."""
    if seeds is None:
        seeds = TRIAL_SEEDS  # fallback to global trial seeds

    task_dir = os.path.dirname(final_path)
    fake_row = {'File Path': final_path}

    task_input = (fake_row, mode, seeds)
    result = process_task(task_input)

    task_dir, success, elapsed = result

    print("\nSingle Task Summary:")
    print(f"Task Dir   : {task_dir}")
    print(f"Solved     : {success}")
    print(f"Time Taken : {elapsed:.2f} sec")

def run_from_csv_parallel(csv_path, mode="old", processes=20):
    """Run DFS for each task in CSV in parallel."""
    df = pd.read_csv(csv_path)
    df = df[
        (df['Terminated'] == True) &
        (df['Invalid Initial State'] == False)
    ]

    df = df.sort_values(by="Seed Number", ascending=True)
    seeds_in_csv = sorted(df['Seed Number'].unique())
    print(f"Total seeds in CSV: {len(seeds_in_csv)} ➤ {seeds_in_csv}")

    overall_start = time.time()
    output_rows = []
    task_inputs = [(row, mode, TRIAL_SEEDS) for _, row in df.iterrows()]

    print(f"\nRunning {len(task_inputs)} tasks in parallel... (mode: {mode})")

    total_tasks = len(task_inputs)
    solved_so_far = 0

    with Pool(processes=processes) as pool:
        for task_dir, success, t in tqdm(pool.imap_unordered(process_task, task_inputs), total=len(task_inputs), desc="Processing tasks"):
            output_rows.append({
                "Task_Dir": task_dir,
                "Solved": success,
                "Time_Taken": round(t, 2)
            })
            if success:
                solved_so_far += 1
                

    output_csv_path = "dfs_parallel_results_model1.csv"
    pd.DataFrame(output_rows).to_csv(output_csv_path, index=False)
    print(f"\nResults saved to: {output_csv_path}")

    overall_duration = time.time() - overall_start
    print(f"\nOverall: {solved_so_far}/{total_tasks} tasks solved in ⏱ {timedelta(seconds=int(overall_duration))}")


def rerun_top10_slowest_failed_tasks(results_csv_path, mode="new", processes=20):
    """Rerun top 10 slowest failed tasks."""
    if not os.path.exists(results_csv_path):
        print(f"Results CSV not found: {results_csv_path}")
        return

    # Load previous results
    df = pd.read_csv(results_csv_path)

    # Filter only the failed ones
    failed_tasks = df[df['Solved'] == False]

    if failed_tasks.empty:
        print(f"No failed tasks to retry.")
        return

    # Sort by time taken (descending) and take top 10
    top10_failed_slow = failed_tasks.sort_values(by='Time_Taken', ascending=False).head(10)

    print(f"Retrying top {len(top10_failed_slow)} slowest failed tasks...")

    task_inputs = []
    for _, row in top10_failed_slow.iterrows():
        task_dir = row['Task_Dir']
        initial_path = os.path.join(task_dir, "initialState.xml")
        final_path = os.path.join(task_dir, "finalState.xml")
        fake_row = {
            'File Path': final_path
        }
        task_inputs.append((fake_row, mode, TRIAL_SEEDS))

    output_rows = []
    total_tasks = len(task_inputs)
    solved_so_far = 0
    overall_start = time.time()

    with Pool(processes=processes) as pool:
        for task_dir, success, t in tqdm(pool.imap_unordered(process_task, task_inputs), total=total_tasks, desc="Retrying top 10 slowest failed tasks"):
            output_rows.append({
                "Task_Dir": task_dir,
                "Solved": success,
                "Time_Taken": round(t, 2)
            })
            if success:
                solved_so_far += 1

    slow_retry_output_csv = "dfs_retry_top10_failed.csv"
    pd.DataFrame(output_rows).to_csv(slow_retry_output_csv, index=False)
    print(f"\nTop 10 retry results saved to: {slow_retry_output_csv}")

    overall_duration = time.time() - overall_start
    print(f"\nRetry finished: {solved_so_far}/{total_tasks} tasks solved in ⏱ {timedelta(seconds=int(overall_duration))}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run instruction generation in parallel.")
    parser.add_argument("--csv", type=str, required=True, help="Path to the input CSV file")
    parser.add_argument("--processes", type=int, default=4, help="Number of parallel processes to use")

    args = parser.parse_args()

    run_from_csv_parallel(args.csv, mode="new", processes=args.processes)