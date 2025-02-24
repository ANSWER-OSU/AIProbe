import os
import gymnasium as gym
import torch
import numpy as np
import torch.nn as nn
from helper_functions import create_flappy_bird_env_from_xml

# Load the trained PPO model
class Agent(nn.Module):
    def __init__(self, envs):
        super().__init__()
        self.critic = nn.Sequential(
            nn.Linear(np.array(envs.observation_space.shape).prod(), 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 1),
        )
        self.actor = nn.Sequential(
            nn.Linear(np.array(envs.observation_space.shape).prod(), 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, envs.action_space.n),
        )

    def get_action(self, x):
        logits = self.actor(x)
        probs = torch.distributions.Categorical(logits=logits)
        action = probs.sample()
        return action


def test_ppo(agent, env, env_id, num_episodes=10, render=False):
    """
    Function to test the trained PPO agent in the environment.

    Args:
        agent: The trained agent (neural network).
        env: The environment to test the agent in.
        num_episodes: Number of episodes to run for testing.
        render: If True, render the environment during testing.
    """
    total_good_fruits_caught = []
    total_bad_fruits_caught = []
    total_good_fruits_missed = []
    total_pipes_passed, total_crashes = [], []
    total_special_pipes_high = []
    total_normal_pipes_high = []
    for episode in range(num_episodes):
        obs, _ = env.reset(seed=42)
        obs = torch.tensor(obs).float()
        done = False
        total_reward = 0
        if env_id=='Catcher':
            good_fruit_caught, missed_good_fruit, bad_fruit_caught = 0, 0, 0
        else:
            pipes_passed, crashes = 0, 0
            special_pipes_high, normal_pipe_high = 0, 0

        while not done:
            with torch.no_grad():
                action = agent.get_action(obs)
            next_obs, reward, terminated, truncated, info = env.step(action.item())
            game_stats = info.get('game_stats', None)
            if env_id=='Catcher':
                if game_stats['caught_good_fruit']:
                    good_fruit_caught+=1
                elif game_stats['missed_good_fruit']:
                    missed_good_fruit+=1
                elif game_stats['caught_bad_fruit']:
                    bad_fruit_caught+=1
            else:
                if game_stats['pipe_passed']:
                    pipes_passed+=1
                elif game_stats['crashed']:
                    crashes+=1
                elif game_stats['special_pipe_high']:
                    special_pipes_high+=1
                elif game_stats['normal_pipe_high']:
                    normal_pipe_high+=1
            print('observation: ', next_obs, 'reward: ', reward)
            obs = torch.tensor(next_obs).float()

            total_reward += reward
            # if render:
            #     env.render()
            # input()
            done = terminated

        print(f"Episode {episode + 1} - Total Reward: {total_reward}")
        if env_id=='Catcher':
            total_good_fruits_caught.append(good_fruit_caught)
            total_bad_fruits_caught.append(bad_fruit_caught)
            total_good_fruits_missed.append(missed_good_fruit)
        else:
            total_pipes_passed.append(pipes_passed)
            total_crashes.append(crashes)
            total_special_pipes_high.append(special_pipes_high)
            total_normal_pipes_high.append(normal_pipe_high)
    print(len(total_bad_fruits_caught))
    if env_id=='Catcher':
        print('Average # good fruits caught: ', np.mean(np.asarray(total_good_fruits_caught)), np.std(np.asarray(total_good_fruits_caught)))
        print('Average # bad fruits caught: ', np.mean(np.asarray(total_bad_fruits_caught)), np.std(np.asarray(total_bad_fruits_caught)))
        print('Average # good fruits missed: ', np.mean(np.asarray(total_good_fruits_missed)), np.std(np.asarray(total_good_fruits_missed)))
    else:
        print('Average # pipes passed: ', np.mean(np.asarray(total_pipes_passed)), np.std(np.asarray(total_pipes_passed)))
        print('Average # crashes: ', np.mean(np.asarray(total_crashes)), np.std(np.asarray(total_crashes)))
        print('Average # high near special pipes: ', np.mean(np.asarray(total_special_pipes_high)), np.std(np.asarray(total_special_pipes_high)))
        print('Average # high near normal pipes: ', np.mean(np.asarray(total_normal_pipes_high)), np.std(np.asarray(total_normal_pipes_high)))
    env.close()


if __name__ == "__main__":
    # Load the environment
    # register(
    #                     id='FlappyBird',  # Unique ID for the environment
    #                     entry_point='initialize_flappyBird:FlappyBirdEnv',  # Path to the CatcherEnv class
    #                     max_episode_steps=100000000,  # Maximum number of steps in an episode
    #                 )
    # env = gym.make('FlappyBird',
    #                normalize=False,
    #                display=False,
    #                random_pipe_color=True,
    #                pipe_color='red'
    #                )
    xml_file = '/home/projects/AIProbe/Test_Enviroment/FlappyBird/Bin5/Result_Flappybird_534/Env_1/Task_1/initialState.xml'
    env = create_flappy_bird_env_from_xml(xml_file, modify_env=False)

    # Load the trained model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = Agent(env).to(device)
    checkpoint_path = "wandb/flappyBird/run_inacc_state_acc_r/files/flappy_agent_inacc_state_acc_r_2.pt"  # Path to the saved model checkpoint
    # checkpoint_path = "wandb/run-20241022_015045-3738pp82/files/flappy_agent_acc_state_inacc_r.pt"  # Path to the saved model checkpoint
    agent.load_state_dict(torch.load(checkpoint_path, map_location=device))
    agent.eval()  # Set the agent to evaluation mode

    # Test the agent
    test_ppo(agent, env, 'FlappyBird', num_episodes=100, render=True)  # Run for 10 episodes with rendering
