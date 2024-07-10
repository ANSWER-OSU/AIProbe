import copy
import os
import random
import time
import sys
import logging

# Add the project root to the PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
print(f"Project root: {project_root}")
print(f"PYTHONPATH: {sys.path}")

import LoadConfig


from Fuzzer.Mutation.mutateEnv import mutate_environment,use_exsisting_enviroment, EnvName
from Minigrid.environment import aumate_enviromet_human_mode
from Fuzzer.Mutation.mutateTask import GenrateTask,PickupTask,UpdateTask
from Fuzzer.Mutation.mutateInstruction import fuzz_instruction , fuzzInstructions
from Fuzzer.CoverageMatrix import compute_valid_actions,compute_unsafe_states


def Main():
    # Loading the setting
    fuzzer = LoadConfig.load_fuzzer_setting('FuzzConfig.xml')

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    overall_start_time = time.time()  # Start time for the overall mutation process

    # Running for all seed values
    for seed in fuzzer.seeds:
        # Mutate the Env
        random.seed(seed)


        xml_file_path = os.path.join(parent_dir,"Minigrid","Config.xml")
        env_count = 1  # Initialize env_count

        print(f"Running for seed {seed}")

        seed_start_time = time.time()  # Start time for the current seed

        while time.time() - seed_start_time < fuzzer.mutate_env_time:  # 3600 seconds = 1 hour per seed
            env_start_time = time.time()  # Start time for the current environment mutation

            print(f"Running for env {env_count}")




            screenshot_path = os.path.join(parent_dir, "Result", "LavaExp", str(seed), f"Env-{env_count}")
            result_folder = updateFilePath(screenshot_path)

            # Saving the Env config
            print(f"Config files: {os.path.join(result_folder)}")
            mutated_env_path = os.path.join(result_folder, 'Config.xml')
            updateFilePath(mutated_env_path)
            # Mutate the environment
            if fuzzer.mutate_env:
                mutated_xml_content = mutate_environment(xml_file_path, EnvName.Four_Room)

                with open(mutated_env_path, "w", encoding="utf-8") as f:
                    f.write(mutated_xml_content)

                aumate_enviromet_human_mode(result_folder, xml_file_path)

            else:
                if not os.path.exists(mutated_env_path):
                    env_count+=1
                    continue
                use_exsisting_enviroment(xml_file_path,mutated_env_path)

            action_map = compute_valid_actions(xml_file_path)



            task_count = 1  # Initialize task_count
            while time.time() - env_start_time < fuzzer.task_mutate_time and time.time() - seed_start_time < fuzzer.mutate_env_time:  # 900 seconds = 15 minutes per environment
                task_start_time = time.time()

                mutated_task_path = os.path.join(result_folder, f"task_{task_count}")
                if(fuzzer.mutate_task):
                    GenrateTask(mutated_env_path, mutated_task_path)
                else:
                    PickupTask(mutated_env_path,mutated_task_path)



                for genrate_interuction_seed in fuzzer.seeds:
                    remove_pervoius_data = True
                    random.seed(genrate_interuction_seed)
                    remaining_coverage_matrix = copy.deepcopy(action_map)

                    instruction_start_time = time.time()
                    instruction_data = []
                    count =1

                    instruction_log_path = os.path.join(mutated_task_path, f"{genrate_interuction_seed}-log.txt")
                    while time.time() - instruction_start_time < fuzzer.instruction_generation_time :  # 180 seconds = 3 minutes per instruction

                        is_achived, current_instruction_data, current_remaining_coverage_matrix = fuzz_instruction(fuzzer.EnvName,action_map ,remaining_coverage_matrix,instruction_data,instruction_log_path, xml_file_path,remove_pervoius_data)

                        remove_pervoius_data = False

                        if(len(current_instruction_data)>=1):



                            instruction_data = current_instruction_data


                            remaining_coverage_matrix = current_remaining_coverage_matrix
                        count+=1
                        if  is_achived:
                            print(f"Instruction found for seed {seed} instruction seed {genrate_interuction_seed} env {env_count} task {task_count}")
                            #break  # Exit the instruction loop

                if time.time() - task_start_time >= fuzzer.task_mutate_time:  # 600 seconds = 10 minutes per task
                            break  # Exit the task loop

                task_count += 1
                break;

            env_count += 1

            # Exit the environment loop if the time limit is reached
            if time.time() - seed_start_time >= fuzzer.mutate_env_time:
                break

        print(f"Finished processing seed {seed}")

