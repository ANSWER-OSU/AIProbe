from gym_pygame.envs.base import BaseEnv

# ## original way to call FlappyBird without any mods
# class FlappyBirdEnv(BaseEnv):
#   def __init__(self, agent_params, obj_params, env_params, normalize=False, display=False, **kwargs):
#     self.game_name = 'FlappyBird'
#     self.init(agent_params, obj_params, env_params, normalize, display, **kwargs)

#   def get_ob_normalize(cls, state):
#     state_normal = cls.get_ob(state)
    # return state_normal

class FlappyBirdEnv(BaseEnv):
  def __init__(self, normalize=False, display=False): #, agent_params=None, obj_params=None, env_params=None, **kwargs):
    self.game_name = 'FlappyBird'
    self.init(normalize, display) #, agent_params, obj_params, env_params, **kwargs)

  def get_ob_normalize(cls, state):
    state_normal = cls.get_ob(state)
    return state_normal


if __name__ == '__main__':
  agent_params = {
                  'FLAP_POWER': 0, # set
                  'MAX_DROP_SPEED': 1, # set
                  'init_pos': (100,100) # set
                }
  obj_params = {
                  'speed': 23,
                  'start_gap': 10, # set
                  'pipe_gap': 10, # set
                  'offset' : 1 # set
                }
  env_params = {
                  'gravity': 55, # set
                  'max_drop_speed': 90 # set
                }
  # env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params)
  env = FlappyBirdEnv()
  print('Action space:', env.action_space)
  print('Action set:', env.action_set)
  print('Obsevation space:', env.observation_space)
  print('Obsevation space high:', env.observation_space.high)
  print('Obsevation space low:', env.observation_space.low)

  seed = 42
  obs, _ = env.reset(seed)
  obs, info = env.reset(seed)
  env.action_space.seed(seed)
  env.observation_space.seed(seed)
  while True:
    print('in while')
    # action = env.action_space.sample()
    action = 'up'
    obs, reward, terminated, _, _ = env.step(action)
    # env.render('rgb_array')
    env.render('human')
    print('Observation:', obs)
    print('Reward:', reward)
    print('Done:', terminated)
    # input()
    if terminated:
      # obs, _ = env.reset()
      break
  env.close()
