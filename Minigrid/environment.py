import pygame
from minigrid.core.actions import Actions

from Fuzzer.LoadConfig import  State, loadSetting
from Minigrid.EnvironmentState import  State,Agent, Door, Key, Object, Lava, State,load_InitialState,Landmines
from minigrid.core.constants import COLOR_NAMES
from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.world_object import Door, Goal, Key, Wall, Lava, Ball
import os
from Minigrid.agentPosition import check_environment_changes
from datetime import datetime
from Minigrid.CapabilitiesChecker import hypothesisCapabilities, check_task_achieved

import requests
import numpy as np
import json
import traceback

from minigrid.core.world_object import WorldObj
from minigrid.core.constants import COLOR_NAMES, COLORS
from minigrid.core.world_object import WorldObj


from minigrid.core.constants import COLORS
from minigrid.core.world_object import WorldObj
from minigrid.core.constants import OBJECT_TO_IDX, IDX_TO_OBJECT, COLORS
from PIL import Image

from minigrid.core.constants import COLOR_NAMES, COLOR_TO_IDX, COLORS



class NonBlockingKey(Key):
    def __init__(self, color='blue'):
        super().__init__(color)

    def can_pickup(self):
        # Override to make the key non-pickable
        return False

    def can_overlap(self):
        # Override to make the key not block the agent's movement
        return True

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
    def __init__(self, state: State,grid_size=None, **kwargs):
        self.initial_state = state
        self.final_state = state
        mission_space = MissionSpace(mission_func=lambda: "Escape Lava And Reach Destination")
        self.coverage = {}

        super().__init__(
            grid_size=grid_size,
            mission_space=mission_space,
            #max_steps=100,

            **kwargs
        )

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        self.agent_pos = self.initial_state.agent.init_pos

        direction_map = {
            'n': 3,
            's': 1,
            'e': 0,
            'w': 2
        }
        self.agent_dir = 1
        self.agent_dir = direction_map.get(self.initial_state.agent.dest_direction, 0)

        start_cell = self.grid.get(*self.agent_pos)
        if start_cell is not None and not start_cell.can_overlap():
            raise ValueError(f"Initial position {self.agent_pos} is occupied by a non-overlapping object.")

        for door in self.initial_state.doors:
            door_color = door.color if hasattr(door, 'color') else 'yellow'
            is_locked = bool(door.door_status)
            self.grid.set(door.x, door.y, Door(door_color, is_open=door.door_status, is_locked=door.door_locked))

        for key in self.initial_state.keys:
            is_present = bool(key.is_present)
            if is_present:
                key_color = key.color
                self.grid.set(key.x_init, key.y_init, NonBlockingKey(key_color))

        for lava in self.initial_state.lava_tiles:
            is_present = bool(lava.is_present)
            if is_present:
                lava_color = 'red'
                self.grid.set(lava.x, lava.y, Lava())
            else:
                continue

        for object in self.initial_state.objects:
            is_present = bool(object.is_present)
            if is_present:
                obj_color = object.color
                self.grid.set(object.x, object.y, Ball())

        for wall in self.initial_state.walls:
            self.grid.set(wall.x, wall.y, Wall())
            self.grid.get(wall.x, wall.y).color = 'blue'

        for landmine in self.initial_state.landmines:
            is_present = bool(landmine.is_present)
            if is_present:
                self.grid.set(landmine.x, landmine.y, Landmine(landmine.x, landmine.y, is_present))

            else:
                continue

        destination_position = self.initial_state.agent.dest_pos
        self.grid.set(destination_position[0], destination_position[1], Goal())
        self.grid.get(destination_position[0], destination_position[1]).color = 'green'


    def get_agent_rgb(self):
        # This method returns the RGB array of the whole grid and extracts the part where the agent is.
        full_rgb = self.render()  # mode='rgb_array'
        if full_rgb is None:
            print("Error: Full RGB array is None.")
            return None

        # Assuming a cell size of 32 pixels as default. Adjust if using a different cell size.
        cell_size = 32
        agent_x, agent_y = self.agent_pos
        # Extract the RGB array for the agent's cell. Adjust indices as needed.
        agent_rgb = full_rgb[agent_y * cell_size:(agent_y + 1) * cell_size,
                    agent_x * cell_size:(agent_x + 1) * cell_size]
        return agent_rgb

    # def update_final_state(self, instruction, env):
    #     current_position = (self.agent_pos[0], self.agent_pos[1])
    #     if current_position not in self.coverage:
    #         self.coverage[current_position] = []
    #     # Check if the action is not already recorded for the current position
    #     if instruction not in self.coverage[current_position]:
    #         self.coverage[current_position].append(instruction)
    #
    #     if instruction == env.actions.forward:
    #         new_pos = self.front_pos
    #         if self.grid.get(*new_pos) is None or self.grid.get(*new_pos).can_overlap() or isinstance(self.grid.get(*new_pos), Key):
    #             self.agent_pos = new_pos
    #             self.final_state.agent.dest_pos = new_pos
    #             self.final_state.agent.path.append(new_pos)
    #
    #
    #
    #     elif instruction == env.actions.left:
    #         if self.final_state.agent.dest_direction == 'e':
    #             self.final_state.agent.dest_direction = 'n'
    #         elif self.final_state.agent.dest_direction == 'n':
    #             self.final_state.agent.dest_direction = 'w'
    #         elif self.final_state.agent.dest_direction == 'w':
    #             self.final_state.agent.dest_direction = 's'
    #         else:
    #             self.final_state.agent.dest_direction = 'e'
    #
    #     elif instruction == env.actions.right:
    #         if self.final_state.agent.dest_direction == 'e':
    #             self.final_state.agent.dest_direction = 's'
    #         elif self.final_state.agent.dest_direction == 's':
    #             self.final_state.agent.dest_direction = 'w'
    #         elif self.final_state.agent.dest_direction == 'w':
    #             self.final_state.agent.dest_direction = 'n'
    #         else:
    #             self.final_state.agent.dest_direction = 'e'
    #
    #     elif instruction == env.actions.pickup:
    #         next_pos = get_next_pos(self.final_state.agent.dest_direction, env.agent_pos)
    #         for key in self.final_state.keys:
    #             if (key.x_init, key.y_init) == next_pos and bool(key.is_present):
    #                  key.is_picked = 1
    #                  return
    #         for object in self.final_state.objects:
    #             if(object.x , object.y) == next_pos and bool(object.is_present):
    #                 object.pick_status = 1
    #                 return
    #
    #
    #
    #     elif instruction == env.actions.toggle:
    #         next_pos = get_next_pos(self.final_state.agent.dest_direction, env.agent_pos)
    #         for door in self.final_state.doors:
    #             if (door.x, door.y) == next_pos:
    #                 for key in self.final_state.keys:
    #                     if door.color == key.color:
    #                         door.door_status = 1
    #
    #     elif instruction == env.actions.drop:
    #         # Find the position where the agent should drop the key
    #         next_pos = tuple(env.agent_pos)
    #         for key in self.final_state.keys:
    #             if key.is_picked == 1:
    #                 key.x_init, key.y_init = next_pos  # Change the key position to the drop position
    #                 break
    #
    #         for object in self.final_state.objects:
    #             if object.pick_status == 1 :
    #                 object.v, object.w = next_pos  # Change the key position to the drop position
    #                 break

    def update_final_state(self, instruction, env):
        current_position = tuple(self.agent_pos)
        #print(f"Current Position: {current_position}")

        if current_position not in self.coverage:
            self.coverage[current_position] = []

        if instruction not in self.coverage[current_position]:
            self.coverage[current_position].append(instruction)

        if instruction == env.actions.forward:
            new_pos = self.front_pos
           # print(f"Attempting to move to: {new_pos}")
            if self.grid.get(*new_pos) is None or self.grid.get(*new_pos).can_overlap():
                self.final_state.agent.dest_pos = (new_pos[0],new_pos[1])
                self.final_state.agent.path.append(new_pos)
                #print(f"Moved to: {new_pos}")

        elif instruction == env.actions.left:
            if self.final_state.agent.dest_direction == 'e':
                self.final_state.agent.dest_direction = 'n'
            elif self.final_state.agent.dest_direction == 'n':
                self.final_state.agent.dest_direction = 'w'
            elif self.final_state.agent.dest_direction == 'w':
                self.final_state.agent.dest_direction = 's'
            else:
                self.final_state.agent.dest_direction = 'e'
            #print(f"Turned left to direction: {self.final_state.agent.dest_direction}")

        elif instruction == env.actions.right:
            if self.final_state.agent.dest_direction == 'e':
                self.final_state.agent.dest_direction = 's'
            elif self.final_state.agent.dest_direction == 's':
                self.final_state.agent.dest_direction = 'w'
            elif self.final_state.agent.dest_direction == 'w':
                self.final_state.agent.dest_direction = 'n'
            else:
                self.final_state.agent.dest_direction = 'e'
            #print(f"Turned right to direction: {self.final_state.agent.dest_direction}")

        elif instruction == env.actions.pickup:
            next_pos = get_next_pos(self.final_state.agent.dest_direction, env.agent_pos)
            #print(f"Attempting to pick up at: {next_pos}")
            for key in self.final_state.keys:
                if (key.x_init, key.y_init) == next_pos and bool(key.is_present):
                    key.is_picked = 1
                    #print(f"Picked up key at: {next_pos}")
                    return
            for object in self.final_state.objects:
                if (object.x, object.y) == next_pos and bool(object.is_present):
                    object.pick_status = 1
                    #print(f"Picked up object at: {next_pos}")
                    return

        elif instruction == env.actions.toggle:
            next_pos = get_next_pos(self.final_state.agent.dest_direction, env.agent_pos)
            print(f"Attempting to toggle at: {next_pos}")
            for door in self.final_state.doors:
                if (door.x, door.y) == next_pos:
                    for key in self.final_state.keys:
                        if door.color == key.color:
                            door.door_status = 1
                            #print(f"Toggled door at: {next_pos}")

        elif instruction == env.actions.drop:
            next_pos = tuple(env.agent_pos)
            print(f"Attempting to drop at: {next_pos}")
            for key in self.final_state.keys:
                if key.is_picked == 1:
                    key.x_init, key.y_init = next_pos
                    print(f"Dropped key at: {next_pos}")
                    break

            for object in self.final_state.objects:
                if object.pick_status == 1:
                    object.v, object.w = next_pos
                    print(f"Dropped object at: {next_pos}")
                    break

    def step(self, action):
        # Get the current position and direction of the agent
        current_pos = tuple(self.agent_pos)
        current_dir = self.agent_dir

        # Perform the action and get the result
        obs, reward, done, info = super().step(action)[:4]

        # Determine the new position after the action
        new_pos = tuple(self.agent_pos)



        # Handle if the agent steps on lava
        if isinstance(self.grid.get(*new_pos), Lava):
            done = True

        # After performing an action, update the final state
        #self.update_final_state(action, self)
        return obs, reward, done, info

    def get_coverage(self):
        return self.coverage
    def get_agent_rgb(self):
        # This method returns the RGB array of the whole grid and extracts the part where the agent is.
        full_rgb = self.render()  # mode='rgb_array'
        # Assuming a cell size of 32 pixels as default. Adjust if using a different cell size.
        cell_size = 32
        agent_x, agent_y = self.agent_pos
        # Extract the RGB array for the agent's cell. Adjust indices as needed.
        agent_rgb = full_rgb[agent_y * cell_size:(agent_y + 1) * cell_size,
                    agent_x * cell_size:(agent_x + 1) * cell_size]
        return agent_rgb

    def setInitialState(self):
        return self.initial_state

    def returnFinalState(self):
        return self.final_state

    def log_state(self,log_file_path, instruction):
        # Get the current time and date
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"----------- Entry Time: {current_time}-----------\n")
            log_file.write(f"Initial State: \n")
            log_file.write(f"Agent Initial position: {self.initial_state.agent.init_pos}, \n")
            log_file.write(f"Agent Initial direction: {self.initial_state.agent.init_direction}\n")
            for door in self.initial_state.doors:
                doorStatus = 'Open'
                if door.door_status == 1:
                    doorStatus = 'Closed'

                lockStatus = 'Unlock'
                if door.door_locked == 1:
                    lockStatus = 'Lock'
                log_file.write(f"Door at ({door.x}, {door.y}) status: {doorStatus}  locked_Status: {lockStatus}  Door_Color: {door.color}\n")
            for key in self.initial_state.keys:
                log_file.write(
                    f"Key at ({key.x_init}, {key.y_init}) picked: {key.is_picked}, present: {key.is_present}, key_color: {key.color}\n")

            for lava_tile in self.initial_state.lava_tiles:
                log_file.write(
                    f"Lava at ({lava_tile.x}, {lava_tile.y})\n")

            for obj in self.initial_state.objects:
                pickStatus = 'Not Picked'
                if obj.pick_status == 1:
                    pickStatus = 'Picked'
                dropStatus = 'Not Dropped'
                if obj.drop_status == 1:
                    dropStatus = 'Dropped'
                log_file.write(
                    f"Object at ({obj.x}, {obj.y}) pick_status: {pickStatus}, drop_status: {dropStatus}, drop destination: ({obj.v}, {obj.w}), is_present: {obj.is_present}, color: {obj.color}\n")

            # Add logging for initial state of objects and lava tiles as needed

            log_file.write("\nFinal State: \n")
            log_file.write(f"Agent Final position: {self.final_state.agent.dest_pos}\n")
            log_file.write(f"Agent Final direction: {self.final_state.agent.dest_direction}\n")
            log_file.write(f"Agent path: {self.final_state.agent.path}\n\n")
            for door in self.final_state.doors:
                doorStatus = 'Close'
                if door.door_status == 1:
                    doorStatus = 'Open'

                lockStatus = 'Unlock'
                if door.door_locked == 1:
                    lockStatus = 'Lock'
                log_file.write(
                    f"Door at ({door.x}, {door.y}) status: {doorStatus}  locked_Status: {lockStatus}  Door_Color: {door.color}\n")
            for key in self.final_state.keys:
                log_file.write(
                    f"Key at ({key.x_init}, {key.y_init}) picked: {key.is_picked}, present: {key.is_present}, key_color: {key.color}\n")

            for lava_tile in self.initial_state.lava_tiles:
                log_file.write(
                    f"Lava at ({lava_tile.x}, {lava_tile.y})\n")

            for obj in self.final_state.objects:
                pickStatus = 'Not Picked'
                if obj.pick_status == 1:
                    pickStatus = 'Picked'
                dropStatus = 'Not Dropped'
                if obj.drop_status == 1:
                    dropStatus = 'Dropped'
                log_file.write(
                    f"Object at ({obj.x}, {obj.y}) pick_status: {pickStatus}, drop_status: {dropStatus}, drop destination: ({obj.v}, {obj.w}), is_present: {obj.is_present}, color: {obj.color}\n")

            log_file.write(f"\nInstruction Applied: {instruction}\n\n")


    def log_grid_state(self, log_file_path):
        # Get dimensions of the grid
        width, height = self.grid.width, self.grid.height

        # Prepare the grid representation as a list of lists
        grid_representation = [['0' for _ in range(width)] for _ in range(height)]

        # Mark lava locations
        for lava in self.initial_state.lava_tiles:
            if lava.is_present:
                grid_representation[lava.y][lava.x] = '1'

        # Mark the agent's initial position
        init_x, init_y = self.initial_state.agent.init_pos
        grid_representation[init_y][init_x] = 'I'

        # Mark the agent's destination position (if defined)
        if hasattr(self.final_state.agent, 'dest_pos'):
            dest_x, dest_y = self.final_state.agent.dest_pos
            grid_representation[dest_y][dest_x] = 'D'

        # Write the grid to a file
        with open(log_file_path, 'w') as file:
            for row in grid_representation:
                row_str = '|' + '|'.join(row) + '|'
                file.write(row_str + '\n')

