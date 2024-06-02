import random
import os
import json
from datetime import datetime, timedelta
import traceback

import sys

import Minigrid.environment
from Fuzzer.Mutation.mutateEnv import EnvName
from Minigrid.environment import execute_and_evaluate_task

#Action space
action_space = {
    0: ("left", "Turn left"),
    1: ("right", "Turn right"),
    2: ("forward", "Move forward"),
    3: ("pickup", "pickup"),
    4: ("toggle", "toggle"),
    5: ("drop", "Done"),
    6: ("done", "Done")

}

navigate_Instruction = {

}

seed_instructions = [
    [action_space[2][0], action_space[1][0], action_space[2][0]],
    [action_space[2][0], action_space[2][0], action_space[1][0]],
    [action_space[1][0], action_space[2][0], action_space[2][0],action_space[0][0],action_space[4][0],action_space[6][0]]
]

class InstructionMutator:



    def __init__(self, seed_instructions):
        self.seed_instructions = seed_instructions
        self.generated_instructions = []
        self.max_avg_coverage = 0
        self.best_instruction =[]
        self.main_dict = {}



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





        is_valid_instruction, is_valid_capabilities, instruction_averag_Coverage, coverage_details = Minigrid.environment.execute_and_evaluate_task(mutated_instruction,env_config_path,instruction_log_path)

        if(is_valid_instruction):
            seed_pool.append(mutated_instruction)

        if is_valid_capabilities:

            return True

        return False


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


def fuzz_instruction(env_name,instruction_log_path,env_config_path):
    mutator = InstructionMutator(seed_instructions)

    if (env_name == EnvName.MINIGRID.value):
        env_name = EnvName.MINIGRID
    elif (env_name == EnvName.CATCHER.value):
        env_name = EnvName.CATCHER
    elif (env_name == EnvName.FLAPPY_BIRD):
        env_name = EnvName.FLAPPY_BIRD

    return mutator.random_fuzzing(env_config_path,instruction_log_path)











