import os
import pygame
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.grid import Grid
from minigrid.core.world_object import Wall, Lava, Goal, Ball
from minigrid.core.actions import Actions
from minigrid.core.mission import MissionSpace
from PIL import Image
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import numpy as np

# Custom environment based on the parsed XML data
class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, environment_data, accurate_model=False, task='escLava', inaccuracy_type=None, goal_pos=None,
                 goal_dir=None, **kwargs):
        # Initialize environment data
        self.environment_data = environment_data

        # Extract grid size from Attributes
        grid_attr = next(attr for attr in self.environment_data['Attributes'] if attr['Name']['Value'] == 'Grid')
        grid_size = int(grid_attr['Value']['Content'])+2


        self.width = grid_size
        self.height = grid_size

        # Ensure the grid is square
        assert self.width == self.height, "Grid width and height must be the same for MiniGridEnv"

        # Initialize mission space
        mission_space = MissionSpace(mission_func=lambda: "Reach the goal while avoiding obstacles")

        # Call the parent initializer
        super().__init__(grid_size=self.width, mission_space=mission_space, **kwargs)

        self.step_count = 0
        self.dir = {'s': 0, 'w': 1, 'n': 2, 'e': 3}
        self.task = task
        self.inaccuracy_type = inaccuracy_type
        self.accurate_model = accurate_model
        self.action_mapping = {0: Actions.left, 1: Actions.right, 2: Actions.forward, 3: Actions.pickup}
        self.valid_actions = [Actions.left, Actions.right, Actions.forward, Actions.pickup]
        self.goal_pos = goal_pos
        self.goal_dir = goal_dir

    def _gen_grid(self, width, height):
        # Create an empty grid and set boundaries
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        # Place walls, landmines, and other objects based on the parsed XML data
        # Place objects from ObjectList
        for obj in self.environment_data['Objects']['ObjectList']:
            self.add_object_to_grid(obj)

        # Set agent's initial position
            # Set the agent's initial position and direction
            agent = self.environment_data['Agents']['AgentList'][0]
            self.agent_pos = (
                int(agent['Attributes'][0]['Value']['Content']),  # X position
                int(agent['Attributes'][1]['Value']['Content'])  # Y position
            )
            self.agent_dir = int(agent['Attributes'][2]['Value']['Content'])  # Direction

    # Set agent direction (convert angle to MiniGrid's direction)
        #direction = int(agent.direction[0].value)
        #self.agent_dir = direction  # Using the direction index (0: East, 1: South, etc.)

    def add_object_to_grid(self, obj):
        # Extract the object's position
        # Extract the object's position
        x = int(obj['Attributes'][0]['Value']['Content'])
        y = int(obj['Attributes'][1]['Value']['Content'])

        # Add objects like walls and landmines based on the parsed XML data
        if obj['Type'] == 'Wall':
            self.grid.set(x, y, Wall())
        elif obj['Type'] == 'Lava':
            self.grid.set(x, y, Lava())
        elif obj['Type'] == 'Goal':
            self.grid.set(x, y, Goal())
        elif obj['Type'] == 'Ball':
            self.grid.set(x, y, Ball())

    def step(self, action):
        self.step_count += 1

        # Update the agent's direction based on the action

        # Step through the environment and capture the results
        result = super().step(action)

        # Unpack the first four values (obs, reward, done, info) and ignore any extras
        obs, reward, done, info, *extra = result

        # Handle landmine (Lava) condition
        if isinstance(self.grid.get(*self.agent_pos), Lava):
            done = True
            reward = -1

        return obs, reward, done, info

    def reset(self):
        # Generate a new random grid at the start of each episode
        self._gen_grid(self.width, self.height)

        self.dir = {'s': 0, 'w': 1, 'n': 2, 'e': 3 }
        # These fields should be defined by _gen_grid
        assert (
            self.agent_pos >= (0, 0)
            if isinstance(self.agent_pos, tuple)
            else all(self.agent_pos >= 0) and self.agent_dir >= 0
        )

        # Check that the agent doesn't overlap with an object
        start_cell = self.agent_pos
        #assert start_cell is None or start_cell.can_overlap()

        # Return first observation
        obs = self.gen_obs()
        self.grid_list = np.array(self.grid.grid).reshape(self.width, self.height)
        self.grid_list = list(map(list, zip(*self.grid_list)))
        self.all_states = self.get_state_factor_rep()

        if self.task=='escLava':
            if self.inaccuracy_type in set([2, 3]):
                self.agent_curr_state = (self.agent_pos[0], self.agent_pos[1], self.agent_dir)
            else:
                if self.grid_list[self.agent_pos[0]][self.agent_pos[1]]!=None and self.grid_list[self.agent_pos[0]][self.agent_pos[1]].type=='lava':
                    self.agent_curr_state = (self.agent_pos[0], self.agent_pos[1], self.agent_dir, True)
                else:
                    self.agent_curr_state = (self.agent_pos[0], self.agent_pos[1], self.agent_dir, False)

        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([2, 3]):
                self.agent_curr_state = (self.agent_pos[0], self.agent_pos[1], self.agent_dir, False)
            else:
                self.agent_curr_state = (self.agent_pos[0], self.agent_pos[1], self.agent_dir, False, 'none', False)
        return obs

    def get_state_factor_rep(self):
        state_feature_rep = []
        for i in range(self.width):
            for j in range(self.height):
                for k in self.dir.values():
                    s = self.grid_list[i][j].type if self.grid_list[i][j]!=None else 'none'
                    if s!='wall':
                        if self.task=='escLava':
                            if self.inaccuracy_type in set([2, 3]):
                                state_feature_rep.append((i, j, k))
                            else:
                                state_feature_rep.append((i, j, k, True if s=='lava' else False))
                        elif self.task=='keyToGoal':
                            key_picked = [True, False]
                            for kp in key_picked:
                                if kp==False:
                                    if self.inaccuracy_type in set([2, 3]):
                                        state_feature_rep.append((i, j, k, kp))
                                    else:
                                        state_feature_rep.append((i, j, k, kp, 'none', True if s=='lava' else False))
                                elif kp==True:
                                    if self.inaccuracy_type in set([2, 3]):
                                        state_feature_rep.append((i, j, k, kp))
                                    else:
                                        for key_color in ['green', 'yellow', 'blue', 'grey', 'red']:
                                            state_feature_rep.append((i, j, k, kp, key_color, True if s=='lava' else False))
        return state_feature_rep

    def is_goal(self, state):
        if self.task=='escLava':
            if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[2]==self.goal_dir:
                return True
        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([0, 1]):
                if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[2]==self.goal_dir and state[3]==True and state[4]=='green':
                    return True
            else:
                if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[2]==self.goal_dir and state[3]==True:
                    if self.exe==True and self.picked_key_color=='green':
                        return True
                    elif self.exe==False:
                        return True
        return False

    def is_terminal(self, state):
        if self.task=='escLava':
            # if self.inaccuracy_type in set([2, 3]): # and self.exe==False:
            #     return False
            if self.inaccuracy_type in set([2, 3]): # and self.exe==True:
                if self.grid_list[state[0]][state[1]]!=None and self.grid_list[state[0]][state[1]].type=='lava':
                    return True
                else:
                    return False
            else:
                _, _, _, lava = state
        elif self.task=='keyToGoal':
            if self.inaccuracy_type in set([2, 3]) and self.exe==False:
                return False
            if self.inaccuracy_type in set([2, 3]) and self.exe==True:
                if self.grid_list[state[0]][state[1]]!=None and self.grid_list[state[0]][state[1]].type=='lava':
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
        # wrong_key = -10
        # correct_key = 10
        step_reward = -1
        x, y = state[0], state[1]

        if self.action_mapping[action] in self.valid_actions:
            if self.is_goal(state)==True:
                return goal_state

            if self.accurate_model==True:
                if self.is_terminal(state)==True:
                    return undesired_state
                # elif self.grid_list[y][x]!=None and self.grid_list[y][x].type=='key' and self.grid_list[y][x].color!='green':
                #     return wrong_key
                # elif self.grid_list[y][x]!=None and self.grid_list[y][x].type=='key' and self.grid_list[y][x].color=='green':
                #     return correct_key
                else:
                    return step_reward
            else:
                return step_reward
        return state_reward

    def is_boundary(self, state):
        x, y = state
        if (x <= 0 or x >= self.height-1 or y <= 0 or y >= self.width-1):
            return True
        elif self.grid_list[x][y]!=None and self.grid_list[x][y].type=='wall':
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
            if direction==0: # v
                new_coords = tuple(x + y for (x, y) in zip((x, y), (0, 1)))
            elif direction==1: # <
                new_coords = tuple(x + y for (x, y) in zip((x, y), (-1, 0)))
            elif direction==2: # ^
                new_coords = tuple(x + y for (x, y) in zip((x, y), (0, -1)))
            elif direction==3: # >
                new_coords = tuple(x + y for (x, y) in zip((x, y), (1, 0)))

            i, j = new_coords[0], new_coords[1]
            if self.is_boundary(new_coords):
                return curr_state, True
            else:
                s = self.grid_list[i][j].type if self.grid_list[i][j]!=None else 'none'
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
            if self.grid_list[x][y]!=None:
                if self.grid_list[x][y].type=='key' and key==False:
                    self.picked_key_color = str(self.grid_list[x][y].color).lower()
                    if self.inaccuracy_type in set([2, 3]):
                        return (x, y, direction, True), False
                    else:
                        return (x, y, direction, True, str(self.grid_list[x][y].color).lower(), lava), False

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

    def agent_step(self, action):
        terminal = False
        successors, succ_probabilities = self.get_successors(self.agent_curr_state, action)
        next_state_idx = np.random.choice(len(successors), p=succ_probabilities)
        self.agent_curr_state = successors[next_state_idx]
        reward = self.get_reward(self.agent_curr_state, action)
        if self.is_goal(self.agent_curr_state) or self.is_terminal(self.agent_curr_state):
            terminal = True
        return successors[next_state_idx], reward, succ_probabilities[next_state_idx], terminal



def map_user_input_to_action(user_input):
    action_map = {
        'forward': Actions.forward,
        'left': Actions.left,
        'right': Actions.right,
        'pickup': Actions.pickup,
        'drop': Actions.drop,
        'toggle': Actions.toggle
    }
    return action_map.get(user_input, None)
