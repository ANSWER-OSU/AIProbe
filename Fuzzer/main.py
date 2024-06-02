import os
import random
import time

import LoadConfig
from Fuzzer.Mutation.mutateTask import GenrateTask
from Minigrid.environment import execute_and_evaluate_task
from Fuzzer.Mutation.mutateInstruction import fuzz_instruction

from Fuzzer.Mutation.mutateEnv import mutate_environment, EnvName
from Minigrid.environment import aumate_enviromet_human_mode


def Main():

    # Loading the setting
    fuzzer =  LoadConfig.load_fuzzer_setting('FuzzConfig.xml')

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Running For all seed values
    for seed in fuzzer.seeds :
        # Mutatee the Env
        random.seed(seed)

        xml_file_path = fuzzer.env_path

        # Start the timer
        start_time = time.time()
        elapsed_time = 1
        env_mutate_time = 1
        env_count = 1
        task_mutate_time = 1
        instruction_mutate_time = 1


        while env_mutate_time < 600:  # 300 seconds = 5 minutes

            # Mutate the environment
            mutated_xml_content = mutate_environment(xml_file_path,EnvName.MINIGRID)
            screenshot_path = os.path.join(parent_dir, "Result", "Minigrid",str(seed), f"Env-{env_count}")
            result_folder = updateFilePath(screenshot_path)

            # saving the Env config
            mutated_env_path = os.path.join(result_folder,'Config.xml')
            updateFilePath(mutated_env_path)
            with open(mutated_env_path, "w", encoding="utf-8") as f:
                f.write(mutated_xml_content)

            task_count = 1
            aumate_enviromet_human_mode(result_folder, xml_file_path)

            task_start_time = time.time()
            task_elapsed_time = 1
            while task_elapsed_time < 300 :
                mutated_task_path = os.path.join(result_folder,f"task_{task_count}")
                GenrateTask(mutated_env_path,mutated_task_path)

                instruction_number = 1
                instruction_start_time = time.time()
                instruction_mutate_time = 1
                while instruction_mutate_time < 300:
                    instruction_log_path = os.path.join(mutated_task_path,f"log.txt")
                    if fuzz_instruction(fuzzer.EnvName,instruction_log_path,xml_file_path):
                        print(f"Instruction found for seed {seed} env {env_count} task {task_count}")
                        task_count += 1

                        break;

                    instruction_mutate_time = time.time() - instruction_start_time


                    instruction_number+=1


                task_count+=1
                task_mutate_time+=1

                task_elapsed_time = time.time() - task_start_time




            # Render the environment and save the screenshot

            env_mutate_time+=1
            env_count += 1
            # Update the elapsed time


        #mutate_minigrid_environment(xml_file_path)
        #aumate_enviromet_human_mode('A:\Github repos\Answer\AIProbe\Result\Minigrid\MutationEnv',xml_file_path,seed)
        print(seed)







    # mutate the task


    # get the fuzzed instruction


    # get the env result





def updateFilePath(log_file):
    # Check if the log file path exists, if not, create it
    log_file_dir = os.path.dirname(log_file)
    if not os.path.exists(log_file_dir):
        os.makedirs(log_file_dir)
        print(f"Created directory for log file: {log_file_dir}")
    return os.path.abspath(log_file)


if __name__ == '__main__':
    Main()