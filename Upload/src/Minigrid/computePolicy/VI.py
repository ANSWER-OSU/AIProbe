import numpy as np

def valueIteration(grid, gamma=0.99, epsilon=0.001):
    state_list = grid.all_states
    state_to_idx = {s: i for i, s in enumerate(state_list)}
    idx_to_state = {i: s for s, i in state_to_idx.items()}
    num_states = len(state_list)
    num_actions = len(grid.action_mapping)

    v = np.zeros(num_states)
    pi = np.zeros(num_states, dtype=int)
    q_value = np.zeros((num_states, num_actions))

    reward_cache = {}
    successors_cache = {}

    while True:
        v_new = np.copy(v)
        delta = 0
        for i, state in enumerate(state_list):
            action_values = np.zeros(num_actions)
            for a in grid.action_mapping:
                a_idx = a
                key = (state, a)

                if key not in successors_cache:
                    successors_cache[key] = grid.get_successors(state, a)
                successors, succ_probabilities = successors_cache[key]

                expected_value = sum(
                    succ_probabilities[j] * v[state_to_idx[successors[j]]] for j in range(len(successors))
                )

                if grid.is_goal(state):
                    reward = grid.get_reward(state, a)
                    action_values[a_idx] = reward
                    continue

                if key not in reward_cache:
                    reward_cache[key] = grid.get_reward(state, a)

                reward = reward_cache[key]
                action_values[a_idx] = reward + gamma * expected_value

            q_value[i] = action_values
            v_new[i] = np.max(action_values)
            pi[i] = np.argmax(action_values)
            delta = max(delta, abs(v_new[i] - v[i]))

        v = v_new
        if delta < epsilon:
            final_v = {s: v[state_to_idx[s]] for s in state_list}
            final_pi = {s: a for s, a in zip(state_list, pi)}
            return final_v, final_pi
