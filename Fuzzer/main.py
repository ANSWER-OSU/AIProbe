import copy
import os
import random
import time
import sys

# Add the project root to the PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
print(f"Project root: {project_root}")
print(f"PYTHONPATH: {sys.path}")

import LoadConfig


from Fuzzer.Mutation.mutateEnv import mutate_environment,use_exsisting_enviroment, EnvName
from Minigrid.environment import aumate_enviromet_human_mode
from Fuzzer.Mutation.mutateTask import GenrateTask,PickupTask
from Fuzzer.Mutation.mutateInstruction import fuzz_instruction
from Fuzzer.CoverageMatrix import compute_valid_actions


def Main():
    # Loading the setting
    fuzzer = LoadConfig.load_fuzzer_setting('FuzzConfig.xml')

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    overall_start_time = time.time()  # Start time for the overall mutation process

    # Running for all seed values
    for seed in fuzzer.seeds:
        # Mutate the Env
        random.seed(seed)

        if(seed != 29 ):
            continue;
        xml_file_path = os.path.join(parent_dir,"Minigrid","Config.xml")
        env_count = 1  # Initialize env_count

        print(f"Running for seed {seed}")

        seed_start_time = time.time()  # Start time for the current seed

        while time.time() - seed_start_time < fuzzer.mutate_env_time:  # 3600 seconds = 1 hour per seed
            env_start_time = time.time()  # Start time for the current environment mutation

            print(f"Running for env {env_count}")

            if(env_count > 7):
                break
            screenshot_path = os.path.join(parent_dir, "Result", "FourRoom", str(seed), f"Env-{env_count}")
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

if __name__ == '__main__':
    Main()
