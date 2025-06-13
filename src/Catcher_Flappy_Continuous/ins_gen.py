import os
import random
import pickle
import hashlib
from copy import deepcopy
from helper_functions import (
    create_flappy_bird_env_from_dict,
    flappy_bird_xml_to_dict,
    flappy_bird_env_to_dict,
)
import warnings
import os
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"
# === Parameters ===
initial_xml = "/initialState.xml"
final_xml = "/Volumes/External_ssd/Data/Flappy/Task_26/finalState.xml"
checkpoint_save_path = "./dfs_test_result.pkl"

max_depth = 200  # allow for longer survival paths

seeds = [
    10 , 23, 66, 32, 73, 881, 71203, 93572, 28514, 60497,
    123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021,
    2223]
action_space = [1,1,1,1,1,1,0]

#random.seed(seed)

# === Helper functions ===

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

    #return f"t={get_timestep(env)}"

def is_crashing_fn(env):
    obs, reward, terminated, truncated, info = env.step(0)
    return terminated or truncated or info.get("game_stats", {}).get("crashed", False)

def deepcopy_env(env):
    from helper_functions import flappy_bird_env_to_dict, create_flappy_bird_env_from_dict
    state = flappy_bird_env_to_dict(env)
    return create_flappy_bird_env_from_dict(state)

# === DFS Core ===
# def run_dfs_survive_to_timesteps(S_i, target_timesteps, env_constructor, step_fn, is_crashing_fn, max_depth, action_space, seed=0):
#     random.seed(seed)
#     visited = set()
#
#     def dfs(env, instr, depth):
#         curr_time = get_timestep(env)
#         if curr_time >= target_timesteps:
#             return True, instr
#         if depth > max_depth:
#             return False, []
#
#         curr_hash = hash_fn(env)
#         if curr_hash in visited or is_crashing_fn(env):
#             return False, []
#
#         visited.add(curr_hash)
#
#         for action in action_space:
#             #env_copy = deepcopy(env)
#             env_next, is_safe = step_fn(env, action)
#             if not is_safe:
#                 continue
#             found, path = dfs(env_next, instr + [action], depth + 1)
#             if found:
#                 return True, path
#
#         return False, []
#
#     env_initial = env_constructor(S_i)
#     return dfs(env_initial, [], 0)

def compute_steps_fn(env_curr, target_timesteps, b):
    """
    Returns number of steps to attempt from the current timestep to goal.
    """
    from helper_functions import flappy_bird_env_to_dict
    curr_timestep = flappy_bird_env_to_dict(env_curr).get("env_params", {}).get("Timestep_Count", 0)
    remaining = max(0, target_timesteps - curr_timestep)
    return max(remaining, b)

import random
from copy import deepcopy

