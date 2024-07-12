from domains.ple.sourcecatcher import SourceCatcher
from domains.ple.sourcecatcher import GoodFruit
from domains.ple.sourcecatcher import AgentPaddle
import random
import pygame
import numpy as np
import math
from itertools import product

class UncertainFruit(GoodFruit):
    def __init__(self, speed, size, SCREEN_WIDTH, SCREEN_HEIGHT, rng, y_feature_bins, fruit_num_types, badfruit_region, init_probGoodFruit):
        super(UncertainFruit, self).__init__(speed, size, SCREEN_WIDTH, SCREEN_HEIGHT, rng, y_feature_bins)
        self.num_types = fruit_num_types
        self.badfruit_region = badfruit_region
        self.init_probGoodFruit = init_probGoodFruit
        self.type = -1 # Initialization of type

    def drawFruit(self, fruitType, bad_fruit_id):
        if fruitType == bad_fruit_id:
            color = (50, 50, 50)
        else:
            color = (255, 120, 120)
        image = pygame.Surface((self.size, self.size))
        image.fill((0, 0, 0, 0))
        image.set_colorkey((0, 0, 0))

        pygame.draw.rect(
            image,
            color,
            (0, 0, self.size, self.size),
            0
        )
        self.image = image

    def reset(self, x_bins, bad_fruit_id):
        super(UncertainFruit, self).reset(x_bins)
        self.setFruitType(self.rect.center[0], bad_fruit_id)
        self.drawFruit(self.type, bad_fruit_id)

    def setFruitType(self, fruit_x, bad_fruit_id):
        # For fruit_x values between 0 and the threshold, the target world looks exactly like the source (only good fruit).
        # For x values after the threshold, good fruit falls with probability probGoodFruit and bad fruit falls with probability (1-probGoodFruit)
        if fruit_x in self.badfruit_region:
            self.probGoodFruit = self.init_probGoodFruit
        else:
            self.probGoodFruit = 1
        if random.random() < self.probGoodFruit:
            self.type = random.randint(1, self.num_types-1) # Good fruit
        else:
            self.type = bad_fruit_id # Bad fruit

class TargetCatcher(SourceCatcher):
    def __init__(self, width=500, height=500, init_lives=3, max_steps=100):
        super(TargetCatcher, self).__init__(width, height, init_lives)
        self.bad_fruit_id = 0 # Bad fruits have type 0. All other fruits have type > 0.
        self.good_fruit_id = 1
        self.fruit_num_types = 2
        self.init_probGoodFruit = 0.5
        self.feature_bins = [range(0, self.width, self.player_speed),
                             range(0, self.width, self.fruit_size),
                             range(0, self.height, self.fruit_size),
                             range(0, self.fruit_num_types, 1)]
        self.feature_map = {"player_x":0, "fruit_x":1, "fruit_y": 2, "fruit_type":3}
        self.badfruit_region = [250,300,350,400,450]
        self.is_obstacle = False
        self.obj_x1 = None
        self.obj_x2 = None
        self.ob_width = 50
        self.agent_side = None

    def init(self):
        self.states = []
        super(TargetCatcher, self).init()

        if self.badfruit_region!=None:
            if len(self.badfruit_region) > 0 and len(self.states) == 0:
                for s in product(*self.feature_bins):
                    # Remove states in which the fruit has already hit the ground (The agent does not take an action in these states because they are goal states - Q-value will be 0).
                    if s[self.feature_map["fruit_y"]] == self.y_locs[len(self.y_locs)-1]:
                        continue
                    # Remove states with bad fruits in the "good" region. There will never be a bad fruit initialized there.
                    elif s[self.feature_map["fruit_x"]] not in self.badfruit_region and s[self.feature_map["fruit_type"]] == self.bad_fruit_id:
                        continue
                    # Remove states with good fruits in the "bad" region. There will never be a bad fruit initialized there.
                    elif s[self.feature_map["fruit_x"]] in self.badfruit_region and s[self.feature_map["fruit_type"]] == self.good_fruit_id:
                        continue

                    else:
                        self.states.append(s)
                print("Total no. of states = ", len(self.states))

        self.fruit = UncertainFruit(self.fruit_fall_speed, self.fruit_size,
                           self.width, self.height, self.rng,
                           self.feature_bins[self.feature_map["fruit_y"]], self.fruit_num_types, self.badfruit_region, self.init_probGoodFruit)

        if not hasattr(self, "locs"):
            self.locs = self.feature_bins[self.feature_map["fruit_x"]]
        self.fruit.reset(self.locs, self.bad_fruit_id)
        self.real_state = True

    def getGameState(self):
        state_id = np.random.choice(range(len(self.states)))
        state = self.states[state_id]
        if self.is_obstacle:
            if self.agent_side=='left':
                while state[0]>=self.obj_x1:
                    state_id = np.random.choice(range(len(self.states)))
                    state = self.states[state_id]
            elif self.agent_side=='right':
                while state[0]<self.obj_x2:
                    state_id = np.random.choice(range(len(self.states)))
                    state = self.states[state_id]
        return state

    def get_source_state(self, state):
        return state[:-1]

    def update_fruit_score(self):
        if self.fruit.type == self.bad_fruit_id:
            dist = abs(self.player.rect.center[0] - self.fruit.rect.center[0])
            self.curr_score = (dist/self.player_speed)
            if dist == 0:
                self.curr_score = -100
            y_feature_bins = self.feature_bins[self.feature_map["fruit_y"]]
            if self.fruit.rect.center[1] == y_feature_bins[len(y_feature_bins)-1]: # Last y-value
                self.ended = True
        else: # If good fruit (exactly like source)
            super(TargetCatcher, self).update_fruit_score()

    def state_in_locs(self, state):
        return state[self.feature_map["fruit_x"]] in self.locs

    def get_successors(self, state, action):
        success_prob = 1
        x_p, x_f, y_f, t_f = state
        new_x_p, new_y_f, new_x_f, new_t_f = -1, -1, -1, -1
        min_x_p, max_x_p = 0, self.screen_width
        dx = 0

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
            new_t_f = t_f
        if y_f>=450 or new_y_f>=450:
            x_bins = self.feature_bins[self.feature_map["fruit_x"]]
            new_x_f = random.choice(x_bins) # Choose randomly from one of the possible values in x_bins
            if new_x_f in self.badfruit_region:
                new_t_f = 0
            else:
                new_t_f = 1
            new_y_f = 0
        return [(new_x_p, new_x_f, new_y_f, new_t_f)], [success_prob]

    def set_badfruit_region(self, region_array):
        self.badfruit_region = region_array

    def set_obstacle(self, value, x1, x2):
        self.is_obstacle = value
        self.obj_x1 = x1
        self.obj_x2 = x2

    def set_agent_side(self, value):
        self.agent_side = value