def get_next_pos(agent_direction,agent_postion):
        # Define the method to convert agent direction to vector representation
        x = agent_postion[0]
        y = agent_postion[1]

        if agent_direction == 'e':
            next_agent_pos = (x+1,y)
            return next_agent_pos
             # Facing right
        elif agent_direction == 'w':
            next_agent_pos = (x - 1, y)
            return next_agent_pos
        elif agent_direction == 's':
            next_agent_pos = (x, y+1)
            return next_agent_pos
        elif agent_direction == 'n':
            next_agent_pos = (x, y-1)
            return next_agent_pos


def execute_instructions(env, instruction):
    action_map = {
        "forward": env.actions.forward,
        "right": env.actions.right,
        "left": env.actions.left,
        "pickup": env.actions.pickup,
        "drop": env.actions.drop,
        "toggle": env.actions.toggle,
        "done": env.actions.done,
    }
    direction_map = {
        0: "E",
        1: "S",
        2: "W",
        3: "N"
    }
    instruction_log = []
    for action in instruction:
        agent_pos = tuple(env.agent_pos)
        dir = direction_map[env.agent_dir]
        key_color = next((key.color for key in env.initial_state.keys if key.is_picked), None)
        landmines = sorted([(landmine.x, landmine.y, landmine.is_present) for landmine in env.initial_state.landmines])

        state_info = (agent_pos[0], agent_pos[1], dir, key_color, tuple(landmines))
        ins = action
        action = action_map.get(action)

        if action is not None:
            obs, reward, done, info = env.step(action)[:4]
            env.update_final_state(action, env)
            env.render()
            agent_rgb = env.get_agent_rgb()
            instruction_log.append((state_info, ins))
            if done:
                break  # Terminate if done is True
        else:
            print(f"Unrecognized instruction: {action}")

    return obs, reward, done, info, instruction_log