# def run_dfs_survive_to_timesteps_k_sampling(S_i, target_timesteps, env_constructor, hash_fn, step_fn, is_crashing_fn,
#                                             compute_steps_fn, max_depth, action_space, b=5, k=3, seed=0):
#     """
#     DFS to reach a specific timestep (survival task) using k-sampling and binning.
#
#     Args:
#         S_i: Initial state dict
#         target_timesteps: Goal timestep (int)
#         env_constructor: builds env from dict
#         hash_fn: computes hash of env
#         step_fn: takes (env, action) and returns (new_env, is_safe)
#         is_crashing_fn: determines if env is crashing
#         compute_steps_fn: returns b
#         max_depth: max recursion depth
#         action_space: list of actions
#         b, k: DFS exploration params
#         seed: RNG seed
#
#     Returns:
#         success (bool), path (list of actions)
#     """
#     random.seed(seed)
#     visited = set()
#
#
#     def get_timestep(env):
#         from helper_functions import flappy_bird_env_to_dict
#         dic =flappy_bird_env_to_dict(env)
#         return dic['env_params']['Timestep']
#
#     # def dfs(env, instr, depth):
#     #     curr_time = get_timestep(env)
#     #     if curr_time >= target_timesteps:
#     #         return True, instr
#     #     if depth > max_depth:
#     #         return False, []
#     #
#     #     curr_hash = hash_fn(env)
#     #     if curr_hash in visited or is_crashing_fn(env):
#     #         return False, []
#     #
#     #     visited.add(curr_hash)
#     #
#     #     k_sample = compute_steps_fn(env, target_timesteps, b)
#     #     #sample_actions = random.choices(action_space, k=max(k_sample, len(action_space)))
#     #     #sample_actions = random.choices(action_space, k=k_sample)
#     #     sample_actions = random.choices(action_space, k=min(k, int(k_sample)))
#     #
#     #     # for action in sample_actions:
#     #     #     #env_next, is_safe = step_fn(deepcopy(env), action)
#     #     #     state_dict = flappy_bird_env_to_dict(env)
#     #     #     env_copy = create_flappy_bird_env_from_dict(state_dict)
#     #     #     env_next, is_safe = step_fn(env_copy, action)
#     #     #     #env_next, is_safe = step_fn(env, action)
#     #     #     if not is_safe:
#     #     #         continue
#     #     #
#     #     #     # Optional k-1 extra exploration steps
#     #     #     extra_steps = []
#     #     #     env_temp = env_next
#     #     #     for _ in range(k_sample - 1):
#     #     #         a2 = random.choice(action_space)
#     #     #         extra_steps.append(a2)
#     #     #         env_temp2, is_safe2 = step_fn(env_temp, a2)
#     #     #         if not is_safe2:
#     #     #             break
#     #     #         env_temp = env_temp2
#     #     #
#     #     #     full_path = instr + [action] + extra_steps
#     #     #     print(full_path)
#     #     #     found, path = dfs(env_temp, full_path, depth + 1)
#     #     #     if found:
#     #     #         return True, path
#     #     for action in sample_actions:
#     #         # Make ONE clone of env for this branch
#     #         env_branch = deepcopy_env(env)  # you'll write this below
#     #         path = [action]
#     #
#     #         env_next, is_safe = step_fn(env_branch, action)
#     #         if not is_safe:
#     #             continue
#     #
#     #         for _ in range(int(k_sample) - 1):
#     #             next_action = random.choice(action_space)
#     #             env_next, is_safe = step_fn(env_next, next_action)
#     #             if not is_safe:
#     #                 break
#     #             path.append(next_action)
#     #
#     #         found, result = dfs(env_next, instr + path, depth + 1)
#     #         if found:
#     #             return True, result
#     #     return False, []
#
#     # def dfs(env, instr_so_far, depth):
#     #     curr_time = get_timestep(env)
#     #     if curr_time >= target_timesteps:
#     #         return True, instr_so_far
#     #     if depth > max_depth:
#     #         return False, []
#     #
#     #     curr_hash = hash_fn(env)
#     #     if is_crashing_fn(env):
#     #         return False, []
#     #
#     #     visited.add(curr_hash)
#     #
#     #     # === 1. Replay known instruction if not exhausted
#     #     if instr_so_far:
#     #         for action in instr_so_far:
#     #             env_next, is_safe = step_fn(env, action)
#     #         # if is_safe:
#     #         #     return dfs(env_next, instr_so_far, depth + 1)
#     #         # Else: crash, fall through to normal sampling
#     #
#     #     # === 2. Continue DFS with k-sampling
#     #     k_sample = compute_steps_fn(env, target_timesteps, b)
#     #     sample_actions = random.choices(action_space, k=min(k, int(k_sample)))
#     #
#     #     for action in sample_actions:
#     #         if not instr_so_far :
#     #             env_branch = deepcopy_env(env)
#     #             env_next, is_safe = step_fn(env_branch, action)
#     #             if not is_safe:
#     #                 continue
#     #
#     #         else:
#     #             env_next = env
#     #         path = [action]
#     #         for _ in range(int(k_sample) - 1):
#     #             next_action = random.choice(action_space)
#     #             env_next, is_safe = step_fn(env_next, next_action)
#     #             if not is_safe:
#     #                 break
#     #             path.append(next_action)
#     #
#     #         found, result = dfs(env, instr_so_far + path[:-2], depth + 1)
#     #         if found:
#     #             return True, result
#     #
#     #     return False, []
#     def generate_sample_action_sequence(k):
#         """
#         Generate a sequence of random actions (0=flap, 1=no-flap).
#         No enforced glide period after flaps.
#         """
#         return [random.choice([0, 1]) for _ in range(k)]
#
#     def dfs(S_i, instr_so_far, depth):
#         # === 1. Replay known instruction if provided
#         current_env = env_constructor(S_i)
#         if instr_so_far:
#             print(f"🔁 Replaying known instruction... : {instr_so_far}")
#
#             for action in instr_so_far:
#                 env_next, is_safe = step_fn(current_env, action)
#                 #print(f"   ↪️ Action: {action}, Safe: {is_safe}")
#                 if not is_safe:
#                     print("   ❌ Replay path crashed — switching to new sampling.")
#                     break
#
#
#         curr_time = get_timestep(current_env)
#         print(f"[DFS] Depth: {depth}, Timestep: {curr_time}, Instr so far: {instr_so_far}")
#
#         if curr_time >= target_timesteps:
#             print(f"✅ Reached target timestep {target_timesteps} with path: {instr_so_far}")
#             return True, instr_so_far
#
#         if depth > max_depth:
#             print(f"⚠️ Max depth {max_depth} exceeded.")
#             return False, []
#
#
#
#
#         curr_hash = hash_fn(current_env)
#         if curr_hash in visited:
#             print("state already visited")
#             return False, []
#
#
#
#         # if is_crashing_fn(current_env):
#         #     print("💥 Crash detected at current state.")
#         #     return False, []
#
#         visited.add(curr_hash)
#
#
#             # We do not return early — fall through to sampling regardless
#
#         # === 2. Continue DFS with k-sampling
#         k_sample = compute_steps_fn(current_env, target_timesteps, b)
#         sample_actions = random.choices(action_space, k=min(k, int(k_sample)))
#         print(f"🔍 Sampling {len(sample_actions)} new actions...")
#
#         for action in sample_actions:
#             if not instr_so_far:
#                 #env_branch = deepcopy_env(current_env)
#                 env_next, is_safe = step_fn(current_env, action)
#                 print(f"   ▶️ Sampled Action: {action}, Safe: {is_safe}")
#                 if not is_safe:
#                     continue
#               # Continue from replay result
#             path = [action]
#             #new_sample_actions = generate_sample_action_sequence(int(k_sample))
#             new_sample_actions = [action] + generate_sample_action_sequence(int(k_sample) - 1)
#             for action in new_sample_actions:
#
#
#             #for _ in range(int(k_sample) - 1):
#                 #next_action = random.choice(action_space)
#                 next_action = action
#                 env_next, is_safe = step_fn(current_env, next_action)
#                 #print(f"      ↪️ Extra Step: {next_action}, Safe: {is_safe}")
#                 #curr_hash = hash_fn(env_next)
#                 if not is_safe:
#                     curr_hash = hash_fn(env_next)
#                     visited.add(curr_hash)
#                     break
#                 #curr_hash = hash_fn(env_next)
#                 #if curr_hash in visited:
#                     #break
#                 path.append(next_action)
#
#             print(f"🚀 Exploring path: {instr_so_far + path[:-1]}")
#             #found, result = dfs(S_i, instr_so_far + path[:-1], depth + 1)
#             attempt_instr = instr_so_far + path
#             backtrack_step = 1
#             while backtrack_step <= len(attempt_instr):
#                 #attempt_instr = instr_so_far + path[:-backtrack_step]
#                 found, result = dfs(S_i, attempt_instr[:-backtrack_step], depth + backtrack_step)
#                 if found:
#                     return True, result
#                 backtrack_step += 1
#             if found:
#                 return True, result
#
#         print("🔁 No valid path found at this level.")
#         return False, []
#
#
#     #env_start = env_constructor(S_i)
#     return dfs(S_i ,[], 0)
#






