import random
import os
import json
from LoadConfig import loadSetting, load_InitialState
from environment import GetFuzzInstruction, send_slack_message, GetFuzzEnvInstruction
from environment import execute_instructions
from datetime import datetime, timedelta
from EnvironmentState import Agent, Door, Key, Object, Lava, State
import traceback
from InstructionData import *
import requests
# Action space
action_space = {
    0: ("left", "Turn left"),
    1: ("right", "Turn right"),
    2: ("forward", "Move forward"),
    #3: ("pickup", "pickup"),
    #4: ("toggle", "toggle")

    # 4: ("drop", "Unused"),
    # 5: ("toggle", "Unused")

}

def checkV(instruction):
    # Placeholder function for validation
    # Replace this with your actual validation logic
    return random.choice([True, False])

output_file = 'invalid_instructions.txt'




class InstructionMutator:
    def __init__(self, seed_instructions):
        self.seed_instructions = seed_instructions
        self.generated_instructions = []
        self.max_avg_coverage = 0
        self.best_instruction =[]


    def insert_random_action(self, instruction):
        action_num = random.choice(list(action_space.keys()))
        action_name = action_space[action_num][0]
        insert_index = random.randint(0, len(instruction))
        instruction.insert(insert_index, action_name)
        return instruction

    def swap_directions(self, instruction):
        direction_actions = ["left", "right"]
        direction_indices = [i for i, action in enumerate(instruction) if action in direction_actions]
        if len(direction_indices) >= 2:
            swap_indices = random.sample(direction_indices, 2)
            instruction[swap_indices[0]], instruction[swap_indices[1]] = instruction[swap_indices[1]], instruction[swap_indices[0]]
        return instruction

    def duplicate_direction(self, instruction):
        direction_actions = ["left", "right"]
        direction_indices = [i for i, action in enumerate(instruction) if action in direction_actions]
        if direction_indices:
            duplicate_index = random.choice(direction_indices)
            instruction.insert(duplicate_index, instruction[duplicate_index])
        return instruction

    def append_to_file(self, instruction):
        with open(output_file, 'a') as f:
            f.write(' '.join(instruction) + '\n')

    def is_instruction_in_file(self, instruction):
        # Check if the file exists before attempting to open it
        if not os.path.isfile(output_file):
            # Create the file if it doesn't exist
            with open(output_file, 'w') as f:
                pass  # Just create the file, no need to write anything yet

        with open(output_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                # Compare each line from the file to the 'joined' instruction
                if line.strip() == ' '.join(instruction):
                    return True  # Return True if a match is found
        return False
    def mutate(self):

        start_time = datetime.now()  # Capture the start time of the mutation process
        time_limit = timedelta(hours=1)  # Set a time limit of 3 hours

        logFile_Setting = loadSetting(os.path.join('.', 'Settings.xml'))
        json_storage = JsonArrayStorage(logFile_Setting.Instruction_logs_path)

        count = 0

        #test_environment, gridSize = self.mutate_lava_positions()
        try:
            while  count < 1000000 and datetime.now() - start_time < time_limit:  # Generate 15 instructions
                # Generate a random length for the instruction
                instruction_length = random.randint(3, 400)

                mutated_instruction = []

                for _ in range(instruction_length):
                    action_num = random.choice(list(action_space.keys()))
                    action_name = action_space[action_num][0]
                    mutated_instruction.append(action_name)

                mutated_instruction = optimize_instructions(mutated_instruction)

                if self.is_instruction_in_file(mutated_instruction):
                    continue
                # Mutation: Apply mutation functions randomly
                if random.random() < 0.5:
                    mutated_instruction = self.insert_random_action(mutated_instruction)
                if random.random() < 0.5:
                    mutated_instruction = self.swap_directions(mutated_instruction)
                if random.random() < 0.5:
                    mutated_instruction = self.duplicate_direction(mutated_instruction)


                #if  "done" in mutated_instruction[:-1]:
                    #continue



                is_valid_instruction, is_valid_capabilities, averageCoverage = GetFuzzInstruction(mutated_instruction,count)
                #is_valid_instruction, is_valid_capabilities = GetFuzzEnvInstruction(test_environment, gridSize,mutated_instruction,count)
                time_remaining = time_limit - (datetime.now() - start_time)
                if(averageCoverage > self.max_avg_coverage):
                    self.max_avg_coverage = averageCoverage
                self.log_mutate(logFile_Setting.mutator_logs_path,count, time_remaining, mutated_instruction, is_valid_instruction, is_valid_capabilities,averageCoverage,self.max_avg_coverage)
                if(is_valid_capabilities):
                    break

                if is_valid_instruction:
                    self.append_to_file(mutated_instruction)
                    json_storage.save_array(mutated_instruction)
                else:
                    self.append_to_file(mutated_instruction)
                print(count)
                count +=1


            message = f"For {logFile_Setting.EnvName} env the fuzzer has stop working."
            send_slack_message(message)

        except Exception as e:

            error_stack = traceback.format_exc()
            error_message = f"An error occurred during mutation: {str(e)}\nError stack:\n{error_stack}"
            print(error_message)
            send_slack_message(error_message)

    def coverage_guided_mutates(self):
        start_time = datetime.now()  # Start time of the mutation process
        time_limit = timedelta(hours=1)  # Set a time limit for mutation
        max_iterations = 1000000  # Set a maximum number of iterations

        # Load the settings and create JSON storage
        logFile_Setting = loadSetting(os.path.join('.', 'Settings.xml'))
        json_storage = JsonArrayStorage(logFile_Setting.Instruction_logs_path)

        count = 0
        seed_pool = []  # List to store high-coverage instructions
        self.max_avg_coverage = 0

        try:
            while count < max_iterations and datetime.now() - start_time < time_limit:
                # Choose the best seed or create a random one if the pool is empty
                if seed_pool:
                    base_instruction = random.choice(seed_pool)
                else:
                    instruction_length = random.randint(3, 400)
                    base_instruction = [
                        action_space[random.choice(list(action_space.keys()))][0]
                        for _ in range(instruction_length)
                    ]

                mutated_instruction = base_instruction[:]

                # Mutation: Apply mutation functions randomly
                if random.random() < 0.5:
                    mutated_instruction = self.insert_random_action(mutated_instruction)
                if random.random() < 0.5:
                    mutated_instruction = self.swap_directions(mutated_instruction)
                if random.random() < 0.5:
                    mutated_instruction = self.duplicate_direction(mutated_instruction)

                # Optimize the mutated instruction
                mutated_instruction = optimize_instructions(mutated_instruction)

                # Skip if the instruction already exists in the log file
                #if self.is_instruction_in_file(mutated_instruction):
                    #continue

                # Execute the instruction and gather coverage information
                is_valid_instruction, is_valid_capabilities, averageCoverage = GetFuzzInstruction(mutated_instruction,
                                                                                                  count)

                # Calculate remaining time for mutation
                time_remaining = time_limit - (datetime.now() - start_time)

                # Update the maximum average coverage and log the mutation details
                if averageCoverage > self.max_avg_coverage:
                    self.max_avg_coverage = averageCoverage
                    self.generated_instructions = mutated_instruction

                    # Clear the seed pool and add the new high-coverage instruction
                    seed_pool.clear()
                    seed_pool.append(mutated_instruction)

                self.log_mutate(
                    logFile_Setting.mutator_logs_path,
                    count,
                    time_remaining,
                    mutated_instruction,
                    is_valid_instruction,
                    is_valid_capabilities,
                    averageCoverage,
                    self.max_avg_coverage
                )

                # Stop mutation if valid capabilities are achieved
                if is_valid_capabilities:
                    break

                # Save useful instructions
                self.append_to_file(mutated_instruction)
                if is_valid_instruction:
                    json_storage.save_array(mutated_instruction)

                print(count)
                count += 1

            # Send Slack notification upon completion
            message = f"For {logFile_Setting.EnvName}, the fuzzer has stopped working."
            send_slack_message(message)

        except Exception as e:
            error_stack = traceback.format_exc()
            error_message = f"An error occurred during mutation: {str(e)}\nError stack:\n{error_stack}"
            print(error_message)
            send_slack_message(error_message)

    def coverage_guided_mutate(self):
        start_time = datetime.now()
        time_limit = timedelta(hours=1)
        max_iterations = 1000000

        # Load the settings and create JSON storage
        logFile_Setting = loadSetting(os.path.join('.', 'Settings.xml'))
        json_storage = JsonArrayStorage(logFile_Setting.Instruction_logs_path)

        count = 0
        seed_pool = []
        self.max_avg_coverage = 0

        try:
            while count < max_iterations and datetime.now() - start_time < time_limit:

                if seed_pool and random.random() < 0.6:
                    base_instruction = random.choice(seed_pool)
                else:
                    instruction_length = random.randint(3, 400)
                    base_instruction = [
                        action_space[random.choice(list(action_space.keys()))][0]
                        for _ in range(instruction_length)
                    ]

                mutated_instruction = base_instruction[:]

                # Mutation: Apply mutation functions randomly
                if random.random() < 0.5:
                    mutated_instruction = self.insert_random_action(mutated_instruction)
                if random.random() < 0.5:
                    mutated_instruction = self.swap_directions(mutated_instruction)
                if random.random() < 0.5:
                    mutated_instruction = self.duplicate_direction(mutated_instruction)

                # Optimize the mutated instruction
                mutated_instruction = optimize_instructions(mutated_instruction)

                # Skip if the instruction already exists in the log file
                #if self.is_instruction_in_file(mutated_instruction):
                    #continue

                # Execute the instruction and gather coverage information
                is_valid_instruction, is_valid_capabilities, averageCoverage = GetFuzzInstruction(mutated_instruction,
                                                                                                  count)

                # Calculate remaining time for mutation
                time_remaining = time_limit - (datetime.now() - start_time)

                # Update the maximum average coverage and log the mutation details
                if averageCoverage > self.max_avg_coverage:
                    self.max_avg_coverage = averageCoverage
                    self.generated_instructions = mutated_instruction
                    seed_pool.append(mutated_instruction)

                self.log_mutate(
                    logFile_Setting.mutator_logs_path,
                    count,
                    time_remaining,
                    mutated_instruction,
                    is_valid_instruction,
                    is_valid_capabilities,
                    averageCoverage,
                    self.max_avg_coverage
                )

                # Stop mutation if valid capabilities are achieved
                if is_valid_capabilities:
                    break

                # Save useful instructions
                self.append_to_file(mutated_instruction)
                if is_valid_instruction:
                    json_storage.save_array(mutated_instruction)

                print(count)
                count += 1

            # Send Slack notification upon completion
            message = f"For {logFile_Setting.EnvName}, the fuzzer has stopped working."
            send_slack_message(message)

        except Exception as e:
            error_stack = traceback.format_exc()
            error_message = f"An error occurred during mutation: {str(e)}\nError stack:\n{error_stack}"
            print(error_message)
            send_slack_message(error_message)

    def mutate_lava_positionse(self):
        file_path = os.path.join('.', 'Config.xml')
        test_environment, gridSize = load_InitialState(file_path)
        valid_positions = range(1, gridSize - 1)  # Valid positions excluding boundaries

        # Display initial state of lava tiles
        print("Initial Lava Tiles:")
        for lava_tile in test_environment.lava_tiles:
            print(f"  Lava Tile at ({lava_tile.x}, {lava_tile.y}) - Present: {lava_tile.is_present}")

        mutation_chance = 0.5  # Chance to mutate (add, move, or remove) each lava tile

        # Potentially mutate by adding, moving, or removing lava tiles
        if random.random() < mutation_chance:
            if random.random() < 0.3:  # 30% chance to add a new lava tile
                if len(test_environment.lava_tiles) < (gridSize - 2) ** 2:  # Check space to add more tiles
                    new_x, new_y = random.choice(valid_positions), random.choice(valid_positions)
                    if not any(tile.x == new_x and tile.y == new_y for tile in test_environment.lava_tiles):

                        test_environment.lava_tiles.append(Lava(new_x, new_y, 1))
                        print(f"Added new Lava Tile at ({new_x}, {new_y}) - Present: 1")

        # Attempt to move or remove tiles
        for lava_tile in list(test_environment.lava_tiles):
            action = random.choice(['move', 'remove'])  # Randomly choose to move or remove a tile
            if action == 'remove' and len(
                    test_environment.lava_tiles) > 1:  # Ensure not removing the last tile unless intended
                test_environment.lava_tiles.remove(lava_tile)
                print(f"Removed Lava Tile from ({lava_tile.x}, {lava_tile.y})")
            elif action == 'move':
                new_x, new_y = random.choice(valid_positions), random.choice(valid_positions)
                print(f"Moving Lava Tile from ({lava_tile.x}, {lava_tile.y}) to ({new_x}, {new_y})")
                lava_tile.x, new_y = new_x, new_y
                lava_tile.is_present = 1  # Optionally ensure the lava tile is marked as present after moving

        # Display final state of lava tiles
        print("Final Lava Tiles:")
        for lava_tile in test_environment.lava_tiles:
            print(f"  Lava Tile at ({lava_tile.x}, {lava_tile.y}) - Present: {lava_tile.is_present}")

        return test_environment, gridSize
    def mutate_lava_positions(self):
        file_path = os.path.join('.', 'Config.xml')
        test_environment, gridSize = load_InitialState(file_path)
        valid_positions = range(1, gridSize - 1)  # Valid positions excluding boundaries

        # Display initial state of lava tiles
        print("Initial Lava Tiles:")
        for lava_tile in test_environment.lava_tiles:
            print(f"  Lava Tile at ({lava_tile.x}, {lava_tile.y}) - Present: {lava_tile.is_present}")

        # Chance to mutate by moving existing lava tiles
        mutation_chance = 0.80  # 50% chance to attempt moving each lava tile

        for lava_tile in test_environment.lava_tiles:
            if random.random() < mutation_chance:  # Decide whether to mutate this tile
                new_x, new_y = random.choice(valid_positions), random.choice(valid_positions)
                # Prevent moving to the same position it already occupies
                if (new_x, new_y) != (lava_tile.x, lava_tile.y):
                    print(f"Moving Lava Tile from ({lava_tile.x}, {lava_tile.y}) to ({new_x}, {new_y})")
                    lava_tile.x, lava_tile.y = new_x, new_y  # Update the position
                    lava_tile.is_present = 1  # Ensure the lava tile is marked as present after moving

        # Display final state of lava tiles
        print("Final Lava Tiles:")
        for lava_tile in test_environment.lava_tiles:
            print(f"  Lava Tile at ({lava_tile.x}, {lava_tile.y}) - Present: {lava_tile.is_present}")

        return test_environment, gridSize

    def get_generated_instructions(self):
        return self.generated_instructions

    def log_mutate(self,log_file_path,iteratio_no,time_remaining,mutated_instruction,is_valid_instruction,is_valid_capabilities,averageCoverage,max_avg_coverage):
        # Get the current time and date
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"----------- Entry Time: {current_time}-----------\n")
            log_file.write(f"Iteration no : {iteratio_no}\n")
            log_file.write(f"Instruction: {mutated_instruction}\n\n")
            log_file.write(f"Is valid instruction : {is_valid_instruction}\n")
            log_file.write(f"Is valid Capabilities : {is_valid_capabilities}\n")
            log_file.write(f"Coverage percentage: {averageCoverage}\n")
            log_file.write(f"Cycle's max Average Coverage: {max_avg_coverage}\n")
            log_file.write(f"Time Remaining : {str(time_remaining)}\n\n")



