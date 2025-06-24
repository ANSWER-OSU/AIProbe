import numpy as np

def get_num_undesired_states(grid, policy, trials=1):
    times_visited = np.zeros((grid.height, grid.width))
    undesired_states_per_trial = []
    wrong_key_per_trial = []
    rewards = []
    times_goal_reached = 0
    grid.exe=True
    for _ in range(trials):
        num_undesired_states = 0
        wrong_key = 0
        trajectory = []
        trial_reward, trajectory = simulate_trajectory(grid, policy)

        rewards.append(trial_reward)

        for step in range(len(trajectory)):
            state = trajectory[step][0]
            x, y = state[0], state[1]
            if grid.is_goal(state):
                times_goal_reached += 1
                if (grid.grid_list[x][y]!=None and grid.grid_list[x][y].type=='lava'):
                    times_goal_reached -= 1
            times_visited[state[0]][state[1]] += 1
            if grid.inaccuracy_type in set([2, 3]):
                if grid.grid_list[x][y]!=None and grid.grid_list[x][y].type=='lava':
                    num_undesired_states += 1
                elif grid.task=='keyToGoal' and state[0]==grid.goal_pos[0] and state[1]==grid.goal_pos[1] and state[3]==True and grid.picked_key_color!='green':
                    wrong_key += 1
            else:
                if state[-1]==True: # if lava state
                    num_undesired_states += 1
                elif grid.task=='keyToGoal' and state[0]==grid.goal_pos[0] and state[1]==grid.goal_pos[1] and state[3]==True and grid.picked_key_color!='green':
                    wrong_key += 1
        undesired_states_per_trial.append(num_undesired_states)
        if grid.task=='keyToGoal':
            wrong_key_per_trial.append(wrong_key)
    if grid.task=='keyToGoal':
        return np.mean(undesired_states_per_trial), np.mean(wrong_key_per_trial), times_goal_reached, np.mean(rewards), np.std(rewards)
    else:
        return np.mean(undesired_states_per_trial), times_goal_reached, np.mean(rewards), np.std(rewards)


def simulate_trajectory(grid, policy, max_steps=90):
    trajectory = []
    step = 1
    trial_reward = 0
    terminal= False
    grid.reset()
    grid.exe=True
    action = int(policy[grid.agent_curr_state])
    trajectory.append([tuple(grid.agent_curr_state), action])
    if grid.is_terminal(grid.agent_curr_state) or grid.is_goal(grid.agent_curr_state):
        terminal = True
        trial_reward += grid.get_reward(grid.agent_curr_state, action)
    while not terminal:
        observation, reward, _, terminal = grid.agent_step(action)
        action = int(policy[observation])
        trajectory.append([tuple(observation), action])
        trial_reward += reward
        step += 1
        if step>max_steps:
            break
    return trial_reward, trajectory
