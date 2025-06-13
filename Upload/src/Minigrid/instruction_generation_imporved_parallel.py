ximport os
import time
import json
import hashlib
import copy
import random
import pandas as pd
from multiprocessing import Pool
from tqdm import tqdm
from MinigridWrapper import run_minigrid_with_single_action
from enviroment_parser import parse_xml_to_dict
import MinigridEnv

# Constants
ACTION_SPACE = ["left", "right", "forward"]
MAX_DEPTH = 200
BINS = 1
K_SAMPLE = 6
TRIAL_SEEDS = [
    10, 23, 66, 32, 73, 881, 71203, 93572, 28514, 60497]
    #123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021, 2223]

# ---- Basic helper functions ----
def compute_hash(env):
    env_dict = json.loads(json.dumps(env, default=lambda o: getattr(o, '__dict__', str(o))))
    agent_attrs = env_dict['Agents']['AgentList'][0]['Attributes']
    attr_map = {attr['Name']['Value']: attr['Value']['Content'] for attr in agent_attrs}
    x = attr_map.get('X')
    y = attr_map.get('Y')
    hash_input = {"X": float(x), "Y": float(y)}
    return hashlib.sha256(json.dumps(hash_input, sort_keys=True).encode()).hexdigest()

def step_fn(env, environment_data, action):
    env_copy = copy.deepcopy(env)  
    updated_env_data, terminated = run_minigrid_with_single_action(env_copy, environment_data, action)
    return updated_env_data, not terminated

def compute_steps(env1, env2, b=BINS):
    def get_agent_info(env_dict):
        attr_list = env_dict['Agents']['AgentList'][0]['Attributes']
        result = {}
        for attr in attr_list:
            name = attr['Name']['Value']
            value = int(attr['Value']['Content'])
            constraint = attr.get('Constraint', {})
            min_val = int(constraint.get('Min', 0))
            max_val = int(constraint.get('Max', 100))
            result[name] = {
                'value': value,
                'min': min_val,
                'max': max_val
            }
        return result
    
    def bin_value(val, min_val, max_val, bins):
        if max_val == min_val:
            return 0
        bin_size = (max_val - min_val) / bins
        return int((val - min_val) / bin_size)
    
    info1 = get_agent_info(env1)
    info2 = get_agent_info(env2)
    
    x1 = info1['X']['value']
    x2 = info2['X']['value']
    y1 = info1['Y']['value']
    y2 = info2['Y']['value']
    
    x_min = info1['X']['min']
    x_max = info1['X']['max']
    y_min = info1['Y']['min']
    y_max = info1['Y']['max']

        
    bx1 = bin_value(x1, x_min, x_max, bins)
    by1 = bin_value(y1, y_min, y_max, bins)
    bx2 = bin_value(x2, x_min, x_max, bins)
    by2 = bin_value(y2, y_min, y_max, bins)
    
    return max(1, (abs(bx1 - bx2) + abs(by1 - by2)))

def is_crashing(env, environment_data):
    # Trying a dummy action ("left") to detect if crashing
    env_copy = copy.deepcopy(env)
    updated_env_data, terminated = run_minigrid_with_single_action(env_copy, environment_data, "left")
    return terminated





# ----- k-sampling based DFS -----
def run_dfs_k_sampling_with_retries(S_i, S_f, hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
                                    max_depth, action_space, b=5, k=10, seed=0):
    random.seed(seed)
    visited = set()

    def dfs_recursive(S_curr, instr, depth):
        env_curr, env_data_curr = S_curr

        if depth > max_depth:
            return False, []

        curr_hash = hash_fn(env_data_curr)
        if curr_hash == hash_fn(S_f):
            if is_crashing_fn(env_curr, env_data_curr) :
                return False, []
            else:
                return True, instr

        if is_crashing_fn(env_curr, env_data_curr) or curr_hash in visited:
            return False, []

        visited.add(curr_hash)

        k_sample = compute_steps_fn(env_data_curr, S_f, b)
        sample_actions = random.choices(action_space, k=max(k_sample, len(action_space)))

        for action in sample_actions:
            candidate_path = instr + [action]
            S_next_data, is_safe = step_fn(env_curr, env_data_curr, action)
            if not is_safe:
                continue

            # Create a new environment for this branch
            env_copy = copy.deepcopy(env_curr)

            found, path = dfs_recursive((env_copy, S_next_data), candidate_path, depth + 1)
            if found:
                return True, path

        return False, []

    return dfs_recursive(S_i, [], 0)