def optimize_instructions(instructions):
    i = 0
    while i < len(instructions) - 1:
        if instructions[i] == 'left' and instructions[i + 1] == 'right':
            del instructions[i:i + 2]
        elif instructions[i] == 'right' and instructions[i + 1] == 'left':
            del instructions[i:i + 2]
        else:
            i += 1
    return instructions

def initialize_json_file(file_path):
    """ Initialize a JSON file with an empty list if it doesn't exist. """
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)

def append_to_json_file(file_path, data):
    """ Append a new item to the JSON file without loading the entire file into memory. """
    with open(file_path, 'r+') as f:
        f.seek(0, os.SEEK_END)
        f.seek(f.tell() - 1, os.SEEK_SET)  # Go to the last character in the file before EOF
        if f.tell() > 1:
            f.write(',\n')  # Write a comma to separate the previous last item
        else:
            f.write('\n')  # Just write a newline if file was empty
        json.dump(data, f)
        f.write('\n]')  # Close the list with a newline and a bracket

# Example usage
seed_instructions = [
    [action_space[0][0], action_space[2][0], action_space[1][0]],
    [action_space[2][0], action_space[2][0], action_space[0][0]],
    [action_space[1][0], action_space[2][0], action_space[2][0]]
]

mutator = InstructionMutator(seed_instructions)
#mutator.mutate()
mutator.coverage_guided_mutate()
#mutator.mutate_lava_positions()
generated_instructions = mutator.get_generated_instructions()

#ins = ['right', 'right', 'right', 'forward', 'left', 'forward', 'forward', 'left', 'forward', 'forward', 'forward', 'right', 'forward', 'right', 'right', 'right', 'forward', 'right']
#GetFuzzInstruction(ins,1)