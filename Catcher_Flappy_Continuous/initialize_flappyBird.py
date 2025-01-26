from gym_pygame.envs.base import BaseEnv
import time

# ## original way to call FlappyBird without any mods
# class FlappyBirdEnv(BaseEnv):
#   def __init__(self, agent_params, obj_params, env_params, normalize=False, display=False, **kwargs):
#     self.game_name = 'FlappyBird'
#     self.init(agent_params, obj_params, env_params, normalize, display, **kwargs)
#
#   def get_ob_normalize(cls, state):
#     state_normal = cls.get_ob(state)
#     return state_normal

class FlappyBirdEnv(BaseEnv):
  def __init__(self, normalize=False, display=False, agent_params=None, obj_params=None, env_params=None, **kwargs):
    self.game_name = 'FlappyBird'
    self.init(normalize, display, agent_params, obj_params, env_params, **kwargs)

  def get_ob_normalize(cls, state):
    state_normal = cls.get_ob(state)
    return state_normal


if __name__ == '__main__':
  agent_params = {
                  'FLAP_POWER': 17, # set
                  'MAX_DROP_SPEED': 100, # set
                  'init_pos': (100,100) ,# set

      # Adding game state information
          "player_vel": -15,
          "next_pipe_dist_to_player": 100,
          "next_pipe_top_y": 100,
          "next_pipe_bottom_y": 100,
          "next_next_pipe_dist_to_player": 100,
          "next_next_pipe_top_y": 100,
          "next_next_pipe_bottom_y":100

  }

  obj_params = {
                  'speed': 40,
                  'start_gap': 10, # set
                  'pipe_gap': 100, # set
                  'offset' : -100 # set
                }
  env_params = {
                  'gravity': 9, # set
                  'max_drop_speed': 5 # set
                }
  env = FlappyBirdEnv(agent_params=agent_params, obj_params=obj_params, env_params=env_params)
#if __name__ == '__main__':
  #env = FlappyBirdEnv(None, None, None, normalize=False, display=False)
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
  bird_should_flap = [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
  act = 0
  while True:

    print('in while')
    action = env.action_space.sample()
    action = bird_should_flap[act]
    obs, reward, terminated, _, _ = env.step(action)
    #env.render('rgb_array')
    env.render('human')
    act +=1

    print(env.game.clock)
    print('Observation:', obs)
    print('Reward:', reward)
    print('Done:', terminated)
    #time.sleep(3)
    if terminated:
      obs, _ = env.reset()
      continue
      #break
  env.close()