# ------------------------
# Single task solver (serial seeds)
# ------------------------
def solve_single_task(task_info):
    initial_path, final_path, mode = task_info

    try:
        S_i = parse_xml_to_dict(initial_path)
        S_f = parse_xml_to_dict(final_path)
    except Exception as e:
        print(f"⚠️ Error parsing {initial_path}: {e}")
        return {"Task_Dir": initial_path, "Solved": False, "Time_Taken": 0.0}

    try:
        # Create env ONCE here
        env = MinigridEnv.CustomMiniGridEnv(environment_data=S_i)
        env.reset()
    except Exception as e:
        print(f"⚠️ Error initializing environment for {initial_path}: {e}")
        return {"Task_Dir": initial_path, "Solved": False, "Time_Taken": 0.0}

    start_time = time.time()

    for seed in TRIAL_SEEDS:
        random.seed(seed)

        success, path = run_dfs_k_sampling_with_retries(
            (env, S_i),  # Pass (env, environment_data) tuple
            S_f,
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

        if success and path:
            elapsed = time.time() - start_time
            print(f"✅ {initial_path} solved with seed {seed} in {elapsed:.2f} sec")

            instruction_save_path = os.path.join(os.path.dirname(initial_path), "instruction.json")
            try:
                with open(instruction_save_path, 'w') as f_out:
                    json.dump({"instruction": path}, f_out, indent=2)
                print(f"💾 Instruction saved to {instruction_save_path}")
            except Exception as e:
                print(f"⚠️ Failed to save instruction JSON: {e}")

            env.close()
            return {"Task_Dir": initial_path, "Solved": True, "Time_Taken": round(elapsed, 2)}

    elapsed = time.time() - start_time
    print(f"❌ {initial_path} unsolved after {elapsed:.2f} sec")
    env.close()
    return {"Task_Dir": initial_path, "Solved": False, "Time_Taken": round(elapsed, 2)}
# ------------------------
# Main runner
# ------------------------
import time  # Add this at the top

def run_from_csv(csv_path, base_dir, mode="new"):
    start_time = time.time()  # Start timing
    csv_dir = os.path.dirname(csv_path)
    

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    print("Available columns:", df.columns.tolist())

    df_filtered = df[(df['#Lava'] == 1) & (df['#AgentToGoal'] == 0) & (df['#Reward'] == 0)]
    print(f"🎯 Total tasks to try: {len(df_filtered)}")

    task_info_list = []


    for _, row in df_filtered.iterrows():
        seed = int(row['Seed'])
        env = int(row['Env#'])
        task = int(row['Task#'])

        initial_path = os.path.join(base_dir, f"{seed}", f"Env_{env}", f"Task_{task}", "initialState.xml")
        final_path = os.path.join(base_dir, f"{seed}", f"Env_{env}", f"Task_{task}", "finalState.xml")

        task_info_list.append((initial_path, final_path, mode))

    print(task_info_list[1])
    with Pool(37) as pool:
        results = list(tqdm(pool.imap_unordered(solve_single_task, task_info_list), total=len(task_info_list)))

    output_df = pd.DataFrame(results)
    output_path = f"{csv_dir}/dfs_minigrid_parallel_task_serial_seeds.csv"
    output_df.to_csv(output_path, index=False)

    total_solved = output_df['Solved'].sum()
    print(f"\n🏁 Done. {total_solved}/{len(output_df)} tasks solved.")
    print(f"📝 Results saved to: {output_path}")

    end_time = time.time()  # End timing
    elapsed_time = end_time - start_time

    print(f"⏱️ Total time taken: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
# ------------------------
# Run Example
# ------------------------
    if __name__ == "__main__":
        csv_paths = [
            "/scratch/projects/AIProbe-Main/AIProbe/Minigrid/accurate_reward_inaccurate_state_rep_results.csv",
            #"/scratch/projects/AIProbe-Main/AIProbe/Minigrid/computePolicy/results_for_fuzzer_gen_configs/Seed_74321/_accurate_reward_accurate_state_rep_results.csv",
            #"/scratch/projects/AIProbe-Main/AIProbe/Minigrid/computePolicy/results_for_fuzzer_gen_configs/Seed_90785/_accurate_reward_accurate_state_rep_results.csv",
            #"/scratch/projects/AIProbe-Main/AIProbe/Minigrid/computePolicy/results_for_fuzzer_gen_configs/Seed_98765/_accurate_reward_accurate_state_rep_results.csv",
            
        ]
        
    base_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50/100_Bin"
    mode = "new"

    for csv_path in csv_paths:
        print(f"Running: {csv_path}")
        run_from_csv(csv_path=csv_path, base_dir=base_dir, mode=mode)

#initial_path = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50/100_Bin/11223/Env_1/Task_1/initialState.xml"
#final_path = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50/100_Bin/11223/Env_1/Task_1/finalState.xml"
#
#
#result = solve_single_task((initial_path, final_path, "new"))
#
#print("\n=== Result ===")
#print(result)