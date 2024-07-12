import gym
from gym import spaces
from ple import PLE
import numpy as np

def process_state_prespecified(state):
    return np.array([ state.values() ])

def process_state(state):
    return np.array(state)

class PLEEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, prespecified_game=True, game_name='FlappyBird', display_screen=True, rgb_state=False):
        # Open up a game state to communicate with emulator
        import importlib
        self.game_name = game_name
        if prespecified_game:
            game_module_name = ('ple.games.%s' % game_name).lower()
        else:
            game_module_name = ('domains.ple.%s' % game_name).lower()
        game_module = importlib.import_module(game_module_name)
        self.game = getattr(game_module, game_name)() # game_module: sourcecatcher, game_name: SourceCatcher
        self.rgb_state = rgb_state
        if self.rgb_state:
            self.game_state = PLE(self.game, fps=30, display_screen=display_screen)
        else:
            if prespecified_game:
                self.game_state = PLE(self.game, fps=30, display_screen=display_screen, state_preprocessor=process_state_prespecified)
            else:
                self.game_state = PLE(self.game, fps=30, display_screen=display_screen, state_preprocessor=process_state)
        self.game_state.init()
        self._action_set = self.game_state.getActionSet() # returns [97, 100, None]; {97: left, 100: right, None: NOOP}
        self.action_space = spaces.Discrete(len(self._action_set))
        self.actions = list(range(self.action_space.n)) # returns [0, 1, 2]; mapping {0: (left or 97), 1: (right or 100), 2: (NOOP or None)}
        if self.rgb_state:
            self.state_width, self.state_height = self.game_state.getScreenDims()
            self.observation_space = spaces.Box(low=0, high=255, shape=(self.state_width, self.state_height, 3))
        else:
            self.state_dim = self.game_state.getGameStateDims()
            self.observation_space = spaces.Box(low=0, high=255, shape=self.state_dim)
        self.viewer = None
        self.feature_bins = []
        self.num_states = len(self.get_states())
        self.goal_score = 100
        if hasattr(self.game, 'score'):
            self.score = self.game.score
        self.start_state = None
        self.agent_curr_state = self.start_state
        if hasattr(self.game, 'feature_map'):
            self.feature_map = self.game.feature_map
        if hasattr(self.game, 'feature_bins'):
            self.feature_bins = self.game.feature_bins
        if hasattr(self.game, 'num_lives'):
            self.num_lives = self.game.num_lives
        if hasattr(self.game, 'lives_left'):
            self.input_lives = self.game.lives_left
            self.lives_left = self.game.lives_left
        if hasattr(self.game, 'good_fruits_caught'):
            self.good_fruits_caught = self.game.good_fruits_caught
        if hasattr(self.game, 'badfruit_region'):
            self.badfruit_region = self.game.badfruit_region
        if hasattr(self.game, 'is_obstacle'):
            self.is_obstacle = self.game.is_obstacle
        if hasattr(self.game, 'obj_x1'):
            self.obj_x1 = self.game.obj_x1
        if hasattr(self.game, 'obj_x2'):
            self.obj_x2 = self.game.obj_x2
        if hasattr(self.game, 'ob_width'):
            self.ob_width = self.game.ob_width
        if hasattr(self.game, 'agent_side'):
            self.agent_side = self.game.agent_side
        if hasattr(self.game, 'is_accurate_model'):
            self.is_accurate_model = self.game.is_accurate_model


    def get_source_state(self, state):
        if hasattr(self.game, 'get_source_state'):
            return self.game.get_source_state(state)
        return None

    def get_states(self):
        if hasattr(self.game, 'states'):
            return self.game.states

    def get_successors(self, state, action):
        if hasattr(self.game, 'get_successors'):
            return self.game.get_successors(state, action)

    def is_goal(self, game_score):
        if game_score>=self.goal_score:
            return True
        return False

    def is_bad_fruit(self, state):
        x_p, x_f, y_f, t_f = state
        if y_f==400 and x_p==x_f: # agent caught a fruit
            if t_f==0: # fruit is bad
                self.lives_left -= 1
                return True
        return False

    def is_good_fruit(self, state):
        x_p, x_f, y_f, t_f = state
        if y_f==400 and x_p==x_f: # agent caught a fruit
            if t_f==1: # fruit is good
                return True
        return False

    def is_terminal(self):
        if self.lives_left==0:
            return True
        return False

    def step(self, action):
        terminal = False
        successors, succ_probabilities = self.get_successors(self.agent_curr_state, action)
        next_state_idx = np.random.choice(len(successors), p=succ_probabilities)
        self.agent_curr_state = successors[next_state_idx]
        reward, obj_type = self.get_reward(self.agent_curr_state, action) # obj is either fruit or pipe; obj_type is the type of fruit or pipe
        self.score += reward
        if self.game_name.lower() == 'sourcecatcher' or self.game_name.lower() == 'targetcatcher':
            _ = self.is_bad_fruit(self.agent_curr_state)
            if self.is_terminal() or self.is_goal(self.score):
                terminal = True
        else:
            if self.is_crash(self.agent_curr_state) or self.is_goal(self.score):
                terminal = True
        return successors[next_state_idx], reward, succ_probabilities[next_state_idx], terminal, obj_type


        # reward = self.game_state.act(self._action_set[action])
        # state = self._get_state()
        # terminal = self.game_state.game_over()
        # return state, reward, terminal, {}

    def _get_image(self, game_state):
        image_rotated = np.fliplr(np.rot90(game_state.getScreenRGB(),3)) # Hack to fix the rotated image returned by ple
        return image_rotated

    def _get_state(self):
        if self.rgb_state:
            return self._get_image(self.game_state)
        else:
            return self.game_state.getGameState()

    @property
    def _n_actions(self):
        return len(self._action_set)

    def reset(self):
        if self.rgb_state:
            self.observation_space = spaces.Box(low=0, high=255, shape=(self.state_width, self.state_height, 3))
        else:
            self.observation_space = spaces.Box(low=0, high=255, shape=self.state_dim)
        self.game_state.reset_game()
        self.start_state = tuple(self._get_state())
        self.agent_curr_state = self.start_state
        self.score = 0
        if hasattr(self, 'input_lives'):
            self.lives_left = self.input_lives
        if hasattr(self, 'is_obstacle') and self.is_obstacle:
            self.update_states()
        self.num_states = len(self.get_states())
        return self.start_state

    def update_states(self):
        # Remove states beyond the obstacle
        if self.is_obstacle:
            updated_states = []
            true_states = self.get_states()
            for s in true_states:
                if self.agent_curr_state[0] < self.obj_x1 and s[0] >= self.obj_x1:
                    continue
                elif self.agent_curr_state[0] > (self.obj_x2-1) and s[0] < self.obj_x2:
                    continue
                else:
                    updated_states.append(s)
            self.game.states = updated_states


    def _render(self, mode='human', close=False):
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return
        img = self._get_image(self.game_state)
        if mode == 'rgb_array':
            return img
        elif mode == 'human':
            from gym.envs.classic_control import rendering
            if self.viewer is None:
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(img)

    def _seed(self, seed):
        rng = np.random.RandomState(seed)
        self.game_state.rng = rng
        self.game_state.game.rng = self.game_state.rng

        self.game_state.init()

    def _get_screen_dim(self):
        if hasattr(self.game, 'screen_width'):
            self.screen_width = self.game.screen_width
        if hasattr(self.game, 'screen_height'):
            self.screen_height = self.game.screen_height

    def get_reward(self, state, action):
        if hasattr(self.game, 'get_reward'):
            return self.game.get_reward(state, action)

    def set_obstacle(self, value, x1, x2):
        if hasattr(self.game, 'set_obstacle'):
            self.is_obstacle = value
            self.obj_x1 = x1
            self.obj_x2 = x2
            return self.game.set_obstacle(value, x1, x2)

    def set_agent_side(self, value):
        if hasattr(self.game, 'set_agent_side'):
            self.agent_side = value
            return self.game.set_agent_side(value)

    def set_badfruit_region(self, region_array):
        if hasattr(self.game, 'badfruit_region'):
            self.badfruit_region = region_array
            return self.game.set_badfruit_region(region_array)

    def set_is_accurate_model(self, value1, value2):
        if hasattr(self.game, 'set_is_accurate_model'):
            self.is_accurate_model = value1
            self.inaccuracy_type = value2
            return self.game.set_accurate_model(value1, value2)

    def _generatePipes(self, offset=0, pipe=None):
        if hasattr(self.game, '_generatePipes'):
            return self.game._generatePipes(offset, pipe)

    def is_past_pipe(self, state):
        if hasattr(self.game, 'is_past_pipe'):
            return self.game.is_past_pipe(state)

    def is_crash(self, state):
        if hasattr(self.game, 'is_crash'):
            return self.game.is_crash(state)
