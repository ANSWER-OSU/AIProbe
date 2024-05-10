import numpy as np

def get_num_undesired_states(env, policy, trials=50):
    all_states = env.get_states()
    times_visited = {s: 0 for s in all_states}
    rewards = []
    num_good_fruits_per_trial, num_bad_fruits_per_trial = [], []
    times_goal_reached = 0
    start_states = []
    for i in range(trials):
        # print('trial: ', i)
        num_bad_fruits, num_good_fruits = 0, 0
        trajectory = []
        trial_reward, trajectory = simulate_trajectory(env, policy)
        rewards.append(trial_reward)

        start_states.append(trajectory[0])
        for step in range(len(trajectory)):
            state = trajectory[step][0]
            # print('state: ', state)

            if env.is_goal(env.score):
                times_goal_reached += 1
            times_visited[state] += 1
            if env.is_bad_fruit(state):
                num_bad_fruits += 1
            elif env.is_good_fruit(state):
                num_good_fruits += 1
            # print('good fruits: ', num_good_fruits, 'bad fruits: ', num_bad_fruits)
        # input()
        num_bad_fruits_per_trial.append(num_bad_fruits)
        num_good_fruits_per_trial.append(num_good_fruits)
    return num_good_fruits_per_trial, num_bad_fruits_per_trial, np.mean(rewards), np.std(rewards), start_states


def simulate_trajectory(env, policy):
    trajectory = []
    trial_reward = 0
    terminal= False
    env.reset()
    action = int(policy[env.agent_curr_state])
    trajectory.append([tuple(env.agent_curr_state), action])
    observation, reward, _, terminal, fruit_type = env.step(action)
    # print('state: ', observation, 'reward: ', reward, 'terminal: ', terminal, 'fruit type: ', 'bad' if fruit_type==0 else 'good')
    action = int(policy[observation])
    trajectory.append([tuple(observation), action])
    trial_reward += reward
    while not terminal:
        observation, reward, _, terminal, fruit_type = env.step(action)
        # print('state: ', observation, 'reward: ', reward, 'terminal: ', terminal, 'fruit type: ', 'bad' if fruit_type==0 else 'good')
        # print('num lives: ', env.num_lives, 'lives left: ', env.lives_left)
        # input()
        action = int(policy[observation])
        trajectory.append([tuple(observation), action])
        trial_reward += reward
        if terminal:
            break
    return trial_reward, trajectory
