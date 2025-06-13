# import os
# import pygame
# from minigrid.minigrid_env import MiniGridEnv
# from minigrid.core.grid import Grid
# from minigrid.core.world_object import Wall, Lava, Goal
# from minigrid.core.actions import Actions
# from minigrid.core.mission import MissionSpace
# from PIL import Image
# os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
# import numpy as np
# from gymnasium import spaces

# class CustomMiniGridEnv(MiniGridEnv):
#     def __init__(self, environment_data, accurate_model=False, task='escLava', inaccuracy_type=None, goal_pos=None,
#                  goal_dir=None, **kwargs):
#         self.environment_data = environment_data
#         grid_attr = next(attr for attr in self.environment_data['Attributes'] if attr['Name']['Value'] == 'Grid')
#         grid_size = int(grid_attr['Value']['Content']) + 2
#         self.width = self.height = grid_size

#         mission_space = MissionSpace(mission_func=lambda: "Reach the goal while avoiding obstacles")
#         kwargs.pop("grid_size", None)
#         super().__init__(grid_size=grid_size, mission_space=mission_space, render_mode='rgb_array', **kwargs)

#         self.task = task
#         self.inaccuracy_type = inaccuracy_type
#         self.accurate_model = accurate_model
#         self.action_mapping = {0: Actions.left, 1: Actions.right, 2: Actions.forward}
#         self.valid_actions = list(self.action_mapping.values())

#         self.goal_pos = goal_pos
#         self.goal_dir = goal_dir
#         self.max_steps = 100  # or any cap you want

#         # Example state: (x, y, dir, step_count[, lava])
#         example_state = (1, 1, 0, 0) if inaccuracy_type in [2, 3] else (1, 1, 0, 0, 0)
#         self.observation_space = spaces.Box(low=0, high=grid_size, shape=(len(example_state),), dtype=np.float32)
#         self.action_space = spaces.Discrete(len(self.valid_actions))

#     def _gen_grid(self, width, height):
#         self.grid = Grid(width, height)
#         self.grid.wall_rect(0, 0, width, height)
#         for obj in self.environment_data['Objects']['ObjectList']:
#             self.add_object_to_grid(obj)
#         agent = self.environment_data['Agents']['AgentList'][0]
#         self.agent_pos = (int(agent['Attributes'][0]['Value']['Content']),
#                           int(agent['Attributes'][1]['Value']['Content']))
#         self.agent_dir = int(agent['Attributes'][2]['Value']['Content'])

#     def add_object_to_grid(self, obj):
#         x = int(obj['Attributes'][0]['Value']['Content'])
#         y = int(obj['Attributes'][1]['Value']['Content'])
#         obj_type = obj['Type']
#         if obj_type == 'Wall': self.grid.set(x, y, Wall())
#         elif obj_type == 'Lava': self.grid.set(x, y, Lava())
#         elif obj_type == 'Goal': self.grid.set(x, y, Goal())

#     def reset(self, seed=None, options=None):
#         super().reset(seed=seed)
#         self._gen_grid(self.width, self.height)
#         self.grid_list = np.array(self.grid.grid).reshape(self.width, self.height)
#         self.grid_list = list(map(list, zip(*self.grid_list)))
#         self.all_states = self.get_state_factor_rep()

#         x, y = self.agent_pos
#         d = self.agent_dir
#         lava = 1 if self.grid_list[x][y] and self.grid_list[x][y].type == 'lava' else 0
#         self.agent_curr_state = (x, y, d, 0) if self.inaccuracy_type in [2, 3] else (x, y, d, 0, lava)
#         return np.array(self.agent_curr_state, dtype=np.float32), {}

#     def get_state_factor_rep(self):
#         state_feature_rep = []
#         for x in range(self.width):
#             for y in range(self.height):
#                 cell_type = self.grid_list[x][y].type if self.grid_list[x][y] else 'none'
#                 if cell_type != 'wall':
#                     for d in range(4):
#                         for step in range(self.max_steps):
#                             if self.inaccuracy_type in [2, 3]:
#                                 state_feature_rep.append((x, y, d, step))
#                             else:
#                                 lava = 1 if cell_type == 'lava' else 0
#                                 state_feature_rep.append((x, y, d, step, lava))
#         return state_feature_rep

#     def is_goal(self, state):
#         return self.task == 'escLava' and state[0:2] == self.goal_pos

#     def is_terminal(self, state):
#         x, y = state[0], state[1]
#         return self.grid_list[x][y] and self.grid_list[x][y].type == 'lava'

