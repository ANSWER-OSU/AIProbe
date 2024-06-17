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
from Fuzzer.Mutation.mutateTask import GenrateTask
from Minigrid.environment import execute_and_evaluate_task
from Fuzzer.Mutation.mutateInstruction import fuzz_instruction

from Fuzzer.Mutation.mutateEnv import mutate_environment, EnvName
from Minigrid.environment import aumate_enviromet_human_mode


def Main():
    # Loading the setting
    fuzzer = LoadConfig.load_fuzzer_setting('FuzzConfig.xml')

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    overall_start_time = time.time()  # Start time for the overall mutation process

    # Running for all seed values
    for seed in fuzzer.seeds:
        # Mutate the Env
        random.seed(seed)


        xml_file_path = fuzzer.env_path
        env_count = 1  # Initialize env_count

        print(f"Running for seed {seed}")

        seed_start_time = time.time()  # Start time for the current seed

        while time.time() - seed_start_time < 3600:  # 3600 seconds = 1 hour per seed
            env_start_time = time.time()  # Start time for the current environment mutation

            print(f"Running for env {env_count}")
            # Mutate the environment
            mutated_xml_content = mutate_environment(xml_file_path, EnvName.MINIGRID)
            screenshot_path = os.path.join(parent_dir, "Result", "Minigrid", str(seed), f"Env-{env_count}")
            result_folder = updateFilePath(screenshot_path)

            # Saving the Env config
            print(f"Config files: {os.path.join(result_folder)}")
            mutated_env_path = os.path.join(result_folder, 'Config.xml')
            updateFilePath(mutated_env_path)
            with open(mutated_env_path, "w", encoding="utf-8") as f:
                f.write(mutated_xml_content)

            aumate_enviromet_human_mode(result_folder, xml_file_path)

            task_count = 1  # Initialize task_count
            while time.time() - env_start_time < 900 and time.time() - seed_start_time < 3600:  # 900 seconds = 15 minutes per environment
                task_start_time = time.time()

                mutated_task_path = os.path.join(result_folder, f"task_{task_count}")
                GenrateTask(mutated_env_path, mutated_task_path)

                instruction_start_time = time.time()
                while time.time() - instruction_start_time < 180 and time.time() - seed_start_time < 3600:  # 180 seconds = 3 minutes per instruction
                    instruction_log_path = os.path.join(mutated_task_path, f"log.txt")
                    if fuzz_instruction(fuzzer.EnvName, instruction_log_path, xml_file_path):
                        print(f"Instruction found for seed {seed} env {env_count} task {task_count}")
                        break  # Exit the instruction loop

                    if time.time() - task_start_time >= 600:  # 600 seconds = 10 minutes per task
                        break  # Exit the task loop

                task_count += 1

            env_count += 1

            # Exit the environment loop if the time limit is reached
            if time.time() - seed_start_time >= 3600:
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
