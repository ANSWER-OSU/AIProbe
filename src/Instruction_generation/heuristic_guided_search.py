

import random

def run_dfs_k_sampling_with_retries(S_i, S_f, hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
                                    max_depth, action_space, b=5, k=3, seed=0):
    """

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