def updateFilePath(log_file):
    # Check if the log file path exists, if not, create it
    log_file_dir = os.path.dirname(log_file)
    if not os.path.exists(log_file_dir):
        os.makedirs(log_file_dir)
        print(f"Created directory for log file: {log_file_dir}")
    return os.path.abspath(log_file)



# def main():
#
#     # Loading the setting
#     fuzzer = LoadConfig.load_fuzzer_setting('FuzzConfig.xml')
#
#     parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     overall_start_time = time.time()  # Start time for the overall mutation process
#
#     # Running for all seed values
#     for seed in fuzzer.seeds:
#         # Mutate the Env
#         random.seed(seed)
#
#         xml_file_path = os.path.join(parent_dir,fuzzer.env_path)
#         env_count = 1
#
#         screenshot_path = os.path.join(parent_dir, fuzzer.log_file_path, str(seed))
#         x = screenshot_path
#         environments = [d for d in os.listdir(screenshot_path) if
#                         os.path.isdir(os.path.join(screenshot_path, d)) and d.startswith("Env-")]
#
#
#         for environment in environments:
#
#             screenshot_path = os.path.join(x,environment)
#
#             result_folder = updateFilePath(screenshot_path)
#
#                 # Saving the Env config
#             mutated_env_path = os.path.join(result_folder, 'Config.xml')
#             updateFilePath(mutated_env_path)
#
#             # Mutate the environment
#             if fuzzer.mutate_env:
#                 mutated_xml_content = mutate_environment(xml_file_path, EnvName.Four_Room)
#
#                 with open(mutated_env_path, "w", encoding="utf-8") as f:
#                     f.write(mutated_xml_content)
#
#                     aumate_enviromet_human_mode(result_folder, xml_file_path)
#
#             else:
#                 if not os.path.exists(mutated_env_path):
#                     continue
#                 use_exsisting_enviroment(xml_file_path, mutated_env_path)
#                 aumate_enviromet_human_mode(result_folder, xml_file_path)
#
#
#             action_map = compute_valid_actions(xml_file_path)
#
#             unsafe_states = compute_unsafe_states(xml_file_path)
#
#
#             task_count = 1  # Initialize task_count
#             # 900 seconds = 15 minutes per environment
#             task_start_time = time.time()
#
#             initial_state = LoadConfig.load_InitialState(mutated_env_path)
#
#             mutated_task_path = os.path.join(result_folder, f"task_{task_count}")
#             if (fuzzer.mutate_task):
#                         GenrateTask(mutated_env_path, mutated_task_path)
#             else:
#                         #PickupTask(mutated_env_path, mutated_task_path)
#                         modified_state = UpdateTask(initial_state)
#
#
#
#             for seed in fuzzer.seeds:
#
#                 random.seed(seed)
#                 remaining_coverage_matrix = copy.deepcopy(action_map)
#
#                 instruction_start_time = time.time()
#                 count = 1
#
#                 instruction_log_path = os.path.join(mutated_task_path,f"{seed}")  # 180 seconds = 3 minutes per instruction
#
#                     # is_achived, current_instruction_data, current_remaining_coverage_matrix = fuzz_instruction(
#                     #     fuzzer.EnvName, action_map, remaining_coverage_matrix, instruction_data, instruction_log_path,
#                     #     xml_file_path, remove_pervoius_data)
#
#                 fuzzInstructions(initial_state[0],modified_state[0],fuzzer.instruction_generation_time,action_map,unsafe_states,instruction_log_path,mutated_env_path)

