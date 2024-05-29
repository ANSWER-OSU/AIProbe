import os
import random
import time

import LoadConfig
from Fuzzer.Mutation.mutateTask import GenrateTask

from Mutation.mutateEnv import mutate_enviroment , EnvName
from Minigrid.environment import aumate_enviromet_human_mode


def Main():

    # Loading the setting
    fuzzer =  LoadConfig.load_fuzzer_setting('FuzzConfig.xml')

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Running For all seed values
    for seed in fuzzer.seeds :
        # Mutatee the Env
        random.seed(seed)

        xml_file_path = "A:\Github repos\Answer\AIProbe\Minigrid\Config.xml"

        # Start the timer
        start_time = time.time()
        elapsed_time = 1
        env_count = 1
        genrateTaskTime = 1

        while env_count < 30:  # 300 seconds = 5 minutes

            # Mutate the environment
            mutated_xml_content = mutate_enviroment(xml_file_path,EnvName.MINIGRID)
            screenshot_path = os.path.join(parent_dir, "Result", "Minigrid",str(seed), f"Env-{env_count}")
            result_folder = updateFilePath(screenshot_path)

            # saving the Env config
            mutated_env_path = os.path.join(result_folder,'Config.xml')
            updateFilePath(mutated_env_path)
            with open(mutated_env_path, "w", encoding="utf-8") as f:
                f.write(mutated_xml_content)

            task_count = 1

            while genrateTaskTime < 300 :

                GenrateTask(mutated_env_path,task_count,result_folder)




            # Render the environment and save the screenshot

            aumate_enviromet_human_mode(result_folder, xml_file_path)
            env_count += 1
            # Update the elapsed time
            elapsed_time = time.time() - start_time
            print(f"sec done: {elapsed_time}")

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