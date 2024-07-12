from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.mission import MissionSpace
from minigrid.core.grid import Grid
from Minigrid.EnvironmentState import State
from minigrid.core.world_object import Lava, Goal, Door, Key, Wall, Ball
from minigrid.core.actions import Actions
import numpy as np

from minigrid.core.world_object import WorldObj
from minigrid.core.constants import COLOR_NAMES, COLORS
from minigrid.core.world_object import WorldObj
from minigrid.core.constants import COLORS
from minigrid.core.world_object import WorldObj
from minigrid.core.constants import OBJECT_TO_IDX, IDX_TO_OBJECT, COLORS
from minigrid.core.constants import COLOR_NAMES, COLOR_TO_IDX, COLORS
from PIL import Image

if 'orange' not in COLORS:
    COLORS['orange'] = np.array([255, 165, 0])

if 'orange' not in COLOR_TO_IDX:
    COLOR_TO_IDX['orange'] = len(COLOR_TO_IDX)

def fill_coords(img, coords, color):
    for x, y in coords:
        if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
            img[int(y)][int(x)] = color

def point_in_circle(cx, cy, r, cell_size):
    points = []
    for y in range(int(cy * cell_size - r * cell_size), int(cy * cell_size + r * cell_size) + 1):
        for x in range(int(cx * cell_size - r * cell_size), int(cx * cell_size + r * cell_size) + 1):
            if (x - cx * cell_size) ** 2 + (y - cy * cell_size) ** 2 <= (r * cell_size) ** 2:
                points.append((x, y))
    return points

class Landmine(WorldObj):
    def __init__(self, x, y, is_present):
        super().__init__('landmine', 'orange')
        self.x = x
        self.y = y
        self.is_present = is_present

    def can_overlap(self):
        return False

    def see_behind(self):
        return True

    def render(self, img):
        c = COLORS[self.color]
        cell_size = 32  # Define the cell size, typically 32 pixels
        coords = point_in_circle(1.5, 1.5, 0.5, cell_size)  # Centered circle with larger radius
        for coord in coords:
            if 0 <= coord[1] < img.shape[0] and 0 <= coord[0] < img.shape[1]:
                img[int(coord[1]), int(coord[0]), :] = c

OBJECT_TO_IDX['landmine'] = len(OBJECT_TO_IDX)
IDX_TO_OBJECT[len(IDX_TO_OBJECT)] = 'landmine'