# def run_dfs_survive_to_timesteps_k_sampling(S_i, target_timesteps, env_constructor, hash_fn, step_fn, is_crashing_fn,
#                                             compute_steps_fn, max_depth, action_space, b=5, k=3, seed=0):
#     import random
#     from copy import deepcopy
#     from helper_functions import flappy_bird_env_to_dict
#
#     random.seed(seed)
#     visited = {}  # hash -> set of tried actions
#
#     def get_timestep(env):
#         dic = flappy_bird_env_to_dict(env)
#         return dic['env_params']['Timestep']
#
#     def generate_sample_action_sequence(k):
#         return [random.choice(action_space) for _ in range(k)]
#
#     def dfs(S_i, instr_so_far, depth):
#         current_env = env_constructor(S_i)
#         for action in instr_so_far:
#             current_env, is_safe = step_fn(current_env, action)
#             if not is_safe:
#                 return False, []
#
#         curr_time = get_timestep(current_env)
#         if curr_time >= target_timesteps:
#             return True, instr_so_far
#
#         if depth > max_depth:
#             return False, []
#
#         curr_hash = hash_fn(current_env)
#         if curr_hash in visited and len(visited[curr_hash]) == len(set(action_space)):
#             return False, []  # All actions from this state have been tried
#
#         # Init action set if not seen before
#         if curr_hash not in visited:
#             visited[curr_hash] = set()
#
#         k_sample = compute_steps_fn(current_env, target_timesteps, b)
#         sample_actions = random.choices(action_space, k=min(k, int(k_sample)))
#
#         for action in sample_actions:
#             if action in visited[curr_hash]:
#                 continue  # Skip already tried action from this state
#
#             visited[curr_hash].add(action)
#
#             env_copy = deepcopy_env(current_env)
#             env_next, is_safe = step_fn(env_copy, action)
#             if not is_safe:
#                 continue
#
#             path = [action]
#             for _ in range(int(k_sample) - 1):
#                 next_action = random.choice(action_space)
#                 env_next, is_safe = step_fn(env_next, next_action)
#                 if not is_safe:
#                     break
#                 path.append(next_action)
#
#             full_instr = instr_so_far + path
#             print(full_instr)
#             # Try backtracking from full_instr if necessary
#             for backtrack_step in range(0, len(path)):
#                 attempt_instr = full_instr[:-backtrack_step] if backtrack_step > 0 else full_instr
#                 found, result = dfs(S_i, attempt_instr, depth + 1)
#                 if found:
#                     return True, result
#
#         return False, []
#
#     return dfs(S_i, [], 0)
#



