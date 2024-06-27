import random
import os
import json
from datetime import datetime, timedelta
import traceback

import sys

import Minigrid.environment
from Fuzzer.Mutation.mutateEnv import EnvName
from Minigrid.environment import execute_and_evaluate_task
from Fuzzer.LoadConfig import load_InitialState

#Action space
action_space = {
    0: ("left", "Turn left"),
    1: ("right", "Turn right"),
    2: ("forward", "Move forward"),
    #3: ("pickup", "pickup"),

}

navigate_Instruction = {

}

seed_instructions = [
    [action_space[2][0], action_space[1][0], action_space[2][0]],
    [action_space[2][0], action_space[2][0], action_space[1][0]],
    [action_space[1][0], action_space[2][0], action_space[2][0],action_space[0][0],action_space[2][0],action_space[2][0]]
]

instruction_log_pool = [[]]

instruction_pool = []


class InstructionMutator:

    def __init__(self, seed_instructions):
        self.seed_instructions = seed_instructions
        self.generated_instructions = []
        self.max_avg_coverage = 0
        self.best_instruction =[]
        self.main_dict = {}
        self.max_instruction_length = 1



    def insert_random_action(self, instruction):
        action_num = random.choice(list(action_space.keys()))
        action_name = action_space[action_num][0]
        insert_index = random.randint(0, len(instruction))
        instruction.insert(insert_index, action_name)
        return instruction

    def insert_action(self, instruction, action_index):
        action_num = random.choice(list(action_space.keys()))
        action_name = action_space[action_num][0]
        instruction.insert(action_index, action_name)
        return instruction

    def remove_action(self, instruction,action_index):
        if(action_index < len(instruction)):

            instruction.pop(action_index)

        return instruction


    def replace_action(self, instruction,action_index):
        if(action_index < len(instruction)):
            action_num = random.choice(list(action_space.keys()))
            action_name = action_space[action_num][0]
            instruction[action_index] = action_name
        return instruction

    def remove_random_action(self, instruction):
        if not instruction:
            return instruction
        remove_index = random.randint(0, len(instruction) - 1)
        removed_action = instruction.pop(remove_index)

        return instruction
    def swap_directions(self, instruction):
        direction_actions = ["left", "right"]
        direction_indices = [i for i, action in enumerate(instruction) if action in direction_actions]
        if len(direction_indices) >= 2:
            swap_indices = random.sample(direction_indices, 2)
            instruction[swap_indices[0]], instruction[swap_indices[1]] = instruction[swap_indices[1]], instruction[swap_indices[0]]
        return instruction

    def update_random_action(self, instruction):
        if not instruction:
            return instruction
        update_index = random.randint(0, len(instruction) - 1)
        action_num = random.choice(list(action_space.keys()))
        action_name = action_space[action_num][0]

        instruction[update_index] = action_name

        return instruction

    def duplicate_direction(self, instruction):
        direction_actions = ["left", "right"]
        direction_indices = [i for i, action in enumerate(instruction) if action in direction_actions]
        if direction_indices:
            duplicate_index = random.choice(direction_indices)
            instruction.insert(duplicate_index, instruction[duplicate_index])
        return instruction


    def append_to_file(self, instruction):
        """Append the instruction to a file, ensuring all items are strings."""
        with open('instructions.txt', 'a') as f:
            try:
                # Ensure each item is a string before joining
                instruction_strings = [str(item) if not isinstance(item, tuple) else str(item[0]) for item in
                                       instruction]
                f.write(' '.join(instruction_strings) + '\n')
            except Exception as e:
                print(f"Error writing to file: {str(e)}")


    # purpose of this method is to implement random(without coverage guidance)
    def random_fuzzing(self,env_config_path,instruction_log_path):
        #random.seed(seed_value)
        seed_pool = seed_instructions
        instruction = random.choice(seed_pool)
        instruction_copy = instruction[:]
        if(len(instruction_copy) ==0):
            return

        ins_len = len(instruction_copy)
        if(ins_len >1 ):
            no_action_to_mutate = random.randint(1,ins_len-1)

            index_list = range(0,(ins_len-1))
        else:
            no_action_to_mutate = 1
            index_list = [0]

        actions_to_mutate = random.sample(index_list,no_action_to_mutate)
        mutated_instruction = instruction_copy
        curr_index = 0
        for action_index in sorted(actions_to_mutate):
          curr_index = action_index
          #k = random.randint(1,3)
          k = random.random()
          #if k == 1:
          if k < 0.50:

              if curr_index == 0 :
                mutated_instruction = self.insert_action(mutated_instruction, action_index)
                curr_index = action_index + 1
              else:
                  mutated_instruction = self.insert_action(mutated_instruction, curr_index)
                  curr_index = curr_index + 1

          elif  k < 0.90 :
              if curr_index  == 0 :
                mutated_instruction = self.replace_action(mutated_instruction, action_index)
                curr_index = action_index + 1
              else:
                  mutated_instruction = self.replace_action(mutated_instruction,curr_index)
                  curr_index = curr_index + 1

          elif len(mutated_instruction) > 0:

              if curr_index == 0:
                mutated_instruction = self.remove_action(mutated_instruction, action_index)
                if(action_index > 0 ):
                    curr_index = action_index  -1
                else:
                    curr_index = action_index
              else:
                  mutated_instruction = self.remove_action(mutated_instruction, curr_index)
                  if (curr_index > 0):
                    curr_index = curr_index - 1


        is_valid_instruction, is_valid_capabilities, instruction_averag_Coverage, coverage_details,instruction_log = Minigrid.environment.execute_and_evaluate_task(mutated_instruction,env_config_path,instruction_log_path)



        if(is_valid_instruction):
            seed_pool.append(mutated_instruction)

        if is_valid_capabilities:

            return True, instruction_log , mutated_instruction

        return False,instruction_log , mutated_instruction


    def get_generated_instructions(self):
        return self.generated_instructions


    def identify_missing_actions(self, coverage):
        """Identify actions that are missing from the current coverage."""
        all_possible_actions = set(action_space.keys())
        missing_actions = {}

        for position, actions in coverage.items():
            current_actions = set(actions)
            missing_for_position = all_possible_actions - current_actions
            if missing_for_position:
                missing_actions[position] = missing_for_position

        return missing_actions

    def coverage_guided_fuzzer(self, bfs_data, remaining_coverage_matrix,instruction_log, env_config_path, instruction_log_path,remove_pervoius_data):

        if not instruction_log:
            generated_instruction =  self.generate_random_instruction(bfs_data,env_config_path)

            mutated_instruction = []
            for instruction in generated_instruction:
                action = instruction[0]
                mutated_instruction.append(action)

            is_valid_instruction, is_valid_capabilities, instruction_average_coverage, coverage_details, instruction_log = execute_and_evaluate_task(
                mutated_instruction, env_config_path, instruction_log_path)

            coverage = self.calculate_coverage(bfs_data, instruction_log)

            if(remove_pervoius_data):
                instruction_log_pool.clear()
                instruction_pool.clear()

            if len(mutated_instruction) >= 1:
                instruction_log_pool.append(instruction_log)
                instruction_pool.append(mutated_instruction)

            self.update_remaining_coverage(instruction_log, remaining_coverage_matrix)
            return is_valid_capabilities, instruction_log, remaining_coverage_matrix

            #is_achieved, instruction_log, mutated_instruction = self.random_fuzzing(env_config_path,instruction_log_path)

        else:
            generated_instruction = random.choice(instruction_log_pool)
            while not generated_instruction:
                generated_instruction = random.choice(instruction_log_pool)


        mutated_instruction = []
        for instruction in generated_instruction:
             action = instruction[0]
             mutated_instruction.append(action)



        action_index =  len(mutated_instruction) - 1

        current_pos = generated_instruction[action_index][2] if action_index < len(generated_instruction) else None
        current_direction = generated_instruction[action_index][1] if action_index < len(generated_instruction) else None

        k = random.random()
        if k < 0.50:
                new_mutated_instruction = self.insert_valid_action(mutated_instruction,len(mutated_instruction) - 1 , bfs_data, current_pos,
                                                               current_direction,remaining_coverage_matrix)
        elif k < 1:
                new_mutated_instruction = self.replace_valid_action(mutated_instruction,action_index , bfs_data,
                                                                current_pos, current_direction,remaining_coverage_matrix)

        if(new_mutated_instruction in instruction_pool):
            return False, instruction_log, remaining_coverage_matrix





        is_valid_instruction, is_valid_capabilities, instruction_average_coverage, coverage_details, instruction_log = execute_and_evaluate_task(
            new_mutated_instruction, env_config_path, instruction_log_path)

        coverage = self.calculate_coverage(bfs_data, instruction_log)

        if(len(coverage)>0):
            invalid_actions = self.find_invalid_actions(instruction_log, bfs_data)
            if invalid_actions:
                return False, instruction_log, remaining_coverage_matrix

            instruction_log_pool.append(instruction_log)
            instruction_pool.append(new_mutated_instruction)

            self.update_remaining_coverage(instruction_log,remaining_coverage_matrix)



        if len(remaining_coverage_matrix) <=0:
            print("done")




        if is_valid_capabilities:
            return True, instruction_log,remaining_coverage_matrix

        return False, instruction_log, remaining_coverage_matrix





        #
        # instruction_copy = instruction[:]
        #
        # mutated_instruction = instruction_copy[:]
        #
        # if len(instruction_copy) == 0:
        #     return
        #
        # # Identify invalid actions from the previous execution
        # if len(instruction_log) > 1:
        #     invalid_actions = self.find_invalid_actions(instruction_log, bfs_data)
        # else:
        #     is_achieved, instruction_log, mutated_instruction = self.random_fuzzing(env_config_path,
        #                                                                             instruction_log_path)
        #     if len(mutated_instruction) >= 1:
        #         Env_seed_instruction.append(instruction_log)
        #     return is_achieved, instruction_log,remaining_coverage_matrix
        #
        # old_instruction = []
        # for instruction in instruction_copy:
        #     action = instruction[0]
        #     old_instruction.append(action)
        #
        # if(old_instruction[0] == 'pickup'):
        #     print('c')
        #
        # if invalid_actions:
        #     action_index = invalid_actions[0]  # Only mutate the first invalid action
        #
        #     # Ensure current_pos and current_direction are correctly taken from instruction_log
        #     current_pos = instruction_log[action_index][2] if action_index < len(instruction_log) else None
        #     current_direction = instruction_log[action_index][1] if action_index < len(instruction_log) else None
        #
        #     k = random.random()
        #     if k < 0.50:
        #         new_mutated_instruction = self.insert_valid_action(old_instruction, action_index, bfs_data, current_pos,
        #                                                        current_direction,remaining_coverage_matrix)
        #     elif k < 0.90:
        #         new_mutated_instruction = self.replace_valid_action(old_instruction, action_index, bfs_data,
        #                                                         current_pos, current_direction,remaining_coverage_matrix)
        #     else:
        #         new_mutated_instruction = self.remove_action(old_instruction, action_index)
        # else:
        #
        #     print("Done")
        #     return
        #
        #     action_index = random.randint(0, len(instruction_copy) - 1)
        #
        #     # Ensure current_pos and current_direction are correctly taken from instruction_log
        #     current_pos = instruction_log[action_index][2] if action_index < len(instruction_log) else None
        #     current_direction = instruction_log[action_index][1] if action_index < len(instruction_log) else None
        #
        #     k = random.random()
        #     if k < 0.50:
        #         new_mutated_instruction = self.insert_valid_action(old_instruction, action_index, bfs_data, current_pos,
        #                                                        current_direction,remaining_coverage_matrix)
        #     elif k < 0.90:
        #         new_mutated_instruction = self.replace_valid_action(old_instruction, action_index, bfs_data,
        #                                                         current_pos, current_direction,remaining_coverage_matrix)
        #     else:
        #         new_mutated_instru1ction = self.remove_action(old_instruction, action_index)
        #
        #
        # if new_mutated_instruction in seed_instructions :
        #     return False, instruction_log, remaining_coverage_matrix
        #
        # if(new_mutated_instruction == ['forward', 'right', 'forward', 'forward', 'left', 'pickup', 'left', 'pickup', 'forward']):
        #     print("bb")
        #
        # if(new_mutated_instruction[0] == 'left' or new_mutated_instruction [0] == 'pickup'):
        #     print('sd')
        #
        # is_valid_instruction, is_valid_capabilities, instruction_average_coverage, coverage_details, instruction_log = execute_and_evaluate_task(
        #     new_mutated_instruction, env_config_path, instruction_log_path)
        #
        # if len(mutated_instruction) >= 1:
        #
        #     Env_seed_instruction.append(instruction_log)
        #     seed_instructions.append(mutated_instruction)
        #
        # self.update_remaining_coverage(instruction_log,remaining_coverage_matrix)
        # if is_valid_capabilities:
        #     return True, instruction_log,remaining_coverage_matrix
        #
        # return False, instruction_log, remaining_coverage_matrix



    def generate_random_instruction(self, bfs_data,env_config_path):
        initialEnvironment,GridSize = load_InitialState(env_config_path)
        instruction = []
        positions = list(bfs_data.keys())
        if not positions:
            return instruction

        current_pos = initialEnvironment.agent.init_pos
        current_direction = initialEnvironment.agent.init_direction.upper()
        length = 1

        for _ in range(length):
            valid_actions = bfs_data.get(current_pos, {}).get(current_direction, {})
            if not valid_actions:
                break

            action = random.choice(list(valid_actions.keys()))
            instruction.append([action, current_direction, current_pos])

            next_pos = valid_actions[action]
            current_pos = next_pos if isinstance(next_pos, tuple) else current_pos  # Handle cases like "pickup"
            current_direction = self.update_direction(current_direction, action)

        return instruction


    def update_direction(self, current_direction, action):
        direction_order = "NESW"
        if action == "left":
            new_direction = direction_order[(direction_order.index(current_direction) - 1) % 4]
        elif action == "right":
            new_direction = direction_order[(direction_order.index(current_direction) + 1) % 4]
        else:
            new_direction = current_direction
        return new_direction
    def update_remaining_coverage(self, instruction_log, remaining_coverage_matrix):
        for action, direction, pos in instruction_log:
            if pos in remaining_coverage_matrix and direction in remaining_coverage_matrix[pos]:
                if action in remaining_coverage_matrix[pos][direction]:
                    del remaining_coverage_matrix[pos][direction][action]
                if not remaining_coverage_matrix[pos][direction]:
                    del remaining_coverage_matrix[pos][direction]
                if not remaining_coverage_matrix[pos]:
                    del remaining_coverage_matrix[pos]

    def find_invalid_actions(self, instruction, bfs_data):
        invalid_actions = []
        for index, (action, direction, pos) in enumerate(instruction):
            if pos not in bfs_data or direction not in bfs_data[pos] or action not in bfs_data[pos][direction]:
                invalid_actions.append(index)
        return invalid_actions

    def replace_valid_action(self, instruction, action_index, bfs_data, current_pos, current_direction,remaining_coverage_matrix):
        if len(remaining_coverage_matrix) <=0 :
            return instruction
        valid_actions = remaining_coverage_matrix.get(current_pos, {}).get(current_direction, {})

        if valid_actions:
            # Choose the action that maximizes coverage
            action_name = self.select_action_maximizing_coverage(valid_actions)
            instruction[action_index] = action_name
        else:
            # Fall back to random selection from bfs_data
            valid_actions = bfs_data.get(current_pos, {}).get(current_direction, {})
            if valid_actions:
                action_name = random.choice(list(valid_actions.keys()))
                if(len(valid_actions) == 1 and action_name == instruction[action_index]):
                    return self.insert_valid_action(instruction, action_index, bfs_data, current_pos, current_direction,remaining_coverage_matrix)
                instruction[action_index] = action_name



        return instruction

    def select_action_maximizing_coverage(self, valid_actions):
        return next(iter(valid_actions))
    def insert_valid_action(self, instruction, action_index, bfs_data, current_pos, current_direction,remaining_coverage_matrix):
        if len(remaining_coverage_matrix) <=0 :
            return instruction

        if instruction[action_index] == 'right':
            if (current_direction == 'E'):
                current_direction = 'S'
            elif current_direction == 'S':
                current_direction = 'W'
            elif current_direction == 'W':
                current_direction = 'N'
            else:
                current_direction = 'E'

        if(instruction[action_index] == 'left'):
            if (current_direction == 'E'):
                current_direction = 'N'
            elif current_direction == 'N':
                current_direction = 'W'
            elif current_direction == 'W':
                current_direction = 'S'
            else:
                current_direction = 'E'


        previous_postion = current_pos

        if instruction[action_index] == 'forward':
            if current_direction == 'E':
                current_pos = (current_pos[0], current_pos[1] + 1)
            elif current_direction == 'N':
                current_pos = (current_pos[0] - 1, current_pos[1])
            elif current_direction == 'W':
                current_pos = (current_pos[0], current_pos[1] - 1)
            elif current_direction == 'S':
                current_pos = (current_pos[0], current_pos[1]+1)


        valid_actions = remaining_coverage_matrix.get(current_pos, {}).get(current_direction, {})


        if valid_actions:
            # Choose the action that maximizes coverage
            action_name = self.select_action_maximizing_coverage(valid_actions)

            instruction.insert(action_index+1, action_name)
        else:
            # Fall back to random selection from bfs_data
            valid_actions = bfs_data.get(previous_postion, {}).get(current_direction, {})
            if valid_actions:
                action_name = random.choice(list(valid_actions.keys()))
                instruction.insert(action_index+1, action_name)
            else:
                valid_actions = bfs_data.get(previous_postion, {}).get(current_direction, {})
                if valid_actions:
                    action_name = random.choice(list(valid_actions.keys()))
                    instruction.insert(action_index + 1, action_name)
                else:
                    return  instruction


        return instruction




        valid_actions = bfs_data.get(current_pos, {}).get(current_direction, {})
        if valid_actions:
            action_name = random.choice(list(valid_actions.keys()))
            instruction.insert(action_index, action_name)
        return instruction

    def calculate_coverage(self,bfs_data, instruction_log):
        covered = set()
        for action, direction, pos in instruction_log:
            if pos in bfs_data and direction in bfs_data[pos] and action in bfs_data[pos][direction]:
                covered.add((pos, direction, action))
        return covered

    def generate_new_instructions(bfs_data, covered):
        uncovered = []
        for pos, directions in bfs_data.items():
            for direction, actions in directions.items():
                for action, next_pos in actions.items():
                    if (pos, direction, action) not in covered:
                        uncovered.append((pos, direction, action))

        if not uncovered:
            print("All actions are covered.")
            return []

        # Generate new instructions from uncovered actions
        new_instructions = []
        for pos, direction, action in uncovered:
            new_instructions.append((action, direction, pos))

        return new_instructions


def fuzz_instruction(env_name,coverage_matrix,remaining_coverage_matrix,instruction_log,instruction_log_path,env_config_path,remove_pervoius_data):
    mutator = InstructionMutator(seed_instructions)

    if (env_name == EnvName.MINIGRID.value):
        env_name = EnvName.MINIGRID
    elif (env_name == EnvName.CATCHER.value):
        env_name = EnvName.CATCHER
    elif (env_name == EnvName.FLAPPY_BIRD):
        env_name = EnvName.FLAPPY_BIRD

    #return mutator.random_fuzzing(env_config_path,instruction_log_path)
    return mutator.coverage_guided_fuzzer(coverage_matrix,remaining_coverage_matrix,instruction_log,env_config_path,instruction_log_path,remove_pervoius_data)