class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, grid_spec=State, grid_size=None, accurate_model=False, task='escLava', inaccuracy_type=None, **kwargs):
        self.dir = {'e': 0, 's': 1, 'w': 2, 'n': 3 }
        self.width = self.height = grid_size
        self.grid_size = [self.width, self.height]
        self.grid_spec = grid_spec
        self.agent_start_pos = self.grid_spec.agent.init_pos
        self.agent_start_dir = self.dir[self.grid_spec.agent.init_direction]
        self.goal_pos = self.grid_spec.agent.dest_pos
        self.goal_dir = self.dir[self.grid_spec.agent.dest_direction]
        self.valid_actions = [Actions.left, Actions.right, Actions.forward, Actions.pickup]
        self.action_mapping = {0: Actions.left, 1: Actions.right, 2: Actions.forward, 3: Actions.pickup}
        self.accurate_model = accurate_model
        self.agent_curr_state = None
        self.all_states = None
        self.task = task
        self.inaccuracy_type = inaccuracy_type
        self.grid_list = None
        self.exe = False
        self.picked_key_color = None
        mission_space = MissionSpace(mission_func=self._gen_mission)
        super().__init__(
                    width=self.width,
                    height=self.height,
                    mission_space=mission_space,
                    see_through_walls=True,
                    **kwargs)

    @staticmethod
    def _gen_mission():
        return "Escape Lava And Reach Destination"

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        for door in self.grid_spec.doors:
            door_color = door.color if hasattr(door, 'color') else 'yellow'  # Default color
            is_locked = bool(door.door_status)  # Default unlocked
            self.grid.set(door.x, door.y, Door(door_color, is_open=door.door_status, is_locked=door.door_locked))

        for key in self.grid_spec.keys:
            is_present=bool(key.is_present)
            if not is_present:
                continue
            else:
                key_color = key.color
                is_picked = bool(key.is_picked)
                if not is_picked:
                    self.grid.set(key.x_init, key.y_init, Key(key_color))

        for object in self.grid_spec.objects:
            is_present = bool(object.is_present)
            if is_present:
                obj_color = object.color
                self.grid.set(object.x,object.y, Ball())

        # Place lava cells
        for lava in self.grid_spec.lava_tiles:
            is_present = bool(lava.is_present)
            if is_present:
                lava_color = 'red'
                self.grid.set(lava.x, lava.y, Lava())
            else:
                continue

        for wall in self.grid_spec.walls:
            self.grid.set(wall.x, wall.y, Wall())
            self.grid.get(wall.x, wall.y).color = 'blue'

        for landmine in self.grid_spec.landmines:
            is_present = bool(landmine.is_present)
            if is_present:
                self.grid.set(landmine.x, landmine.y, Landmine(landmine.x, landmine.y, is_present))
            else:
                continue

        # Place a destination square
        # destination_position = self.initial_state.agent.dest_pos
        self.grid.set(self.goal_pos[0], self.goal_pos[1], Goal())
        self.grid.get(self.goal_pos[0], self.goal_pos[1]).color = 'green'

         # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "Escape Lava And Reach Destination"

    def get_state_factor_rep(self):
        state_feature_rep = []
        for i in range(self.width):
            for j in range(self.height):
                for k in self.dir.values():
                    s = self.grid_list[i][j].type if self.grid_list[i][j]!=None else 'none'
                    if s!='wall':
                        if self.task=='escLava':
                            if self.inaccuracy_type in set([2, 3]):
                                state_feature_rep.append((j, i, k))
                            else:
                                state_feature_rep.append((j, i, k, True if s=='lava' else False))
                        elif self.task=='keyToGoal':
                            key_picked = [True, False]
                            for kp in key_picked:
                                if kp==False:
                                    if self.inaccuracy_type in set([2, 3]):
                                        state_feature_rep.append((j, i, k, kp))
                                    else:
                                        state_feature_rep.append((j, i, k, kp, 'none', True if s=='lava' else False))
                                elif kp==True:
                                    if self.inaccuracy_type in set([2, 3]):
                                        state_feature_rep.append((j, i, k, kp))
                                    else:
                                        for key_color in ['green', 'yellow', 'blue', 'grey', 'red']:
                                            state_feature_rep.append((j, i, k, kp, key_color, True if s=='lava' else False))
        return state_feature_rep


    def reset(self):
        self.dir = {'e': 0, 's': 1, 'w': 2, 'n': 3 }
        if self.task=='escLava':
            if self.inaccuracy_type in set([2, 3]):
                self.agent_curr_state = (self.agent_start_pos[0], self.agent_start_pos[1], self.agent_start_dir)
            else:
                self.agent_curr_state = (self.agent_start_pos[0], self.agent_start_pos[1], self.agent_start_dir, False)

        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([2, 3]):
                self.agent_curr_state = (self.agent_start_pos[0], self.agent_start_pos[1], self.agent_start_dir, False)
            else:
                self.agent_curr_state = (self.agent_start_pos[0], self.agent_start_pos[1], self.agent_start_dir, False, 'none', False)
        # Generate a new random grid at the start of each episode
        self._gen_grid(self.width, self.height)

        # These fields should be defined by _gen_grid
        assert (
            self.agent_pos >= (0, 0)
            if isinstance(self.agent_pos, tuple)
            else all(self.agent_pos >= 0) and self.agent_dir >= 0
        )

        # Check that the agent doesn't overlap with an object
        start_cell = self.grid.get(*self.agent_pos)
        assert start_cell is None or start_cell.can_overlap()

        # Return first observation
        obs = self.gen_obs()
        self.grid_list = np.array(self.grid.grid).reshape(self.width, self.height)
        self.all_states = self.get_state_factor_rep()
        return obs

    def is_goal(self, state):
        if self.task=='escLava':
            if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1]:
                return True
        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([0, 1]):
                if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[3]==True and state[4]=='green':
                    return True
            else:
                if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[3]==True:
                    if self.exe==True and self.picked_key_color=='green':
                        return True
                    elif self.exe==False:
                        return True
        return False

    def is_terminal(self, state):
        if self.task=='escLava':
            if self.inaccuracy_type in set([2, 3]) and self.exe==False:
                return False
            if self.inaccuracy_type in set([2, 3]) and self.exe==True:
                if self.grid_list[state[1]][state[0]]!=None and self.grid_list[state[1]][state[0]].type=='lava':
                    return True
                else:
                    return False
            else:
                _, _, _, lava = state
        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([2, 3]) and self.exe==False:
                return False
            if self.inaccuracy_type in set([2, 3]) and self.exe==True:
                if self.grid_list[state[1]][state[0]]!=None and self.grid_list[state[1]][state[0]].type=='lava':
                    return True
                elif state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[3]==True and self.picked_key_color!='green':
                    return True
                return False
            else:
                _, _, _, _, _, lava = state

        if lava:
            return True
        return False


    def get_reward(self, state, action):
        state_reward = None
        goal_state = 100
        undesired_state = -200
        wrong_key = -10
        correct_key = 10
        step_reward = -1
        x, y = state[0], state[1]

        if self.action_mapping[action] in self.valid_actions:
            if self.is_goal(state)==True:
                return goal_state

            if self.accurate_model==True:
                if self.is_terminal(state)==True:
                    return undesired_state
                elif self.grid_list[y][x]!=None and self.grid_list[y][x].type=='key' and self.grid_list[y][x].color!='green':
                    return wrong_key
                else:
                    return step_reward
            else:
                # 2: '_accurate_reward_inaccurate_state_rep'
                if (self.inaccuracy_type==2 and self.is_terminal(state)==True):
                    if self.grid_list[state[1]][state[0]]!=None and self.grid_list[state[1]][state[0]].type=='lava':
                        return undesired_state
                    elif state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[3]==True and self.picked_key_color!='green':
                        return wrong_key
                    elif state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[3]==True and self.picked_key_color=='green':
                        return correct_key
                else:
                    return step_reward
        return state_reward

    def is_boundary(self, state):
        x, y = state
        if (x <= 0 or x >= self.height-1 or y <= 0 or y >= self.width-1):
            return True
        elif self.grid_list[y][x]!=None and self.grid_list[y][x].type=='wall':
            return True
        return False

    def move(self, curr_state, action):
        if self.task=='escLava':
            if self.inaccuracy_type in set([2, 3]):
                x, y, direction = curr_state
            else:
                x, y, direction, lava = curr_state
        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([2, 3]):
                x, y, direction, key = curr_state
            else:
                x, y, direction, key, key_color, lava = curr_state
        new_direction = None
        # Turn left
        if action == Actions.left:
            new_direction = direction-1
            if new_direction < 0:
                new_direction += 4
            if self.task=='escLava':
                if self.inaccuracy_type in set([2, 3]):
                    return (x, y, new_direction), False
                else:
                    return (x, y, new_direction, lava), False
            elif self.task=='keyToGoal':
                if self.inaccuracy_type in set([2, 3]):
                    return (x, y, new_direction, key), False
                else:
                    return (x, y, new_direction, key, key_color, lava), False

        # Turn right
        elif action == Actions.right:
            new_direction = (direction+1) % 4
            if self.task=='escLava':
                if self.inaccuracy_type in set([2, 3]):
                    return (x, y, new_direction), False
                else:
                    return (x, y, new_direction, lava), False
            elif self.task=='keyToGoal':
                if self.inaccuracy_type in set([2, 3]):
                    return (x, y, new_direction, key), False
                else:
                    return (x, y, new_direction, key, key_color, lava), False

        # Move forward
        elif action == Actions.forward:
            if direction==0: # >
                new_coords = tuple(x + y for (x, y) in zip((x, y), (1, 0)))
            elif direction==1: # v
                new_coords = tuple(x + y for (x, y) in zip((x, y), (0, 1)))
            elif direction==2: # <
                new_coords = tuple(x + y for (x, y) in zip((x, y), (-1, 0)))
            elif direction==3: # ^
                new_coords = tuple(x + y for (x, y) in zip((x, y), (0, -1)))

            i, j = new_coords[0], new_coords[1]
            if self.is_boundary(new_coords):
                return curr_state, True
            else:
                s = self.grid_list[j][i].type if self.grid_list[j][i]!=None else 'none'
                if s!='wall':
                    if self.task=='escLava':
                        if self.inaccuracy_type in set([2, 3]):
                            return (i, j, direction), False
                        else:
                            new_lava_val = True if s=='lava' else False
                            return (i, j, direction, new_lava_val), False
                    elif self.task=='keyToGoal':
                        if self.inaccuracy_type in set([2, 3]):
                            return (i, j, direction, key), False
                        else:
                            # new_key_val = key
                            new_lava_val = True if s=='lava' else False
                            return (i, j, direction, key, key_color, new_lava_val), False

        elif action == Actions.pickup:
            if self.grid_list[y][x]!=None:
                if self.grid_list[y][x].type=='key' and key==False:
                    self.picked_key_color = str(self.grid_list[y][x].color).lower()
                    if self.inaccuracy_type in set([2, 3]):
                        return (x, y, direction, True), False
                    else:
                        return (x, y, direction, True, str(self.grid_list[y][x].color).lower(), lava), False

        if self.task=='escLava':
            if self.inaccuracy_type in set([2, 3]):
                return (x, y, direction), False
            return (x, y, direction, lava), False
        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([2, 3]):
                return (x, y, direction, key), False
            return (x, y, direction, key, key_color, lava), False




    def get_transition(self, curr_state, action, next_state):
        succ_factored_state, is_wall = self.move(curr_state, action)
        if self.action_mapping[action] in self.valid_actions:
            success_prob = 1

            if is_wall:
                transition_probs = []
                for feature_idx in range(len(curr_state)):
                    if (curr_state[feature_idx] == next_state[feature_idx]):
                        transition_probs.append(1)
                    else:
                        transition_probs.append(0)
                return np.prod(transition_probs)

            elif not is_wall:
                transition_probs = []
                if (next_state[0]==succ_factored_state[0] and next_state[1]==succ_factored_state[1]):
                    transition_probs.append(success_prob)
                    for i in range(2, len(next_state)):
                        if (next_state[i]==succ_factored_state[i]):
                            transition_probs.append(1)
                        elif (next_state[i]!=succ_factored_state[i]):
                            transition_probs.append(0)
                    return np.prod(transition_probs)
        return 0

    def get_possible_next_states(self, state):
        possible_states = set()
        action_set = list(self.action_mapping.keys())
        for action in action_set:
            next_state, _= self.move(state, action)
            possible_states.add(next_state)
        return possible_states

    def get_successors(self, state, action):
        successors, succ_probabilities = [], []
        for next_state in self.get_possible_next_states(state):
            p = self.get_transition(state, action, next_state)
            if p > 0:
                successors.append(next_state)
                succ_probabilities.append(p)
        return successors, succ_probabilities

    def step(self, action):
        terminal = False
        successors, succ_probabilities = self.get_successors(self.agent_curr_state, action)
        next_state_idx = np.random.choice(len(successors), p=succ_probabilities)
        self.agent_curr_state = successors[next_state_idx]
        reward = self.get_reward(self.agent_curr_state, action)
        if self.is_goal(self.agent_curr_state) or self.is_terminal(self.agent_curr_state):
            terminal = True
        return successors[next_state_idx], reward, succ_probabilities[next_state_idx], terminal
