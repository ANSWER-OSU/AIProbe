import numpy as np

def get_num_undesired_states(grid, policy, trials=50):
    times_visited = np.zeros((grid.height, grid.width))
    undesired_states_per_trial = []
    rewards = []
    times_goal_reached = 0
    for _ in range(trials):
        num_undesired_states = 0
        trajectory = []
        trial_reward, trajectory = simulate_trajectory(grid, policy)
        # print(trajectory)

        rewards.append(trial_reward)

        for step in range(len(trajectory)):
            state = trajectory[step][0]
            if grid.is_goal(state):
                times_goal_reached += 1
            times_visited[state[0]][state[1]] += 1
            if state[3]==True: # if lava state
                num_undesired_states += 1
        undesired_states_per_trial.append(num_undesired_states)
    return np.sum(undesired_states_per_trial), times_goal_reached, np.mean(rewards), np.std(rewards)


def simulate_trajectory(grid, policy, max_steps=90):
    trajectory = []
    step = 1
    trial_reward = 0
    terminal= False
    grid.reset()
    action = int(policy[grid.agent_curr_state])
    trajectory.append([tuple(grid.agent_curr_state), action])
    observation, reward, _, terminal = grid.step(action)
    action = int(policy[observation])
    trajectory.append([tuple(observation), action])
    trial_reward += reward
    while not terminal:
        observation, reward, _, terminal = grid.step(action)
        action = int(policy[observation])
        trajectory.append([tuple(observation), action])
        trial_reward += reward
        step += 1
        if step>max_steps:
            break
    return trial_reward, trajectory
