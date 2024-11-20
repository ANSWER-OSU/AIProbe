from gym_pygame.envs.base import BaseEnv
import numpy as np


class ModifiedFlappyBirdEnv(BaseEnv):
    def __init__(self, normalize=False, display=False, random_pipe_color=True, pipe_color="red", **kwargs):
        self.game_name = 'FlappyBird'
        self.init(normalize, display, random_pipe_color=random_pipe_color, pipe_color=pipe_color, **kwargs)

    def get_ob_normalize(cls, state):
        state_normal = cls.get_ob(state)
        return state_normal


HEIGHT = 500
BIN_SIZE = HEIGHT / 20
WIDTH = 288


class FlappyBirdEnv(BaseEnv):
    def __init__(self, normalize=False, display=False, **kwargs):
        self.game_name = 'FlappyBird'
        self.init(normalize, display, **kwargs)

    def get_ob_normalize(cls, state):
        state_normal = cls.get_ob(state)
        return state_normal



import numpy as np
import matplotlib.pyplot as plt


HEIGHT = 500
BIN_SIZE_Y = HEIGHT / 20
WIDTH = 280
BIN_SIZE_DISTANCE = 50


def bin_value(value, bin_size):
    return int(value // bin_size)

def run_flappy_bird_with_y_and_distance_bins():
    # Initialize the environment
    env = FlappyBirdEnv(normalize=True)
    seed = 42
    env.reset(seed)
    env.action_space.seed(seed)
    env.observation_space.seed(seed)

    time_elapsed = 0
    y_bins = []
    distance_bins = []
    initial_y = None
    initial_distance = None

    while True:
        action = env.action_space.sample()
        obs, reward, terminated, _, _ = env.step(action)


        y_value = obs[0]
        distance_to_pipe = obs[2]


        if initial_y is None:
            initial_y = y_value
            initial_distance = distance_to_pipe
            relative_y = 0
            relative_distance = 0
        else:
            # Calculate the relative y position and distance from the initial point
            relative_y = y_value - initial_y
            relative_distance = distance_to_pipe - initial_distance

        # Bin the y value and distance to new pipe based on their respective bin sizes
        y_bin_index = bin_value(y_value, BIN_SIZE_Y)
        distance_bin_index = bin_value(relative_distance, BIN_SIZE_DISTANCE)

        # Store the binned values
        y_bins.append(y_bin_index)
        distance_bins.append(distance_bin_index)

        # Render the environment (optional)
        env.render('rgb_array')

        # Print for debugging
        print(f'Time: {time_elapsed}, Y Value: {y_value}, Y Bin: {y_bin_index}, Distance to Pipe: {distance_to_pipe}, Distance Bin: {distance_bin_index}')
        print('Observation:', obs)
        print('Reward:', reward)
        print('Done:', terminated)

        if terminated:
            break

        # Increment time
        time_elapsed += 1

    env.close()

    # Visualization of the binned y values and distance to new pipe over time
    plt.figure(figsize=(12, 6))

    # Plot for Y Value Bins
    plt.subplot(1, 2, 1)
    plt.plot(range(len(y_bins)), y_bins, marker='o', linestyle='-', color='green', label='Y Binned Value')
    plt.title('Bird’s Y Binned Position Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Y Bin Index')
    plt.grid(True)
    plt.legend()

    # Plot for Distance to Pipe Bins
    plt.subplot(1, 2, 2)
    plt.plot(range(len(distance_bins)), distance_bins, marker='o', linestyle='-', color='blue', label='Distance to Pipe Binned Value')
    plt.title('Distance to New Pipe Binned Value Over Time')
    plt.xlabel('Time Step')
    plt.ylabel('Distance Bin Index')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

    return y_bins, distance_bins


if __name__ == '__main__':
    # Run the Flappy Bird environment and bin the y values and distance to new pipe
    y_binned_values, distance_binned_values = run_flappy_bird_with_y_and_distance_bins()

