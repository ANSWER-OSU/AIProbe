import random

def dfs(S_curr, S_goal, hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
        max_depth=20, depth=0, visited=None, instr_seq=None,
        action_space=None, b=5, retries=5):

    # Set random seed only once
    if depth == 0:
        random.seed(42)

    if visited is None:
        visited = set()
    if instr_seq is None:
        instr_seq = []

    if depth > max_depth:
        #print(f"🚫 Max depth {max_depth} reached at depth {depth}")
        #print(f"🧱 Total visited states: {len(visited)}")
        return False, "", visited

    curr_hash = hash_fn(S_curr)
    if curr_hash in visited:
        #print(f"🔁 Already visited state at depth {depth}")
        return False, "", visited

    if is_crashing_fn(S_curr):
        #print(f"💥 Crashing state detected at depth {depth}")
        return False, "", visited

    visited.add(curr_hash)

    if curr_hash == hash_fn(S_goal):
       # print("🎯 Goal reached!")
        #print("✅ Path:", instr_seq)
       # print("🔍 Total visited states:", len(visited))
        return True, instr_seq, visited

    k = compute_steps_fn(S_curr, S_goal, b)
   # print(f"🔢 k = {k} (steps to sample) at depth {depth}")

    for attempt in range(retries):  # Try different random sequences
        temp_env = S_curr
        temp_seq = instr_seq.copy()
        crashed = False

        actions = random.choices(action_space, k=k)
       # print(f"🎲 Attempt {attempt+1}/{retries} — Sampled actions: {actions}")

        for step_idx in range(k):
            available_actions = action_space.copy()
            success_in_step = False

            while available_actions:
                action = random.choice(available_actions)
                available_actions.remove(action)

                temp_env_candidate, is_safe = step_fn(temp_env, action)
                temp_step_hash = hash_fn(temp_env_candidate)

                if not is_safe or is_crashing_fn(temp_env_candidate):
                   # print(f"💥 Crash at step {step_idx + 1} with action '{action}' — trying alternative...")
                    continue

                if temp_step_hash in visited:
                   # print(f"🔁 State already visited after action '{action}' — trying alternative...")
                    continue

                # Valid action found
                temp_env = temp_env_candidate
                temp_seq.append(action)
                success_in_step = True
                break

            if not success_in_step:
               # print(f"⛔ All actions failed at step {step_idx + 1} — abandoning sequence")
                crashed = True
                break
        if crashed:
            continue  # Try a new sequence

        temp_hash = hash_fn(temp_env)
        if temp_hash in visited:
            #print(f"🔁 Resulting state already visited — skipping")
            continue

        if temp_hash == hash_fn(S_goal):
            #print("🎯 Goal reached at end of sequence!")
           # print("✅ Path:", temp_seq)
           # print("🔍 Total visited states:", len(visited))
            return True, temp_seq, visited

        success, path, visited = dfs(
            temp_env, S_goal,
            hash_fn, step_fn, is_crashing_fn, compute_steps_fn,
            max_depth, depth + 1,
            visited, temp_seq, action_space, b, retries
        )

        if success:
           # print(f"↪️ Recursive success from depth {depth}")
           # print("✅ Path:", path)
           # print("🔍 Total visited states:", len(visited))
            return True, path, visited

    #print(f"❌ No path found at depth {depth} after {retries} retries")
   # print("🧱 Explored states so far:", len(visited))
    return False, "", visited