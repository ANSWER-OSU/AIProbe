import gymnasium as gym
from gymnasium.envs.registration import register
from initialize_catcher import CatcherEnv  # Update the import path as needed

register(
    id='Catcher',  # Unique ID for the environment
    entry_point='initialize_catcher.CatcherEnv',  # Path to the CatcherEnv class
    max_episode_steps=1000,  # Maximum number of steps in an episode
)
