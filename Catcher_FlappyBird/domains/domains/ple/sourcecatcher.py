from ple.games.catcher import Catcher
from ple.games.catcher import Paddle
from ple.games.catcher import Fruit
import pygame
import random
import collections
from pygame.constants import K_a, K_d
from ple.games import base
import numpy as np
from itertools import product

class AgentPaddle(Paddle):
    def __init__(self, speed, width, height, SCREEN_WIDTH, SCREEN_HEIGHT, feature_bins):
        super(AgentPaddle, self).__init__(speed, width, height, SCREEN_WIDTH, SCREEN_HEIGHT)
        x = random.choice(feature_bins) # Choose randomly from one of the possible x locations
        self.rect.center = (x, SCREEN_HEIGHT - height - 3)

    def update(self, dx, dt): # gets successor state
        '''
        dx is by how much the paddle moves
        when a==left, dx = -50
        when a==right, dx==+50
        '''
        x, y = self.rect.center
        n_x = x + dx

        if n_x <= 0:
            n_x = 0

        if n_x + self.width >= self.SCREEN_WIDTH:
            n_x = self.SCREEN_WIDTH - self.width

        self.rect.center = (n_x, y)

class GoodFruit(Fruit):
    def __init__(self, speed, size, SCREEN_WIDTH, SCREEN_HEIGHT, rng, y_feature_bins):
        super(GoodFruit, self).__init__(speed, size, SCREEN_WIDTH, SCREEN_HEIGHT, rng)
        self.y_feature_bins = y_feature_bins
        self.type = 1 # setting fruit type to 1 (1: good fruit, 0: bad fruit)

    def update(self, dt):
        x, y = self.rect.center
        curr_y_bin = np.digitize(y, self.y_feature_bins)-1
        new_y_bin = curr_y_bin + self.speed
        if new_y_bin >= len(self.y_feature_bins):
            new_y_bin = len(self.y_feature_bins)-1
        n_y = self.y_feature_bins[new_y_bin]

        self.rect.center = (x, n_y)

    def reset(self, x_bins):
        x = random.choice(x_bins) # Choose randomly from one of the possible values in x_bins
        y = 0
        self.rect.center = (x, y)