def key_status_changed(env):
    # Compare the initial state of the environment with the current state
    # and detect changes indicative of key pickup
    initial_key_present = initial_state_has_key(env)
    current_key_present = current_state_has_key(env)

    # If the key was present initially but is not present now, it has been picked up
    return initial_key_present and not current_key_present


def initial_state_has_key(env):
    # Check if the key was present in the initial state of the environment
    initial_state = env.setInitialState()
    return any(key.is_present for key in initial_state.keys)


def current_state_has_key(env):
    # Check if the key is present in the current state of the environment
    current_state = env.returnFinalState()
    return any(key.is_present for key in current_state.keys)

def logCapabilities(log_file_path,is_valid_instruction,averageCoverage):

    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Valid Capability : {is_valid_instruction} \n")
        log_file.write(f"Average Coverage : {averageCoverage}\n")


def GetFuzzInstruction(instructions,iteration):
    file_path = os.path.join('.', 'Config.xml')  # Adjust the path as necessary
    logFile_Setting = loadSetting(os.path.join('.', 'Settings.xml'))
    test_environment,gridSize = load_InitialState(file_path)
    env = CustomMiniGridEnv(state=test_environment,grid_size=gridSize, render_mode='rgb_array') #rgb_array
    #env.log_grid_state(logFile_Setting.environment_logs_path)
    initial_state = env.setInitialState()



    obs = env.reset()
    # Render the initial state of the environment for visualization
    env.render()

    instruction_log = execute_instructions(env,logFile_Setting.environment_logs_path, instructions)
    # print(instructions)
    # Keep the window open until a key is pressed
    final_state = env.returnFinalState()
    final_initial_environment,gridSize = load_InitialState(file_path)
    is_valid_instruction = check_environment_changes(final_initial_environment,final_state)
    is_valid_capabilities = False
    possible_actions = ["forward", "left", "right"]
    COVERAGE = env.get_coverage()
    #averageCoverage = calculate_coverage(env.get_coverage(),gridSize,possible_actions,final_initial_environment.agent.dest_pos)
    averageCoverage , di = calculate_coverage_and_return_actions(env.get_coverage(),gridSize,possible_actions,test_environment.lava_tiles,final_initial_environment.agent.dest_pos)
    averageCoverage2  = calculate_coverages(env.get_coverage(),gridSize,possible_actions,final_initial_environment.agent.dest_pos)
    if(is_valid_instruction):

                is_capable, sta,roomExplored = hypothesisCapabilities(final_initial_environment,final_state,instructions)
                is_valid_capabilities = is_capable
                logCapabilities(logFile_Setting.environment_logs_path,is_valid_instruction,roomExplored,sta,iteration,averageCoverage,)

    else:
        logCapabilities(logFile_Setting.environment_logs_path,False, False,'Na',iteration,averageCoverage)

        # Close the environment
    env.close()

    if is_valid_instruction and is_valid_capabilities:
            message = f"For {logFile_Setting.EnvName} both instructions and capabilities are valid for iteration {iteration}."
            send_slack_message(message)

    return is_valid_instruction , is_valid_capabilities , averageCoverage , di,instruction_log