#     # def get_reward(self, state, action):
#     #     x, y = state[0], state[1]
#     #     if self.is_goal(state): return 1
#     #     if self.grid_list[x][y] and self.grid_list[x][y].type == 'lava': return -1
#     #     return -0.01

#     def get_reward(self, state, action):
#         x, y = state[0], state[1]
#         step_count = state[3] 
#         if self.is_goal(state):
#             return 1 - (0.9 * step_count / self.max_steps)
#         if self.grid_list[x][y] and self.grid_list[x][y].type == 'lava':
#             return -1
#         return 0

#     def is_boundary(self, pos):
#         x, y = pos
#         return x <= 0 or y <= 0 or x >= self.width - 1 or y >= self.height - 1 or \
#                (self.grid_list[x][y] and self.grid_list[x][y].type == 'wall')

#     def move(self, curr_state, action):
#         if self.inaccuracy_type in [2, 3]:
#             x, y, dir, step = curr_state
#         else:
#             x, y, dir, step, lava = curr_state

#         # Update direction
#         if action == Actions.left:
#             dir = (dir - 1) % 4
#         elif action == Actions.right:
#             dir = (dir + 1) % 4

#         # Compute next position
#         nx, ny = x, y
#         if action == Actions.forward:
#             if dir == 0: ny += 1  # down
#             elif dir == 1: nx -= 1  # left
#             elif dir == 2: ny -= 1  # up
#             elif dir == 3: nx += 1  # right

#         step = min(step + 1, self.max_steps - 1)
#         if self.is_boundary((nx, ny)):
#             return ((x, y, dir, step) if self.inaccuracy_type in [2, 3] else (x, y, dir, step, lava)), True

#         cell_type = self.grid_list[nx][ny].type if self.grid_list[nx][ny] else 'none'
#         if self.inaccuracy_type in [2, 3]:
#             return (nx, ny, dir, step), False
#         else:
#             new_lava = 1 if cell_type == 'lava' else 0
#             return (nx, ny, dir, step, new_lava), False

#     def get_possible_next_states(self, state):
#         return {self.move(state, a)[0] for a in self.action_mapping}

#     def get_transition(self, curr_state, action, next_state):
#         succ_state, hit_wall = self.move(curr_state, action)
#         return 1.0 if next_state == succ_state else 0.0

#     def get_successors(self, state, action):
#         succ, prob = self.move(state, action)
#         return [succ], [1.0]

#     def agent_step(self, action):
#         successors, probs = self.get_successors(self.agent_curr_state, action)
#         next_state = successors[0]
#         self.agent_curr_state = next_state
#         reward = self.get_reward(next_state, action)
#         done = self.is_goal(next_state) or self.is_terminal(next_state)
#         return next_state, reward, 1.0, done

'''
No dir in the state space
'''

import os
import pygame
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.grid import Grid
from minigrid.core.world_object import Wall, Lava, Goal
from minigrid.core.actions import Actions
from minigrid.core.mission import MissionSpace
from PIL import Image
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import numpy as np
from gymnasium import spaces

