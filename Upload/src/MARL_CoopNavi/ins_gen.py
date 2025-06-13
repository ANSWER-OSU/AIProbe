import os
import sys
import random
import numpy as np
import pickle

sys.path.append(os.path.abspath("/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/multiagent_particle_envs"))
sys.path.append(os.path.abspath("maddpg/experiments"))
sys.path.append(os.path.abspath("/scratch/projects/AIProbe-Main/AIProbe/Instruction_generation"))

from test_aiprobe_parallely_for_buggy_models import make_env
#from run_dfs_k_sampling_with_retries import run_dfs_k_sampling_with_retries


import os
import sys
import argparse
import numpy as np
import pickle
import time
import random

sys.path.append(os.path.abspath("/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/multiagent_particle_envs"))
from test_aiprobe_parallely_for_buggy_models import make_env, parse_args

#from run_dfs_k_sampling_with_retries import run_dfs_k_sampling_with_retries


def step_fn(env, action):
    try:
        obs, _, _, _ = env.step([action for _ in env.world.agents])
        return env, True
    except:
        return env, False



def run_dfs_k_sampling_with_retries(S_i, S_f, hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
                                    max_depth, action_space, b=5, k=3, seed=0):
    """
    Core DFS with k-sampling retries.

    Args:
        S_i: Initial environment state
        S_f: Final (goal) environment state
        hash_fn: Function to compute a hash of environment
        step_fn: Function to take a step in environment given an action
        is_crashing_fn: Function to detect if a state is crashing
        compute_steps_fn: Function to compute steps/distance from current to goal
        max_depth: Maximum recursion depth
        action_space: List of possible actions
        b: Bin size for step estimation
        k: k-sampling parameter
        seed: Random seed for reproducibility

    Returns:
        (success_flag, path_list)
    """
    random.seed(seed)
    visited = set()

    def dfs_recursive(S_curr, instr, depth):
        input()
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

            full_candidate_path = instr + [action] + extra_steps
            found, path = dfs_recursive(S_temp, full_candidate_path, depth + 1)
            if found:
                return True, path

        return False, []

    return dfs_recursive(S_i, [], 0)


def hash_fn(env):
    """Hash based on agents' absolute positions."""
    return tuple((round(agent.state.p_pos[0], 3), round(agent.state.p_pos[1], 3)) for agent in env.world.agents)


def is_crashing_fn(env):
    world = env.world
    for i, agent in enumerate(world.agents):
        for j, other in enumerate(world.agents):
            if i < j:
                if np.linalg.norm(agent.state.p_pos - other.state.p_pos) < (agent.size + other.size):
                    return True
    return False


def compute_steps_fn(env, goal_env, b):
    current = [agent.state.p_pos for agent in env.world.agents]
    goal = [agent.state.p_pos for agent in goal_env.world.agents]
    dist = np.mean([np.linalg.norm(c - g) for c, g in zip(current, goal)])
    return int(max(1, min(b, dist * 5)))


def generate_instruction(xml_config, action_space, args):
    S_i = make_env(args.scenario, {"initial": xml_config["initial"], "final": xml_config["final"]})
    print(hash_fn(S_i))
    S_f = make_env(args.scenario, {"initial": xml_config["final"], "final": xml_config["final"]})
    print(hash_fn(S_f))


    print(f"🔍 Running DFS for {xml_config['initial']}")
    success, path = run_dfs_k_sampling_with_retries(
        S_i, S_f,
        hash_fn=hash_fn,
        step_fn=step_fn,
        is_crashing_fn=is_crashing_fn,
        compute_steps_fn=compute_steps_fn,
        max_depth=args.max_episode_len,
        action_space=action_space,
        b=5, k=3, seed=42
    )

    result_dir = os.path.dirname(xml_config["initial"])
    with open(os.path.join(result_dir, "dfs_success.pkl"), "wb") as f:
        pickle.dump({"success": success, "path_len": len(path), "path": path}, f)

    print(f"✅ Success: {success} | Path length: {len(path)}")
    return success


def main():
    args = parse_args()

    xml_config = {
        "initial": "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/100_Bin/534/Env_1/Task_2/initialState.xml",
        "final": "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/100_Bin/534/Env_1/Task_2/finalState.xml"
    }

    bins = np.linspace(-1.0, 1.0, 3)
    action_space = [np.array(action, dtype=np.float32) for action in itertools.product(bins, repeat=2)]

    generate_instruction(xml_config, action_space, args)


if __name__ == "__main__":
    import itertools
    main()