def execute_and_evaluate_task(instruction, config_path,log_file_path):
    file_path = os.path.join('Config.xml')
    initial_environment, gridSize = load_InitialState(config_path)
    env = CustomMiniGridEnv(state=initial_environment, grid_size=gridSize, render_mode='rgb_array')  # rgb_array
    initial_state = env.setInitialState()

    obs = env.reset()
    env.render()

    obs, reward, done, info, instruction_log = execute_instructions(env, instruction)

    #instruction_log =     execute_instructions(env, log_file_path, instruction)

    final_state = env.returnFinalState()
    final_initial_environment, gridSize = load_InitialState(config_path)

    is_valid_instruction = check_environment_changes(final_initial_environment, final_state)
    is_valid_capabilities = False
    possible_actions = ["forward", "left", "right","pickup","toggle","drop","done"]
    COVERAGE = env.get_coverage()
    # averageCoverage = calculate_coverage(env.get_coverage(),gridSize,possible_actions,final_initial_environment.agent.dest_pos)
    averageCoverage, di = calculate_coverage_and_return_actions(env.get_coverage(), gridSize, possible_actions,
                                                                initial_environment.lava_tiles,
                                                                final_initial_environment.agent.dest_pos)
    averageCoverage2 = calculate_coverages(env.get_coverage(), gridSize, possible_actions,
                                           final_initial_environment.agent.dest_pos)
    if (is_valid_instruction):

        is_capable = check_task_achieved(final_initial_environment, final_state, log_file_path)
        is_valid_capabilities = is_capable
        logCapabilities(log_file_path, is_valid_capabilities,averageCoverage)

    else:
        logCapabilities(log_file_path, False, averageCoverage)

        # Close the environment
    env.close()

    return is_valid_instruction, is_valid_capabilities, averageCoverage, di,instruction_log



