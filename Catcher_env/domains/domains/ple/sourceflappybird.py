from ple.games.flappybird import FlappyBird
from ple.games.flappybird import Pipe
from ple.games.flappybird import BirdPlayer
import os
import sys
import numpy as np
import pygame
from pygame.constants import K_w
from ple.games import base
import random
import collections
from itertools import product
from pprint import pprint

class SourceFlappyBird(FlappyBird):
    def __init__(self, width=288, height=512, pipe_gap=100):
        super(SourceFlappyBird, self).__init__(width, height, pipe_gap)
        self.__dir__ = 'Catcher/domains/domains/ple/'

        actions = collections.OrderedDict() # To force order of actions to be the same each time
        actions["up"] = K_w
        base.PyGameWrapper.__init__(self, width, height, actions=actions)
        self.states = []
        # all in terms of y
        self.scale = 1.0
        self.vel = 0
        self.FLAP_POWER = 9 * self.scale
        self.MAX_DROP_SPEED = 10.0
        self.GRAVITY = 1.0 * self.scale
        self.thrust_time = 0.0
        # self.x_a = int(self.width * 0.2)
        self.speed = 50.0 * self.scale
        self.pipe_x = 240.0
        self.pipe_width = 52
        self.num_lives = 1
        self.lives_left = 1
        self.score = 0

    def init(self):
        super(SourceFlappyBird, self).init()
        self.pipe_min = 25
        self.pipe_max = 150
        self.init_pos = (
            int(self.width * 0.2),
            int(self.height / 2 - 100)
         )
        self.y_interval = 50
        self.y_max_pos = 300
        self.feature_bins = [[self.pipe_min+self.pipe_gap, self.pipe_max+self.pipe_gap],
                              [i for i in range(0, 251, 50)],
                              [self.pipe_min, self.pipe_max],
                              [i for i in range(0, 341, 50)],
                              [i for i in range(-10, 11, 5)],
                              [i for i in range(0, self.y_max_pos+1, self.y_interval)]]
        self.feature_map = {"next_pipe_bottom_y": 0, "next_pipe_dist_to_player": 1, "next_pipe_top_y": 2, "next_pipe_x": 3,
                            "player_vel": 4,
                            "player_y": 5}

        if len(self.states) == 0:
            for s in product(*self.feature_bins):
                # Remove states where the top and bottom pipes are not a distance of pipe_gap in between.
                if s[self.feature_map["next_pipe_bottom_y"]] != s[self.feature_map["next_pipe_top_y"]] + self.pipe_gap:
                    continue
                else:
                    self.states.append(s)
            print("Total no. of states = ", len(self.states))

        self.pipe_group = pygame.sprite.Group([self._generatePipes(offset=-75)])
        for i, p in enumerate(self.pipe_group):
            self._generatePipes(offset=self.pipe_offsets[i], pipe=p)

        self.win = False

    def getGameState(self):
        # State = [player y position, player velocity, next pipe distance to player,
        #          next pipe top y position, next pipe bottom y position]
        self.pipes = []
        for p in self.pipe_group:
            self.pipes.append((p, p.x - self.player.pos_x))
        self.pipes.sort(key=lambda p: p[1])

        next_pipe = self.pipes[0][0]

        self.state_dict = {
            "player_y": self.player.pos_y,
            "player_vel": self.player.vel,

            "next_pipe_dist_to_player": next_pipe.x - self.player.pos_x,
            "next_pipe_top_y": next_pipe.gap_start,
            "next_pipe_bottom_y": next_pipe.gap_start + self.pipe_gap,
            "next_pipe_x": next_pipe.x
        }
        for i in self.state_dict:
            possible_values = self.feature_bins[self.feature_map[i]]
            self.state_dict[i] = possible_values[np.digitize(self.state_dict[i], possible_values)-1]
        return [int(x) for x in self.get_arr_state(self.state_dict)]

    def get_arr_state(self, state):
        arr_state = np.zeros(len(state))
        i=0
        for key in sorted(state.keys()):
            index = self.feature_map[key]
            digitized_value = self.feature_bins[index][np.digitize(state[key], self.feature_bins[index])-1]
            arr_state[i] = digitized_value
            i+=1
        return arr_state

    def get_pipe_color(self, start_gap):
        return "green"

    def create_pipe(self, start_gap, offset):
        return Pipe(
                self.width,
                self.height,
                start_gap,
                self.pipe_gap,
                self.images["pipes"],
                self.scale,
                offset=offset,
                color=self.pipe_color
            )

    def _generatePipes(self, offset=0, pipe=None):
        possible_gaps = [0]
        if hasattr(self, "feature_map"):
            possible_gaps = self.feature_bins[self.feature_map["next_pipe_top_y"]]
        start_gap = random.choice(possible_gaps)

        self.pipe_color = self.get_pipe_color(start_gap)

        if pipe is None:
            return self.create_pipe(start_gap, offset)
        else:
            pipe.init(start_gap, self.pipe_gap, offset, self.pipe_color)

    def game_over(self):
        return self.lives <= 0 or self.win

    # def update_reward(self):
    #     for p in self.pipe_group:
    #         if self.player.pos_y <= 50:
    #             self.score += 0.1

    # def step(self, dt):
    #     self.rewards["tick"] = 0
    #     self.rewards["positive"] = 10
    #     self.rewards["loss"] = -10
    #     super(SourceFlappyBird, self).step(dt)
    #     for p in self.pipe_group:
    #         # If bird is under the pipe, wins this episode!
    #         if (p.x - p.width / 2) <= self.player.pos_x < (p.x - p.width / 2 + 4):
    #             self.score += self.rewards["positive"]
    #             self.win = True
    #     self.update_reward()

    def get_successors(self, state, action):
        success_prob = 1
        y_b, del_x, y_t, x_p, v_a, y_a = state
        new_y_t, new_y_b, new_y_a, new_del_x, new_x_p , new_v_a = 0, 0, 0, 0, 0, 0

        # Get agent position
        if action==0:
            new_v_a = v_a - 5
            if new_v_a==0:
                new_y_a = y_a
            elif new_v_a>0:
                new_y_a = y_a - 51 # 50 + 1 --> 1 bin adjustment
        elif action==1:
            new_v_a = v_a + 5
            if new_v_a==0:
                new_y_a = y_a
            elif new_v_a<0:
                new_y_a = y_a + 51

        # Get pipe positions
        if y_a==300 or x_p==0: # if game over i.e., when agent y-pos==300
            new_pipes = []
            pipe_group = pygame.sprite.Group([
                self._generatePipes(offset=-75),
                self._generatePipes(offset=-75 + self.width / 2),
                self._generatePipes(offset=-75 + self.width * 1.5)
            ])
            for p in pipe_group:
                new_pipes.append((p, p.x - self.player.pos_x))
            new_pipes.sort(key=lambda p: p[1])
            next_pipe = new_pipes[0][0]

            new_y_t = next_pipe.gap_start
            new_y_b = next_pipe.gap_start + self.pipe_gap
            new_del_x = next_pipe.x - self.player.pos_x
            new_x_p = next_pipe.x
            # print('new top: ', new_y_t, 'new bottom: ', new_y_b, 'new del x: ', new_del_x, 'new pipe x: ', new_x_p)
        else: # game contd.
            new_y_t = y_t
            new_y_b = y_b
            new_del_x = del_x - self.speed - 1
            new_x_p = x_p - self.speed -1

        x_delta_bin = np.digitize(new_del_x, self.feature_bins[self.feature_map['next_pipe_dist_to_player']])
        velocity_bin = np.digitize(new_v_a, self.feature_bins[self.feature_map['player_vel']])
        agent_pos_bin = np.digitize(new_y_a, self.feature_bins[self.feature_map['player_y']])
        pipe_x = np.digitize(new_x_p, self.feature_bins[self.feature_map['next_pipe_x']])
        if agent_pos_bin==len(self.feature_bins[self.feature_map['player_y']]):
            agent_pos_bin -= 1

        if velocity_bin==len(self.feature_bins[self.feature_map['player_vel']]):
            velocity_bin -= 1

        new_del_x = self.feature_bins[self.feature_map['next_pipe_dist_to_player']][x_delta_bin]
        new_v_a = self.feature_bins[self.feature_map['player_vel']][velocity_bin]
        new_y_a = self.feature_bins[self.feature_map['player_y']][agent_pos_bin]
        new_x_p = self.feature_bins[self.feature_map['next_pipe_x']][pipe_x]

        return [(new_y_b, new_del_x, new_y_t, new_x_p, new_v_a, new_y_a)], [success_prob]

    def get_reward(self, state, action):
        cross_pipe = +10
        loss = -10
        fly_high = +0.1
        step = 0
        # loss = fly_high = step
        pipe_type = None

        y_b, del_x, y_t, x_p, v_a, y_a = state
        gap_start = y_t


        top_pipe_check = ((y_a - self.player.height/2 + 12) <= gap_start) and (del_x==0 and x_p==self.player.pos_x)
        bot_pipe_check = ((y_a + self.player.height) > gap_start + self.pipe_gap) and (del_x==0 and x_p==self.player.pos_x)
        # top_pipe_check =

        if top_pipe_check:
            self.lives_left -= 1

        if bot_pipe_check:
            self.lives_left -= 1

        if del_x==0 and not top_pipe_check and not bot_pipe_check:
            return cross_pipe, pipe_type

        # fell on the ground
        if y_a >= 0.79 * self.height - self.player.height:
            self.lives_left -= 1
            return loss, pipe_type

        # went above the screen
        if y_a <= 0:
            self.lives_left -= 1
            return loss, pipe_type

        if y_a <= 50:
            return fly_high, pipe_type

        return step, pipe_type

    def is_past_pipe(self, state):
        y_b, del_x, y_t, x_p, v_a, y_a = state
        gap_start = y_t
        top_pipe_check = ((y_a - self.player.height/2 + 12) <= gap_start) and (del_x==0 and x_p<=self.player.pos_x)
        bot_pipe_check = ((y_a + self.player.height) > gap_start + self.pipe_gap) and (del_x==0 and x_p<=self.player.pos_x)
        if del_x==0 and not top_pipe_check and not bot_pipe_check:
            return True
        return False

    def is_crash(self, state):
        crashed = False
        y_b, del_x, y_t, x_p, v_a, y_a = state
        gap_start = y_t
        top_pipe_check = ((y_a - self.player.height/2 + 12) <= gap_start) and (del_x==0 and x_p<=self.player.pos_x)
        bot_pipe_check = ((y_a + self.player.height) > gap_start + self.pipe_gap) and (del_x==0 and x_p<=self.player.pos_x)

        if top_pipe_check or bot_pipe_check:
            crashed = True
        elif y_a >= 0.79 * self.height - self.player.height: # fell on the ground
            crashed = True
        elif y_a <= 0: # went above the screen
            crashed = True
        return crashed
