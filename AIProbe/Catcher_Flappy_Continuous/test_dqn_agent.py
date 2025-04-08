import os
import gymnasium as gym
from gymnasium.envs.registration import register
import torch
import numpy as np
import torch.nn as nn
from initialize_flappyBird import FlappyBirdEnv
from initialize_catcher import CatcherEnv

# Load the trained DQN model
class CatcherAgent(nn.Module):
    def __init__(self, envs):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(np.array(envs.observation_space.shape).prod(), 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, envs.action_space.n),
        )

    def get_action(self, x, epsilon=0.05):
        q_values = self.network(x)
        action = torch.argmax(q_values, dim=1).item()
        return action

class FlappyBirdAgent(nn.Module):
    def __init__(self, envs):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(np.array(envs.observation_space.shape).prod(), 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, env.action_space.n),
        )

    def get_action(self, x, epsilon=0.05):
        q_values = self.network(x)
        action = torch.argmax(q_values, dim=1).item()
        return action


def test_dqn(agent, env, env_id, num_episodes=10, render=False):
    """
    Function to test the trained DQN agent in the environment.

    Args:
        agent: The trained agent (neural network).
        env: The environment to test the agent in.
        num_episodes: Number of episodes to run for testing.
        render: If True, render the environment during testing.
    """
    total_fruits_caught, total_fruits_missed = [], []
    total_pipes_passed, total_crashes = [], []

    for episode in range(num_episodes):
        obs, _ = env.reset(seed=42)
        obs = torch.tensor(obs).float().unsqueeze(0)
        done = False
        total_reward = 0
        max_timesteps = 1000
        timesteps = 0
        if env_id == 'Catcher':
            fruits_caught, missed_fruits = 0, 0
        else:
            pipes_passed, crashes = 0, 0

        while not done and timesteps<=max_timesteps:
            with torch.no_grad():
                action = agent.get_action(obs)
            next_obs, reward, terminated, truncated, info = env.step(action)
            game_stats = info.get('game_stats', None)
            if env_id == 'Catcher':
                if game_stats['caught_fruit']:
                    fruits_caught += 1
                elif game_stats['missed_fruit']:
                    missed_fruits += 1
            else:
                if game_stats['pipe_passed']:
                    pipes_passed += 1
                elif game_stats['crashed']:
                    crashes += 1

            obs = torch.tensor(next_obs).float().unsqueeze(0)
            print(obs)
            total_reward += reward
            if render:
                env.render()
            timesteps+=1
            done = terminated or truncated

        print(f"Episode {episode + 1} - Total Reward: {total_reward}")
        if env_id == 'Catcher':
            total_fruits_caught.append(fruits_caught)
            total_fruits_missed.append(missed_fruits)
        else:
            total_pipes_passed.append(pipes_passed)
            total_crashes.append(crashes)

    if env_id == 'Catcher':
        print('Average # fruits caught:', np.mean(total_fruits_caught), np.std(total_fruits_caught))
        print('Average # fruits missed:', np.mean(total_fruits_missed), np.std(total_fruits_missed))
    else:
        print('Average # pipes passed:', np.mean(total_pipes_passed), np.std(total_pipes_passed))
        print('Average # crashes:', np.mean(total_crashes), np.std(total_crashes))
    env.close()


if __name__ == "__main__":
    # Load the environment
    env_id = 'FlappyBird'

    if env_id=='FlappyBird':
        register(
            id='FlappyBird',  # Unique ID for the environment
            entry_point='initialize_flappyBird:FlappyBirdEnv',  # Path to the FlappyBirdEnv class
            max_episode_steps=100000000,  # Maximum number of steps in an episode
        )
        env = gym.make('FlappyBird',
                    normalize=False,
                    display=False,
                    )

        # Load the trained DQN model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        agent = FlappyBirdAgent(env).to(device)
        checkpoint_path = "wandb/flappyBird/run_acc_state_acc_r/files/flappy_agent_acc_state_acc_r_2.pt"  # Path to the saved model checkpoint
        agent.load_state_dict(torch.load(checkpoint_path, map_location=device))
        agent.eval()  # Set the agent to evaluation mode

        # Test the agent
        test_dqn(agent, env, 'FlappyBird', num_episodes=100, render=True)  # Run for 100 episodes with rendering

    elif env_id=='Catcher':
        register(
            id='Catcher',  # Unique ID for the environment
            entry_point='initialize_catcher:CatcherEnv',  # Path to the FlappyBirdEnv class
            max_episode_steps=100000000,  # Maximum number of steps in an episode
        )
        env = gym.make('Catcher',
                    normalize=False,
                    display=False,
                    )

        # Load the trained DQN model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        agent = CatcherAgent(env).to(device)
        checkpoint_path = "Catcher_Flappy_Continuous/wandb/DQN_Catcher_Acc_State_Acc_R/files/catcher_agent_acc_state_acc_r.pt"  # Path to the saved model checkpoint
        agent.load_state_dict(torch.load(checkpoint_path, map_location=device))
        agent.eval()  # Set the agent to evaluation mode

        # Test the agent
        test_dqn(agent, env, 'Catcher', num_episodes=100, render=True)  # Run for 100 episodes with rendering