def calculate_coveragesw(coverage, grid_size, possible_actions, destination=None):
    # Define which cells to exclude (e.g., boundaries and the destination)
    excluded_cells = set()
    for x in range(grid_size):
        excluded_cells.add((x, 0))  # Top boundary
        excluded_cells.add((x,(grid_size-1)))  # Bottom boundary
    for y in range(grid_size):
        excluded_cells.add((0, y))  # Left boundary
        excluded_cells.add((grid_size - 1, y))  # Right boundary
    if destination:
        excluded_cells.add(destination)  # Add destination to excluded cells

    total_coverage = 0
    count_cells = 0

    # Iterate through each cell in the coverage map
    for position, actions in coverage.items():
        if position not in excluded_cells:
            # Calculate how many of the possible actions have been performed
            performed_actions = len(set(actions))
            cell_coverage = performed_actions / len(possible_actions) * 100  # Coverage in percentage
            total_coverage += cell_coverage
            count_cells += 1

    # Calculate average coverage, excluding the excluded cells
    average_coverage = total_coverage / count_cells if count_cells else 0
    return average_coverage



def calculate_coverages(coverage, grid_size, possible_actions, destination=None):
    # Define which cells to exclude (e.g., boundaries and the destination)
    excluded_cells = set()
    for x in range(grid_size):
        excluded_cells.add((x, 0))  # Top boundary
        excluded_cells.add((x, grid_size - 1))  # Bottom boundary
    for y in range(grid_size):
        excluded_cells.add((0, y))  # Left boundary
        excluded_cells.add((grid_size - 1, y))  # Right boundary
    if destination:
        excluded_cells.add(destination)  # Add destination to excluded cells

    valid_cells = {
        (x, y)
        for x in range(1, grid_size - 1)
        for y in range(1, grid_size - 1)
    } - excluded_cells

    total_coverage = 0

    # Iterate through each valid cell in the grid
    for cell in valid_cells:
        # Get the actions taken for this specific cell, or an empty list if not present
        actions = coverage.get(cell, [])
        performed_actions = len(set(actions))
        cell_coverage = performed_actions / len(possible_actions) * 100  # Coverage in percentage
        total_coverage += cell_coverage

    # Calculate the average coverage over all valid cells
    average_coverage = total_coverage / len(valid_cells) if valid_cells else 0


    return average_coverage



