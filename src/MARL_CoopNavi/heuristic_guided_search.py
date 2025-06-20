import os
import sys
import numpy as np
import copy
import random
from itertools import product
import pandas as pd
from itertools import product
from multiprocessing import Pool
import csv
import time


# Addding experiment path for make_env import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "maddpg/experiments")))
from test_aiprobe_parallely_for_buggy_models import make_env


# Helper functions 
def is_goal_reached(S_curr, S_f, tol=0.05):
    for a1, a2 in zip(S_curr.world.agents, S_f.world.agents):
        if np.linalg.norm(a1.state.p_pos - a2.state.p_pos) > tol:
            return False
    return True

def hash_fn(env):
    return tuple((round(a.state.p_pos[0], 2), round(a.state.p_pos[1], 2)) for a in env.world.agents)

def is_crashing_fn(env):
    agents = env.world.agents
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            if np.linalg.norm(agents[i].state.p_pos - agents[j].state.p_pos) < (agents[i].size + agents[j].size):
                return True
    return False

def compute_steps_fn(env_curr, env_final, b):
    dists = [np.linalg.norm(a1.state.p_pos - a2.state.p_pos)
             for a1, a2 in zip(env_curr.world.agents, env_final.world.agents)]
    return max(1, int(np.mean(dists) * b))

def step_fn(env, action, goal_positions, tolerance=1e-2):
    env_copy = copy.deepcopy(env)
    for i, agent in enumerate(env_copy.world.agents):
        if np.linalg.norm(agent.state.p_pos - goal_positions[i]) < tolerance:
            agent.action.u = np.array([0.0, 0.0])
        else:
            agent.action.u = action[i]
    env_copy.world.step()
    return env_copy, not is_crashing_fn(env_copy)

def get_scaled_actions(env, goal_positions, bins=5):
    step = 1.0 / bins
    magnitudes = [round(i * step, 4) for i in range(1, bins + 1)]
    
    agent_actions = []
    for agent, goal in zip(env.world.agents, goal_positions):
        current = agent.state.p_pos
        delta_vec = goal - current
        dist = np.linalg.norm(delta_vec)
        
        if dist < 1e-2:
            agent_actions.append([np.array([0.0, 0.0])])
        else:
            direction = delta_vec / dist
            actions = [(mag * direction) for mag in magnitudes if mag <= dist]
            actions.append(np.array([0.0, 0.0]))
            agent_actions.append(actions)
    return agent_actions

def generate_seeded_actions(env, goal_positions, bins=5, seed=0):
    print(seed)
    random.seed(seed)  # Ensure deterministic randomness
    agent_actions = []
    
    for i, (agent, goal) in enumerate(zip(env.world.agents, goal_positions)):
        current = agent.state.p_pos
        delta_vec = goal - current
        dist = np.linalg.norm(delta_vec)
        
        if dist < 1e-2:
            agent_actions.append([np.array([0.0, 0.0])])
            continue
        
        direction = delta_vec / dist
        
        # Bin ranges between 0 and 1: [0.0–0.1), [0.1–0.2), ..., [0.9–1.0)
        actions = []
        for j in range(bins):
            lower = j / bins
            upper = (j + 1) / bins
            rand_mag = random.uniform(lower, upper)
            if rand_mag <= dist:  # Only add if within reach
                action = rand_mag * direction
                actions.append(action)
            
        actions.append(np.array([0.0, 0.0]))  # stationary action so agent don not move if it reaches the goal.
        agent_actions.append(actions)
        
    return agent_actions

def get_agent_positions(env, label=""):
    print(f"\n--- Agent Positions {label} ---")
    for i, agent in enumerate(env.world.agents):
        print(f"Agent {i}: X = {agent.state.p_pos[0]:.3f}, Y = {agent.state.p_pos[1]:.3f}")
    return [agent.state.p_pos.copy() for agent in env.world.agents]

def _append_csv(seed_id, env_id, task_id, solved, used_seed, steps_or_note, runtime):
    result_path = "instruction_generation_results.csv"
    write_header = not os.path.exists(result_path)
    
    with open(result_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["SeedID", "Environment", "Task", "Solved", "UsedSeed", "StepsOrNote", "RuntimeSeconds"])
        writer.writerow([seed_id, env_id, task_id, solved, used_seed, steps_or_note, runtime])
        
def get_timestep_count(xml_path):
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        root = tree.getroot()
        attr = root.find(".//Attribute[Name[@value='Timestep_Count']]/Value")
        if attr is not None:
            return int(attr.get("value"))
    except Exception as e:
        print(f"Failed to extract timestep count: {e}")
    return None


