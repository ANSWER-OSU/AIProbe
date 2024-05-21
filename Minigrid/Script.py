import os
import random
import shutil
import xml.etree.ElementTree as ET
import subprocess

from LoadConfig import load_InitialState , load_Script_Setting
from environment import send_slack_message

def create_directories_if_not_exist(file_path):
    """Creates directories leading to the file path if they don't exist."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def update_setting_xml(setting_xml_path, new_log_number,script_setting_path,iteration, current_env_mutation,seed):
    tree = ET.parse(setting_xml_path)
    root = tree.getroot()

    script_setting =  load_Script_Setting(script_setting_path)

    # Define paths
    env_log_path = f"{script_setting.environment_logs_path}-Env_log{new_log_number}.txt"
    mutator_log_path = f"{script_setting.mutator_logs_path}-mutator-{new_log_number}.txt"
    instruction_log_path = f"{script_setting.mutator_logs_path}-Log-Lava-Env.json"

    # Create the directories if they don't exist
    create_directories_if_not_exist(env_log_path)
    create_directories_if_not_exist(mutator_log_path)
    create_directories_if_not_exist(instruction_log_path)

    # Update the log paths in the XML tree
    for setting in root.findall('EnviromentLogs'):
        setting.set('path', env_log_path)

    for setting in root.findall('MutatorLogs'):
        setting.set('path', mutator_log_path)

    for setting in root.findall('InstructionLog'):
        setting.set('path', instruction_log_path)

    for setting in root.findall('seed'):
        setting.set('seed_number', str(seed))  # Ensure the seed number is a string

    # Save the changes to the XML file
    tree.write(setting_xml_path)

def main():
    setting_xml_path = 'Settings.xml'
    Script_setting_path = 'Script_setting.xml'
    max_env_mutations = 1
    current_env_mutation = 0
    seeds = [11,56,32,88,41,29,78,93,100,200]
    while current_env_mutation <= max_env_mutations:
        message = f"---------- Running For the Env no {current_env_mutation} ------------"
        send_slack_message(message)
        current_log_number = 1
        for seed in seeds:
            #while current_log_number <= 10:

            update_setting_xml(setting_xml_path, current_log_number,Script_setting_path,current_log_number, current_env_mutation,seed)

            try:
                    proc = subprocess.Popen(['python', 'mutate.py'])
                    proc.wait()
            except subprocess.CalledProcessError as e:
                    print(f"Error running mutator.py: {e}")
                    return
            current_log_number+= 1



        message = f"---------- Fuzzed process completed successfully ------------"
        send_slack_message(message)
        print("Mutation process completed successfully.")
        current_env_mutation += 1

def mutate_lava_positions():
    file_path = os.path.join('.', 'Config.xml')
    test_environment, gridSize = load_InitialState(file_path)
    valid_positions = list(range(1, gridSize - 1))

    tree = ET.parse(file_path)
    root = tree.getroot()

    print("Initial Lava Tiles:")
    lava_elements = list(root.findall('.//Lava'))

    for lava, lava_tile in zip(lava_elements, test_environment.lava_tiles):
        print(f"  Lava Tile at ({lava.get('x')}, {lava.get('y')}) - Present: {lava.get('is_present')}")

    mutation_chance = 0.80

    for lava, lava_tile in zip(lava_elements, test_environment.lava_tiles):
        if random.random() < mutation_chance:
            new_x, new_y = random.choice(valid_positions), random.choice(valid_positions)
            if (new_x, new_y) != (1, 1) and (new_x, new_y) != (int(lava.get('x')), int(lava.get('y'))):
                print(f"Moving Lava Tile from ({lava.get('x')}, {lava.get('y')}) to ({new_x}, {new_y})")
                lava.set('x', str(new_x))
                lava.set('y', str(new_y))
                lava.set('is_present', '1')

    tree.write(file_path)

    print("Final Lava Tiles:")
    for lava in root.findall('.//Lava'):
        print(f"  Lava Tile at ({lava.get('x')}, {lava.get('y')}) - Present: {lava.get('is_present')}")

def getConfigFiles(directory_path):
    directories = []

    # Check if the specified path is actually a directory
    if os.path.isdir(directory_path):
        # List all files and directories in the specified directory
        for item in os.listdir(directory_path):
            # Full path of the item
            item_path = os.path.join(directory_path, item)
            # Check if the item is a directory
            if os.path.isdir(item_path):
                directories.append(item)

    print(directories)

if __name__ == "__main__":
    main()