def calculate_coverage_and_return_actions(coverage, grid_size, possible_actions,lava_tiles, destination=None):
    """Calculate average coverage and return a dictionary of valid cells with their actions."""
    # Define which cells to exclude (e.g., boundaries and the destination)
    excluded_cells = set()
    for x in range(grid_size):
        excluded_cells.add((x, 0))  # Top boundary
        excluded_cells.add((x, grid_size - 1))  # Bottom boundary
    for y in range(grid_size):
        excluded_cells.add((0, y))  # Left boundary
        excluded_cells.add((grid_size - 1, y))  # Right boundary
    if destination:
        excluded_cells.add(destination)

    for lava in lava_tiles:
        if lava.is_present:
            excluded_cells.add((lava.x, lava.y))

    # Initialize a set of all valid (non-excluded) cells
    valid_cells = {
        (x, y)
        for x in range(1, grid_size - 1)
        for y in range(1, grid_size - 1)
    } - excluded_cells

    # Create a dictionary for valid cells with their associated actions or an empty list
    valid_cells_dict = {
        cell: coverage.get(cell, []) for cell in valid_cells
    }

    total_coverage = 0

    # Iterate through each valid cell in the grid
    for actions in valid_cells_dict.values():
        performed_actions = len(set(actions))
        cell_coverage = performed_actions / len(possible_actions) * 100  # Coverage in percentage
        total_coverage += cell_coverage

    # Calculate the average coverage over all valid cells
    average_coverage = total_coverage / len(valid_cells) if valid_cells else 0

    return average_coverage, valid_cells_dict