# def run_dfs_survive_to_timesteps_k_sampling(S_i, target_timesteps, env_constructor, hash_fn, step_fn, is_crashing_fn,
#                                             compute_steps_fn, max_depth, action_space, b=5, k=3, seed=0):
#     import random
#     from copy import deepcopy
#     from helper_functions import flappy_bird_env_to_dict
#
#     random.seed(seed)
#     visited = {}  # hash -> set of tried actions
#
#     def get_timestep(env):
#         dic = flappy_bird_env_to_dict(env)
#         return dic['env_params']['Timestep']
#
#     def dfs(S_curr_dict, instr_so_far, depth):
#         env = env_constructor(S_curr_dict)
#
#         # === Replay instruction so far
#         for action in instr_so_far:
#             env, is_safe = step_fn(env, action)
#             if not is_safe:
#                 return False, []
#
#         curr_time = get_timestep(env)
#         if curr_time >= target_timesteps:
#             return True, instr_so_far
#
#         if depth > max_depth:
#             return False, []
#
#         curr_hash = hash_fn(env)
#
#         if curr_hash not in visited:
#             visited[curr_hash] = set()
#
#         # If all actions from this state are exhausted, backtrack
#         if len(visited[curr_hash]) == len(action_space):
#             return False, []
#
#         # === Sample unexplored actions only
#         unexplored_actions = [a for a in action_space if a not in visited[curr_hash]]
#         random.shuffle(unexplored_actions)
#
#         for action in unexplored_actions:
#             visited[curr_hash].add(action)
#
#             env_next =deepcopy_env(env)
#             env_next, is_safe = step_fn(env_next, action)
#             if not is_safe:
#                 continue
#
#             # Optional: apply more steps (exploration)
#             path = [action]
#             for _ in range(compute_steps_fn(env, int(target_timesteps), b) - 1):
#                 next_a = random.choice(action_space)
#                 env_next, is_safe = step_fn(env_next, next_a)
#                 if not is_safe:
#                     break
#                 path.append(next_a)
#
#             full_instr = instr_so_far + path
#             print(f"length {len(full_instr)} {full_instr}")
#             # Recurse — explore with the new instruction
#             found, result = dfs(S_i, full_instr, depth + 1)
#             if found:
#                 return True, result
#
#         return False, []
#
#     return dfs(S_i, [], 0)
#

