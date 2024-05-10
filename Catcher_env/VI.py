def valueIteration(env, gamma=0.95, epsilon=1e-8, max_iters=1e12):
    all_states = env.get_states()
    v_new = {s: 0 for s in all_states}
    pi_new = {s: 0 for s in all_states}
    q_value = {s: [] for s in all_states}
    reward_cache = {}
    successors_cache = {}
    curr_iter = 0

    # while True:
    while curr_iter<=max_iters:
        curr_iter +=1
        v = v_new.copy()
        delta = 0
        for state in all_states:
            value = {}
            all_actions = list(range(env.action_space.n))
            for action in all_actions:
                if (state, action) not in successors_cache:
                    successors_cache[(state, action)] = env.get_successors(state, action)
                successor, probability = successors_cache[(state, action)]

                state_val = sum(probability[i] * v[successor[i]] for i in range(len(successor)))
                if (state, action) not in reward_cache:
                    r, _ = env.get_reward(state, action)
                    reward_cache[(state, action)] = r
                    reward = reward_cache[(state, action)]
                else:
                    reward = reward_cache[(state, action)]
                value[action] = reward + gamma * state_val

            q_value[state] = value
            v_new[state] = max(value.values())
            pi_new[state] = max(value, key=value.get)
            delta = max(delta, abs(v_new[state] - v[state]))

        if delta < epsilon:
            print('VI complete!')
            return v_new, pi_new