def GetFuzzEnvInstruction(test_environment, gridSize,instructions, iteration):

    file_path = os.path.join('.', 'Config.xml')  # Adjust the path as necessary
    logFile_Setting = loadSetting(os.path.join('.', 'Settings.xml'))
    test_environment2 = test_environment
    # gridSize = load_InitialState(file_path)
    env = CustomMiniGridEnv(state=test_environment2, grid_size=gridSize, render_mode='rgb_array')  # rgb_array
    # env.log_grid_state(logFile_Setting.environment_logs_path)
    initial_state = env.setInitialState()

    obs = env.reset()
    # Render the initial state of the environment for visualization
    env.render()

    execute_instructions(env, logFile_Setting.environment_logs_path, instructions)
    # print(instructions)
    # Keep the window open until a key is pressed
    final_state = env.returnFinalState()
    final_initial_environment, gridSize = load_InitialState(file_path)
    #final_initial_environment = test_environment
    is_valid_instruction = check_environment_changes(final_initial_environment, final_state)
    is_valid_capabilities = False


    if (is_valid_instruction):

        is_capable, sta, roomExplored = hypothesisCapabilities(final_initial_environment, final_state, instructions)
        is_valid_capabilities = is_capable
        logCapabilities(logFile_Setting.environment_logs_path, is_valid_instruction, roomExplored, sta, iteration)

    else:
        logCapabilities(logFile_Setting.environment_logs_path, False, False, 'Na', iteration)

        # Close the environment
    env.close()

    if is_valid_instruction and is_valid_capabilities:
        message = f"For {logFile_Setting.EnvName} both instructions and capabilities are valid for iteration {iteration}."
        send_slack_message(message)

    return is_valid_instruction, is_valid_capabilities