class SourceCatcher(Catcher):
    def __init__(self, width=500, height=500, init_lives=3, max_steps=100):
        super(SourceCatcher, self).__init__(width, height, init_lives)

        actions = collections.OrderedDict() # To force order of actions to be the same each time
        actions["left"] = K_a
        actions["right"] = K_d

        base.PyGameWrapper.__init__(self, width, height, actions=actions)
        self.player_speed = 50
        self.fruit_id = 1
        self.fruit_num_types = 1
        self.fruit_fall_speed = 1
        self.fruit_size = 50
        self.paddle_width = 50
        self.paddle_height = 50
        self.step_num = 0
        self.max_steps = max_steps
        self.screen_width = width
        self.screen_height = height
        self.num_lives = init_lives
        self.lives_left = init_lives
        # for obstacles
        self.is_obstacle = False
        self.obj_x1 = 250
        self.obj_x2 = 300
        self.ob_width = 50
        self.agent_side = None
        self.is_accurate_model = None
        self.inaccuracy_type = None
        print(self.inaccuracy_type)
        input()

    def init(self):
        self.score = 0
        if self.inaccuracy_type in set([0, 1]):
            self.feature_bins = [range(0, self.width, self.player_speed),
                                range(0, self.width, self.fruit_size),
                                range(0, self.height, self.fruit_size),
                                range(1, self.fruit_num_types+1, 1)]
            self.feature_map = {"player_x":0, "fruit_x":1, "fruit_y": 2, "fruit_type":3}
        else:
            self.feature_bins = [range(0, self.width, self.player_speed),
                                range(0, self.width, self.fruit_size),
                                range(0, self.height, self.fruit_size)]
            self.feature_map = {"player_x":0, "fruit_x":1, "fruit_y": 2}

        self.y_locs = self.feature_bins[self.feature_map["fruit_y"]]
        self.states = []
        for s in product(*self.feature_bins):
            # Remove states in which the fruit has already hit the ground (The agent does not take an action in these states because they are goal states - Q-value will be 0)
            if s[self.feature_map["fruit_y"]] == self.y_locs[len(self.y_locs)-1]:
                continue
            else:
                self.states.append(s)

        print("Total no. of states = ", len(self.states))
        self.player = AgentPaddle(self.player_speed, self.paddle_width,
                             self.paddle_height, self.width, self.height, self.feature_bins[self.feature_map["player_x"]])

        self.fruit = GoodFruit(self.fruit_fall_speed, self.fruit_size,
                           self.width, self.height, self.rng, self.feature_bins[self.feature_map["fruit_y"]])

        self.fruit.reset(self.feature_bins[self.feature_map["fruit_x"]])
        self.step_num = 0
        self.ended = False

    def getGameState(self):
        state_id = np.random.choice(range(len(self.states)))
        state = self.states[state_id]
        if self.is_obstacle:
            if self.agent_side=='left':
                while state[0]>self.obj_x1:
                    state_id = np.random.choice(range(len(self.states)))
                    state = self.states[state_id]
            elif self.agent_side=='right':
                while state[0]<self.obj_x2:
                    state_id = np.random.choice(range(len(self.states)))
                    state = self.states[state_id]
        return state

    def game_over(self):
        return self.ended

    def step(self, dt):
        self.step_num += 1
        self.screen.fill((0, 0, 0))
        self._handle_player_events()

        self.curr_score = 0

        self.player.update(self.dx, dt)
        self.fruit.update(dt)

        self.player.draw(self.screen)
        self.fruit.draw(self.screen)

        self.update_fruit_score()
        self.score += self.curr_score

    def update_fruit_score(self):
        max_dist = self.width - self.paddle_width
        dist = abs(self.player.rect.center[0] - self.fruit.rect.center[0])
        self.curr_score = ((max_dist-dist)/self.player_speed)
        y_feature_bins = self.feature_bins[self.feature_map["fruit_y"]]
        if self.fruit.rect.center[1] == y_feature_bins[len(y_feature_bins)-1]: # Last y-value
            self.ended = True

    def get_reward(self, state, action):
        '''
        TODO: Streamline this further
        '''
        caught_good_fruit = 20
        caught_fruit = 20
        caught_bad_fruit = -5
        step = -1

        #### Accurate Reward & State Rep. ####
        if self.inaccuracy_type==0:
            x_p, x_f, y_f, t_f = state
            if y_f==400:
                if x_p==x_f and t_f==1: # agent caught good fruit
                    return caught_good_fruit, 1
                elif x_p==x_f and t_f==0: # agent caught bad fruit
                    self.lives_left -= 1
                    return caught_bad_fruit, 0
                else:
                    return step, t_f
            else:
                    return step, t_f

        #### Inaccurate Reward & Accurate State Rep. ####
        elif self.inaccuracy_type==1:
            x_p, x_f, y_f, t_f = state
            if y_f==400:
                if x_p==x_f:
                    return caught_fruit, t_f
                else:
                    return step, t_f
            else:
                    return step, t_f

        #### Accurate Reward & Inaccurate State Rep. ####
        elif self.inaccuracy_type==2:
            x_p, x_f, y_f = state
            if y_f==400:
                if x_p==x_f: # agent caught good fruit
                    return caught_good_fruit
                elif x_p==x_f: # agent caught bad fruit
                    self.lives_left -= 1
                    return caught_bad_fruit
                else:
                    return step
            else:
                return step

        #### Inaccurate Reward & Inaccurate State Rep. ####
        elif self.inaccuracy_type==3:
            x_p, x_f, y_f = state
            if y_f==400:
                if x_p==x_f:
                    return caught_fruit
                else:
                    return step
            else:
                return step


    def get_successors(self, state, action):
        success_prob = 1

        if self.inaccuracy_type in set([0, 1]):
            x_p, x_f, y_f, t_f = state
        else:
            x_p, x_f, y_f = state
        new_x_p, new_y_f, new_x_f, dx = -1, -1, -1, 0
        min_x_p, max_x_p = 0, self.screen_width

        # update paddle position
        if action==0: # left
            dx = -50
        elif action==1: # right
            dx = 50
        else: # NOOP
            dx = 0
        new_x_p = x_p + dx

        if self.is_obstacle:
            if x_p < self.obj_x1:
                max_x_p = self.obj_x1
            elif x_p >= self.obj_x2:
                min_x_p = self.obj_x2

        if new_x_p <= min_x_p:
            new_x_p = min_x_p
        if new_x_p + self.paddle_width >= max_x_p:
            new_x_p = max_x_p - self.paddle_width


        # update fruit position
        self.y_feature_bins = self.feature_bins[self.feature_map["fruit_y"]]
        self.fruit_fall_speed = 1

        if y_f <= self.y_feature_bins[len(self.y_feature_bins)-2]:
            if y_f==0:
                curr_y_bin = 0
            else:
                curr_y_bin = np.digitize(y_f, self.y_feature_bins)-1
            new_y_bin = curr_y_bin + self.fruit_fall_speed
            if new_y_bin >= len(self.y_feature_bins):
                new_y_bin = len(self.y_feature_bins)-1
            new_y_f = self.y_feature_bins[new_y_bin]
            new_x_f = x_f
        if y_f==450 or new_y_f==450:
            x_bins = self.feature_bins[self.feature_map["fruit_x"]]
            new_x_f = random.choice(x_bins) # Choose randomly from one of the possible values in x_bins
            new_y_f = 0
        if self.inaccuracy_type in set([0, 1]):
            return [(new_x_p, new_x_f, new_y_f, t_f)], [success_prob]
        else:
            return [(new_x_p, new_x_f, new_y_f)], [success_prob]

    def set_obstacle(self, value, x1, x2):
        self.is_obstacle = value
        self.obj_x1 = x1
        self.obj_x2 = x2

    def set_agent_side(self, value):
        self.agent_side = value

    def set_accurate_model(self, value1, value2):
        self.is_accurate_model = value1
        self.inaccuracy_type = value2