# Heuristic guided search
def run_dfs_k_sampling_with_retries(S_i, S_f, hash_fn, step_fn, is_crashing_fn, compute_steps_fn, max_depth, b=5, k=3, seed=0, goal_positions=None):
    random.seed(seed)
    visited = set()


    def dfs_recursive(S_curr, instr, depth,seed=0):

        curr_hash = hash_fn(S_curr)
        print(f"[Depth {depth}] Visiting hash: {curr_hash}")

        if depth > max_depth:
            print(f"[Depth {depth}] Max depth exceeded.")
            return False, []

        print(f" final hash {hash_fn(S_f)}")
        if is_goal_reached(S_curr, S_f):
            print(f"[Depth {depth}] ✨ Goal reached!")
            return True, instr

        if curr_hash in visited:
            print(f"[Depth {depth}] ♻ Already visited.")
            return False, []

        visited.add(curr_hash)
        k_sample = compute_steps_fn(S_curr, S_f, b)
        print(f"[Depth {depth}] Sampling {k_sample} actions.")

        agent_action_lists = generate_seeded_actions(S_curr, goal_positions, bins=b, seed=seed)
        joint_actions = list(product(*agent_action_lists))
        sample_actions = random.sample(joint_actions, min(k_sample, len(joint_actions)))

        for idx, action in enumerate(sample_actions):
            print(f"[Depth {depth}] Trying action {idx}: {action}")
            S_next, is_safe = step_fn(S_curr, action, goal_positions)
            if not is_safe:
                continue

            extra_steps = []
            S_temp = S_next
            for _ in range(k_sample - 1):
                next_action = random.choice(sample_actions)
                extra_steps.append(next_action)
                S_temp2, is_safe2 = step_fn(S_temp, next_action, goal_positions)
                if not is_safe2:
                    break
                if is_goal_reached(S_curr, S_f):
                    print(f"[Depth {depth}] ✨ Goal reached!")
                    return True, instr + [action] + extra_steps
                S_temp = S_temp2

            full_candidate_path = instr + [action] + extra_steps
            found, path = dfs_recursive(S_temp, full_candidate_path, depth + 1,seed=seed)
            if found:
                return True, path

        print(f"[Depth {depth}]  Backtrack.")
        return False, []

    return dfs_recursive(S_i, [], 0,seed=seed)

# 
def run_instruction_generation(seed_id, env_id, task_id, model_type, scenario, base_dir, seeds):
    try:
        start_time = time.time()

        task_folder = os.path.join(base_dir, str(seed_id), env_id, task_id)
        initial_path = os.path.join(task_folder, "initialState.xml")
        final_path = os.path.join(task_folder, "finalState.xml")

        if not os.path.exists(initial_path):
            print(f"Missing: {initial_path}")
            _append_csv(seed_id, env_id, task_id, False, None, "missing_initial", 0.0)
            return (env_id, task_id, False, None, "missing_initial")

        if not os.path.exists(final_path):
            print(f"Missing: {final_path}")
            _append_csv(seed_id, env_id, task_id, False, None, "missing_final", 0.0)
            return (env_id, task_id, False, None, "missing_final")

        xml_config = {"initial": initial_path, "final": final_path}
        env = make_env(scenario, xml_config, inaccurate_model=model_type)
        
        xml_config = {"initial": final_path, "final": final_path}
        env_final = make_env(scenario, xml_config, inaccurate_model=model_type)
        goal_positions = [a.state.p_pos.copy() for a in env_final.world.agents]

        for s in seeds:
            success, path = run_dfs_k_sampling_with_retries(
                S_i=env,
                S_f=env_final,
                hash_fn=hash_fn,
                step_fn=step_fn,
                is_crashing_fn=is_crashing_fn,
                compute_steps_fn=compute_steps_fn,
                max_depth=200,
                b=100,
                k=3,
                seed=s,
                goal_positions=goal_positions
            )
            if success:
                runtime = round(time.time() - start_time, 3)
                timestep_count = get_timestep_count(final_path)
                
                if timestep_count is not None and timestep_count < len(path):
                    print(f"ath too long ({len(path)}) vs Timestep_Count ({timestep_count}) — invalid solution")
                    _append_csv(seed_id, env_id, task_id, False, s, "too_long", runtime)
                    return (env_id, task_id, False, s, "too_long")
                    continue
                
                print(f"{env_id}/{task_id} solved with seed {s} in {runtime} seconds")
                
                instruction_path = os.path.join(task_folder, "instruction.json")
                try:
                    import json
                    json.dump([a.tolist() for a in path], open(instruction_path, "w"), indent=2)
                    print(f"Instruction saved to {instruction_path}")
                except Exception as save_err:
                    print(f"Failed to save instruction: {save_err}")
                    
                _append_csv(seed_id, env_id, task_id, True, s, len(path), runtime)
                return (env_id, task_id, True, s, len(path))
            
            
        runtime = round(time.time() - start_time, 3)
        print(f"{env_id}/{task_id} unsolved in {runtime} seconds")
        _append_csv(seed_id, env_id, task_id, False, None, None, runtime)
        return (env_id, task_id, False, None, None)

    except Exception as e:
        runtime = round(time.time() - start_time, 3)
        print(f"Exception in {env_id}/{task_id}: {e}")
        _append_csv(seed_id, env_id, task_id, False, None, str(e), runtime)
        return (env_id, task_id, False, None, str(e))

# Main function
def main():
    
    parser = argparse.ArgumentParser(description="Run instruction generation.")
    parser.add_argument("--config_csv", type=str, required=True, help="Path to the config CSV file")
    parser.add_argument("--base_dir", type=str, required=True, help="Base directory of task folders")
    parser.add_argument("--num_workers", type=int, default=2, help="Number of parallel processes")
    args = parser.parse_args()
    config_csv = args.config_csv
    base_dir = args.base_dir
    model_type = "accurate"
    scenario = "simple_spread"
    seeds = [10, 23, 66, 32, 73, 881, 71203, 93572, 28514, 60497,123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021, 2223]
    num_workers = args.num_workers

    df = pd.read_csv(config_csv)
    bug_df = df[df["BugFound"] == True]  # Or remove this filter to process all

    task_args = [
        (int(row["Seed"]), row["Environment"], row["Task"], model_type, scenario, base_dir, seeds)
        for _, row in bug_df.iterrows()
    ]

    print(f"Launching {len(task_args)} parallel instruction generation tasks")

    from multiprocessing import Pool
    with Pool(processes=num_workers) as pool:
        results = pool.starmap(run_instruction_generation, task_args)

    # Print/save results
    for env_id, task_id, success, used_seed, steps in results:
        print(f"{env_id}/{task_id}, Seed: {used_seed}, Steps: {steps}")

if __name__ == "__main__":
    main()
    