def send_slack_message(message):
    webhook_url = 'https://hooks.slack.com/services/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'
    data = {'text': message}
    response = requests.post(webhook_url, json=data)
    if response.status_code != 200:
        print(f"Failed to send Slack message. Status code: {response.status_code}")


def render_environment_human_mode():
    file_path = os.path.join('.', 'Config.xml')  # Adjust the path as necessary
    test_environment, gridSize = load_InitialState(file_path)
    env = CustomMiniGridEnv(state=test_environment, grid_size=gridSize, render_mode='human')

    # Reset the environment and render the initial state
    obs = env.reset()
    env.render()
    instruction = ['left','forward','forward','pickup','right','toggle','forward','forward']
    #execute_instructions(env, '', instruction)

    # Execute instructions in the environment
    #execute_instructions(env, instructions)
    input("Press any key to close the environment...")
    # Close the environment
    env.close()


def aumate_enviromet_human_mode(screenshot_path, config_path):
    # Adjust the path as necessary
    test_environment, gridSize = load_InitialState(config_path)
    env = CustomMiniGridEnv(state=test_environment, grid_size=gridSize, render_mode='rgb_array')  # Use 'rgb_array' for rendering

    # Reset the environment and render the initial state
    obs = env.reset()
    img = env.render()  # Render the environment to get the image

    # Ensure the directories exist
    if not os.path.exists(screenshot_path):
        os.makedirs(screenshot_path)

    # Save the image to a file
    surface = pygame.surfarray.make_surface(img.transpose((1, 0, 2)))
    screenshot_file = os.path.join(screenshot_path, 'screenshot.png')

    pygame.image.save(surface, screenshot_file)

    # Close the environment
    env.close()

#render_environment_human_mode()


def test():
    instruction = ['forward', 'forward', 'forward', 'forward', 'forward', 'forward']

    lo = r"A:\Github repos\Answer\AIProbe\Result\Four_room_Env\11\Env-29\Config.xml"
    is_valid_instruction, is_valid_capabilities, averageCoverage, di ,c  = execute_and_evaluate_task(instruction, "A:\Github repos\Answer\AIProbe\Minigrid\Config.xml", lo)
    print(is_valid_capabilities)


#test()


def  apply_instruction (instruction,mutated_env_path):



    initial_environment, gridSize = load_InitialState(mutated_env_path)

    initial_environment.agent.dest_pos= initial_environment.agent.init_pos
    env = CustomMiniGridEnv(state=initial_environment, grid_size=gridSize, render_mode='rgb_array')  # rgb_array
    initial_state = env.setInitialState()

    obs = env.reset()
    env.render()

    obs, reward, done, info, instruction_log =  execute_instructions(env, instruction)

    final_state = env.returnFinalState()
    return final_state,info,instruction_log

    # final_initial_environment, gridSize = load_InitialState(config_path)
    # is_valid_instruction = check_environment_changes(final_initial_environment, final_state)
    # is_valid_capabilities = False
    # possible_actions = ["forward", "left", "right","pickup","toggle","drop","done"]
    # COVERAGE = env.get_coverage()
    # # averageCoverage = calculate_coverage(env.get_coverage(),gridSize,possible_actions,final_initial_environment.agent.dest_pos)
    # averageCoverage, di = calculate_coverage_and_return_actions(env.get_coverage(), gridSize, possible_actions,
    #                                                             initial_environment.lava_tiles,
    #                                                             final_initial_environment.agent.dest_pos)
    # averageCoverage2 = calculate_coverages(env.get_coverage(), gridSize, possible_actions,
    #                                        final_initial_environment.agent.dest_pos)
    # if (is_valid_instruction):
    #
    #     is_capable = check_task_achieved(final_initial_environment, final_state, log_file_path)
    #     is_valid_capabilities = is_capable
    #     logCapabilities(log_file_path, is_valid_capabilities,averageCoverage)
    #
    # else:
    #     logCapabilities(log_file_path, False, averageCoverage)
    #
    #     # Close the environment
    # env.close()
    #
    # return is_valid_instruction, is_valid_capabilities, averageCoverage, di,instruction_log
