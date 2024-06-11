import numpy as np

def get_num_undesired_states(env, policy, trials=50, is_flappy=False):
    all_states = env.get_states()
    times_visited = {s: 0 for s in all_states}
    rewards = []
    num_good_fruits_per_trial, num_bad_fruits_per_trial = [], []
    num_past_pipe_per_trial, num_crashes_per_trial = [], []
    times_goal_reached = 0
    trajectory_lengths = []
    for i in range(trials):
        print('trial: ', i)
        num_bad_fruits, num_good_fruits = 0, 0
        past_pipe, crashes = 0, 0
        trajectory = []
        trial_reward, trajectory = simulate_trajectory(env, policy)
        print('traj:\n', trajectory, '\trial reward: ', trial_reward)
        input()
        rewards.append(trial_reward)

        trajectory_lengths.append(len(trajectory))

        if is_flappy:
            if env.is_goal(env.score):
                    times_goal_reached += 1
        for step in range(len(trajectory)):
            state = trajectory[step][0]
            # print('state: ', state)

            times_visited[state] += 1
            if is_flappy:
                if env.is_past_pipe(state):
                    print('crossed a pipe! state --> ', state)
                    past_pipe += 1
                if env.is_crash(state):
                    print('CRASHED :( state --> ', state)
                    crashes += 1
            else:
                if env.is_goal(env.score):
                    times_goal_reached += 1
                if env.is_bad_fruit(state):
                    num_bad_fruits += 1
                elif env.is_good_fruit(state):
                    num_good_fruits += 1
            # print('good fruits: ', num_good_fruits, 'bad fruits: ', num_bad_fruits)
            # print('env.score: ', env.score)
        # input()
        if is_flappy:
            num_past_pipe_per_trial.append(past_pipe)
            num_crashes_per_trial.append(crashes)
        else:
            num_bad_fruits_per_trial.append(num_bad_fruits)
            num_good_fruits_per_trial.append(num_good_fruits)
    if is_flappy:
        return num_past_pipe_per_trial, num_crashes_per_trial, np.mean(rewards), np.std(rewards), trajectory_lengths, times_goal_reached
    else:
        return num_good_fruits_per_trial, num_bad_fruits_per_trial, np.mean(rewards), np.std(rewards), trajectory_lengths


def simulate_trajectory(env, policy):
    trajectory = []
    trial_reward = 0
    terminal= False
    env.reset()
    # print('start state: ', env.agent_curr_state)
    action = int(policy[env.agent_curr_state])
    trajectory.append([tuple(env.agent_curr_state), action])
    observation, reward, _, terminal, obj_type = env.step(action)
    # print('state: ', observation, 'reward: ', reward, 'terminal: ', terminal, 'fruit type: ', 'bad' if fruit_type==0 else 'good')
    action = int(policy[observation])
    trajectory.append([tuple(observation), action])
    trial_reward += reward
    while not terminal:
        observation, reward, _, terminal, obj_type = env.step(action)
        # print('state: ', observation, 'reward: ', reward, 'terminal: ', terminal, 'fruit type: ', 'bad' if fruit_type==0 else 'good')
        # print('num lives: ', env.num_lives, 'lives left: ', env.lives_left)
        # input()
        action = int(policy[observation])
        trajectory.append([tuple(observation), action])
        trial_reward += reward
        if terminal:
            break
    return trial_reward, trajectory
