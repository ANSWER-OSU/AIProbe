from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.mission import MissionSpace
from minigrid.core.grid import Grid
from Minigrid.EnvironmentState import State
from minigrid.core.world_object import Lava, Goal, Door, Key, Wall, Ball
from minigrid.core.actions import Actions
import numpy as np

class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, grid_spec=State, grid_size=None, accurate_model=False, task='escLava', **kwargs):
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

        ## Place a goal square in the bottom-right corner
        # self.put_obj(Goal(), self.goal_pos[0], self.goal_pos[1])

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
                            state_feature_rep.append((j, i, k, True if s=='lava' else False))
                        elif self.task=='keyToGoal':
                            for key in ['green', 'yellow', 'none']:
                                state_feature_rep.append((j, i, k, key))
        return state_feature_rep


    def reset(self):
        self.dir = {'e': 0, 's': 1, 'w': 2, 'n': 3 }
        if self.task=='escLava':
            self.agent_curr_state = (self.agent_start_pos[0], self.agent_start_pos[1], self.agent_start_dir, False)
        elif self.task=='keyToGoal':
            self.agent_curr_state = (self.agent_start_pos[0], self.agent_start_pos[1], self.agent_start_dir, 'none')
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
            if state[0]==self.goal_pos[0] and state[1]==self.goal_pos[1] and state[3]=='green': # at the goal state with GREEN key
                return True
        return False

    def is_terminal(self, state):
        if self.task=='escLava':
            _, _, _, lava = state
            if lava:
                return True
        return False


    def get_reward(self, state, action):
        state_reward = None
        goal_state = 100
        undesired_state = -100
        step_reward = -1

        if self.action_mapping[action] in self.valid_actions:
            if self.is_goal(state)==True:
                return goal_state

            if self.accurate_model==True:
                if self.is_terminal(state)==True:
                    return undesired_state
                else:
                    return step_reward
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
        x, y, direction, state_feature = curr_state
        new_direction = None
        # Turn left
        if action == Actions.left:
            new_direction = direction-1
            if new_direction < 0:
                new_direction += 4
            return (x, y, new_direction, state_feature), False

        # Turn right
        elif action == Actions.right:
            new_direction = (direction+1) % 4
            return (x, y, new_direction, state_feature), False

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
                        new_state_feature_val = True if s=='lava' else False
                    elif self.task=='keyToGoal':
                        new_state_feature_val = state_feature
                return (i, j, direction, new_state_feature_val), False

        elif action == Actions.pickup:
            if self.grid_list[y][x]!=None:
                if self.grid_list[y][x].type=='key' and state_feature=='none':
                    return (x, y, direction, str(self.grid_list[y][x].color).lower()), False
        return (x, y, direction, state_feature), False




    def get_transition(self, curr_state, action, next_state):
        # print('curr_state: ', curr_state, 'action: ', action)
        succ_factored_state, is_wall = self.move(curr_state, action)
        # print('succ_factored_state: ', curr_state)
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
            # print(state, action)
            next_state, _ = self.move(state, action)
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
