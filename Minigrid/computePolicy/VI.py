def valueIteration(grid, gamma=0.99, epsilon=0.0001):
    print('begin VI')
    v_new = {s: 0 for s in grid.all_states}
    pi_new = {s: 0 for s in grid.all_states}
    q_value = {s: [] for s in grid.all_states}
    reward_cache = {}
    successors_cache = {}

    while True:
        v = v_new.copy()
        delta = 0
        for state in grid.all_states:
            value = {}
            all_actions = list(grid.action_mapping.keys())
            for action in all_actions:
                # print('state: ', state, 'action: ', action)
                if (state, action) not in successors_cache:
                    successors_cache[(state, action)] = grid.get_successors(state, action)
                successors, succ_probabilities = successors_cache[(state, action)]
                # print('successor: ', successors)
                # input()

                state_val = sum(succ_probabilities[i] * v[successors[i]] for i in range(len(successors)))
                if grid.is_goal(state):
                    # or grid.is_terminal(state):
                    value[action] = grid.get_reward(state, action)
                    continue

                if (state, action) not in reward_cache:
                    reward_cache[(state, action)] = grid.get_reward(state, action)
                    reward = reward_cache[(state, action)]
                else:
                    reward = reward_cache[(state, action)]
                value[action] = reward + gamma * state_val

            q_value[state] = value
            v_new[state] = max(value.values())
            pi_new[state] = max(value, key=value.get)
            delta = max(delta, abs(v_new[state] - v[state]))

        if delta < epsilon:
            return v_new, pi_new
