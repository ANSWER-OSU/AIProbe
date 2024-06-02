import gym
import minigrid
from minigrid.wrappers import RGBImgPartialObsWrapper, ImgObsWrapper
import numpy as np
import pygame

# Create the environment
env = gym.make('MiniGrid-MemoryS7-v0')
env = RGBImgPartialObsWrapper(env)  # Get pixel observations
env = ImgObsWrapper(env)  # Get rid of the 'mission' field

# Define the action mapping
action_map = {
    pygame.K_w: 2,  # Move forward
    pygame.K_a: 0,  # Turn left
    pygame.K_d: 1,  # Turn right
    pygame.K_p: 3,  # Pick up an object
    pygame.K_t: 5  # Toggle/activate an object
}

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("MiniGrid Memory Environment")
clock = pygame.time.Clock()


# Function to render the environment using Pygame
def render(obs):
    img = obs
    img = np.transpose(img, (1, 0, 2))
    surface = pygame.surfarray.make_surface(img)
    screen.blit(surface, (0, 0))
    pygame.display.flip()


# Reset the environment
obs, _ = env.reset()
done = False

while not done:
    render(obs)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.KEYDOWN:
            if event.key in action_map:
                action = action_map[event.key]
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                print(f"Action: {action}, Reward: {reward}, Done: {done}")

    clock.tick(30)  # Limit to 30 frames per second

env.close()
pygame.quit()