class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, environment_data, accurate_model=False, task='escLava', inaccuracy_type=None, goal_pos=None,
                 goal_dir=None, **kwargs):
        self.environment_data = environment_data
        grid_attr = next(attr for attr in self.environment_data['Attributes'] if attr['Name']['Value'] == 'Grid')
        grid_size = int(grid_attr['Value']['Content']) + 2
        self.width = self.height = grid_size

        mission_space = MissionSpace(mission_func=lambda: "Reach the goal while avoiding obstacles")
        kwargs.pop("grid_size", None)
        super().__init__(grid_size=grid_size, mission_space=mission_space, render_mode='rgb_array', **kwargs)

        self.task = task
        self.inaccuracy_type = inaccuracy_type
        self.accurate_model = accurate_model
        self.action_mapping = {0: Actions.left, 1: Actions.right, 2: Actions.forward}
        self.valid_actions = list(self.action_mapping.values())

        self.goal_pos = goal_pos
        self.goal_dir = goal_dir
        self.max_steps = 100

        example_state = (1, 1, 0) if inaccuracy_type in [2, 3] else (1, 1, 0, 0)
        self.observation_space = spaces.Box(low=0, high=grid_size, shape=(len(example_state),), dtype=np.float32)
        self.action_space = spaces.Discrete(len(self.valid_actions))

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)
        for obj in self.environment_data['Objects']['ObjectList']:
            self.add_object_to_grid(obj)
        agent = self.environment_data['Agents']['AgentList'][0]
        self.agent_pos = (int(agent['Attributes'][0]['Value']['Content']),
                          int(agent['Attributes'][1]['Value']['Content']))
        self.agent_dir = int(agent['Attributes'][2]['Value']['Content'])

    def add_object_to_grid(self, obj):
        x = int(obj['Attributes'][0]['Value']['Content'])
        y = int(obj['Attributes'][1]['Value']['Content'])
        obj_type = obj['Type']
        if obj_type == 'Wall': self.grid.set(x, y, Wall())
        elif obj_type == 'Lava': self.grid.set(x, y, Lava())
        elif obj_type == 'Goal': self.grid.set(x, y, Goal())

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._gen_grid(self.width, self.height)
        self.grid_list = np.array(self.grid.grid).reshape(self.width, self.height)
        self.grid_list = list(map(list, zip(*self.grid_list)))
        self.all_states = self.get_state_factor_rep()

        x, y = self.agent_pos
        lava = 1 if self.grid_list[x][y] and self.grid_list[x][y].type == 'lava' else 0
        self.agent_curr_state = (x, y, 0) if self.inaccuracy_type in [2, 3] else (x, y, 0, lava)
        return np.array(self.agent_curr_state, dtype=np.float32), {}

    def get_state_factor_rep(self):
        state_feature_rep = []
        for x in range(self.width):
            for y in range(self.height):
                cell_type = self.grid_list[x][y].type if self.grid_list[x][y] else 'none'
                if cell_type != 'wall':
                    for step in range(self.max_steps):
                        if self.inaccuracy_type in [2, 3]:
                            state_feature_rep.append((x, y, step))
                        else:
                            lava = 1 if cell_type == 'lava' else 0
                            state_feature_rep.append((x, y, step, lava))
        return state_feature_rep

    def is_goal(self, state):
        return self.task == 'escLava' and (state[0], state[1]) == self.goal_pos

    def is_terminal(self, state):
        x, y = state[0], state[1]
        # return self.grid_list[x][y] and self.grid_list[x][y].type == 'lava'
        return False

    def get_reward(self, state, action):
        x, y = state[0], state[1]
        step_count = state[2]
        if self.is_goal(state):
            return 1 - (0.9 * step_count / self.max_steps)
        if self.inaccuracy_type in [0, 2]:
            if self.grid_list[x][y] and self.grid_list[x][y].type == 'lava':
                return -1
        return 0

    def is_boundary(self, pos):
        x, y = pos
        return x <= 0 or y <= 0 or x >= self.width - 1 or y >= self.height - 1 or \
               (self.grid_list[x][y] and self.grid_list[x][y].type == 'wall')

    def move(self, curr_state, action):
        if self.inaccuracy_type in [2, 3]:
            x, y, step = curr_state
        else:
            x, y, step, lava = curr_state

        dir = self.agent_dir  # agent direction is internal

        # Rotate in place
        if action == Actions.left:
            dir = (dir - 1) % 4
        elif action == Actions.right:
            dir = (dir + 1) % 4

        # Move forward
        nx, ny = x, y
        if action == Actions.forward:
            if dir == 0: ny += 1  # down
            elif dir == 1: nx -= 1  # left
            elif dir == 2: ny -= 1  # up
            elif dir == 3: nx += 1  # right

        step = min(step + 1, self.max_steps - 1)
        self.agent_dir = dir  # update internal direction

        if self.is_boundary((nx, ny)):
            return ((x, y, step) if self.inaccuracy_type in [2, 3] else (x, y, step, lava)), True

        cell_type = self.grid_list[nx][ny].type if self.grid_list[nx][ny] else 'none'
        if self.inaccuracy_type in [2, 3]:
            return (nx, ny, step), False
        else:
            new_lava = 1 if cell_type == 'lava' else 0
            return (nx, ny, step, new_lava), False

    def get_possible_next_states(self, state):
        return {self.move(state, a)[0] for a in self.action_mapping}

    def get_transition(self, curr_state, action, next_state):
        succ_state, hit_wall = self.move(curr_state, action)
        return 1.0 if next_state == succ_state else 0.0

    def get_successors(self, state, action):
        succ, prob = self.move(state, action)
        return [succ], [1.0]

    def agent_step(self, action):
        successors, probs = self.get_successors(self.agent_curr_state, action)
        next_state = successors[0]
        self.agent_curr_state = next_state
        reward = self.get_reward(next_state, action)
        done = self.is_goal(next_state) or self.is_terminal(next_state)
        return next_state, reward, 1.0, done