def generate_instruction(env, action_space, target_timesteps, b, compute_steps_fn, k_max):
    k_sample = min(k_max, int(compute_steps_fn(env, target_timesteps, b)))
    return tuple(random.choices(action_space, k=k_sample))


def run_dfs_survive_to_timesteps_k_sampling(S_i, target_timesteps, env_constructor, hash_fn, step_fn, is_crashing_fn,
                                            compute_steps_fn, max_depth, action_space, b=5, k=3, seed=0):
    import random
    from copy import deepcopy
    from helper_functions import flappy_bird_env_to_dict

    random.seed(seed)
    visited = {}  # state hash -> set of sampled action sequences (tuples)

    def get_timestep(env):
        dic = flappy_bird_env_to_dict(env)
        return dic['env_params']['Timestep']

    def dfs(S_curr_dict, instr_so_far, depth):
        env = env_constructor(S_curr_dict)

        # === Replay instruction so far
        for action in instr_so_far:
            env, is_safe = step_fn(env, action)
            if not is_safe:
                return False, []

        curr_time = get_timestep(env)
        if curr_time >= target_timesteps:
            return True, instr_so_far

        if depth > max_depth:
            return False, []

        curr_hash = hash_fn(env)
        if curr_hash not in visited:
            visited[curr_hash] = set()

        attempts = 0
        max_attempts = 10 * k  # cap random attempts per state

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
            print(f"[Depth {depth}] ✅ Trying path: {full_instr} → total steps: {len(full_instr)}")

            found, result = dfs(S_i, full_instr, depth + 1)
            if found:
                return True, result
        return False, []

    return dfs(S_i, [], 0)

def run_custom_action_sequence(S_i, action_sequence, env_constructor, step_fn):
    """
    Runs a custom predefined action sequence in the environment from S_i.

    Args:
        S_i: Initial state dictionary.
        action_sequence: List of actions to take (e.g., [1, 1, 0, 1, ...])
        env_constructor: Function to reconstruct the env from S_i.
        step_fn: Function to perform a step in the environment.

    Returns:
        success (bool): Whether the full sequence ran without crash.
        actual_path (list): List of actions that were actually taken.
        crash_timestep (int or None): Timestep at which crash occurred, if any.
    """
    env = env_constructor(S_i)
    actual_path = []

    for step_id, action in enumerate(action_sequence):
        env, is_safe = step_fn(env, action)
        actual_path.append(action)

        if not is_safe:
            print(f"💥 Crash occurred at step {step_id}, action={action}")
            return False, actual_path, step_id

    print("✅ Sequence completed without crashing.")
    return True, actual_path, None



# === Main run ===
if __name__ == "__main__":
    print("Loading initial and final states...")
    S_i = flappy_bird_xml_to_dict(initial_xml)
    print(f"Initial state loaded. {S_i}")
    S_f = flappy_bird_xml_to_dict(final_xml)
    target_timesteps = S_f["env_params"]["Timestep_Count"]

    print(f"Target: survive until timestep {target_timesteps}")
    print("Starting DFS exploration...")

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
            b=100,
            k=10,
            seed=seed
        )

        if success:
            print(f"✅ Path found! Length: {len(path)}")
            break
        else:
            print(f"❌ No path found.")

    custom_actions = [1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1]
# Run it
#     for x in range(10):
#         success, path, crash_time = run_custom_action_sequence(
#             S_i=S_i,
#             action_sequence=custom_actions,
#             env_constructor=make_env,
#             step_fn=step_fn
#         )


    print(f"Saving result to {checkpoint_save_path}...")
    # with open(checkpoint_save_path, "wb") as f:
    #     pickle.dump(path, f, protocol=pickle.HIGHEST_PROTOCOL)

    print("Done.")