def setup_logging(log_file='log.txt'):
    """Set up logging configuration."""
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def log_message(message, level='info'):
    """Log a message with a specified level."""
    if level == 'info':
        logging.info(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)
    else:
        logging.debug(message)

def main():

    # Loading the setting
    fuzzer = LoadConfig.load_fuzzer_setting('FuzzConfig.xml')
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Setup logging
    setup_logging(os.path.join(parent_dir,fuzzer.log_file_path,'log.txt'))
    log_message("Loaded fuzzer settings from 'FuzzConfig.xml'.")


    overall_start_time = time.time()  # Start time for the overall mutation process
    log_message(f"Overall mutation process started at {time.ctime(overall_start_time)}")

    # Running for all seed values
    for seed in fuzzer.seeds:
        log_message(f"Processing seed: {seed}")
        random.seed(seed)

        xml_file_path = os.path.join(parent_dir, fuzzer.env_path)
        env_count = 1

        screenshot_path = os.path.join(parent_dir, fuzzer.log_file_path, str(seed))
        x = screenshot_path
        environments = [d for d in os.listdir(screenshot_path) if
                        os.path.isdir(os.path.join(screenshot_path, d)) and d.startswith("Env-")]

        for environment in environments:


            env_start_time = time.time()
            log_message(f"Processing environment: {environment} started at {time.ctime(env_start_time)}")

            screenshot_path = os.path.join(x, environment)
            result_folder = updateFilePath(screenshot_path)
            log_message(f"Result folder path: {result_folder}")

            # Saving the Env config
            mutated_env_path = os.path.join(result_folder, 'Config.xml')
            updateFilePath(mutated_env_path)

            # Mutate the environment
            if fuzzer.mutate_env:
                mutated_xml_content = mutate_environment(xml_file_path, EnvName.Four_Room)
                with open(mutated_env_path, "w", encoding="utf-8") as f:
                    f.write(mutated_xml_content)
                log_message(f"Mutated environment saved at: {mutated_env_path}")

                aumate_enviromet_human_mode(result_folder, xml_file_path)
            else:
                if not os.path.exists(mutated_env_path):
                    log_message(f"Mutated environment path does not exist: {mutated_env_path}", level='warning')
                    continue
                use_exsisting_enviroment(xml_file_path, mutated_env_path)
                aumate_enviromet_human_mode(result_folder, xml_file_path)

            action_map = compute_valid_actions(mutated_env_path)
            unsafe_states = compute_unsafe_states(xml_file_path)

            task_count = 1  # Initialize task_count
            task_start_time = time.time()
            log_message(f"Task {task_count} for environment {environment} started at {time.ctime(task_start_time)}")

            initial_state = LoadConfig.load_InitialState(mutated_env_path)
            mutated_task_path = os.path.join(result_folder, f"task_{task_count}")

            if fuzzer.mutate_task:
                GenrateTask(mutated_env_path, mutated_task_path)
                log_message(f"Generated new task at: {mutated_task_path}")
            else:
                modified_state = UpdateTask(initial_state)
                log_message(f"Updated task with initial state: {initial_state}")

            for seed in fuzzer.seeds:
                random.seed(seed)
                remaining_coverage_matrix = copy.deepcopy(action_map)

                instruction_start_time = time.time()
                log_message(f"Instruction generation for seed {seed} started at {time.ctime(instruction_start_time)}")

                instruction_log_path = os.path.join(mutated_task_path, f"{seed}")

                fuzzInstructions(initial_state[0], modified_state[0], fuzzer.instruction_generation_time, action_map, unsafe_states, instruction_log_path, mutated_env_path)
                log_message(f"Fuzz instructions logged at: {instruction_log_path}")

            env_end_time = time.time()
            log_message(f"Processing environment: {environment} completed at {time.ctime(env_end_time)}")
            log_message(f"Total time for environment {environment}: {env_end_time - env_start_time} seconds")

    overall_end_time = time.time()
    log_message(f"Overall mutation process completed at {time.ctime(overall_end_time)}")
    log_message(f"Total runtime: {overall_end_time - overall_start_time} seconds")




if __name__ == '__main__':
    #Main()
    main()
