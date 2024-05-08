import os
import random
import shutil
import xml.etree.ElementTree as ET
import subprocess

from Code.LoadConfig import load_InitialState
from environment import send_slack_message


def update_setting_xml(setting_xml_path, new_log_number,current_env_mutauion):
    tree = ET.parse(setting_xml_path)
    root = tree.getroot()

    # Update the log paths with the new number
    for setting in root.findall('EnviromentLogs'):
        setting.set('path', f'Results Log\\Lava Env\\GuidedFuzz\\Hpc\\60\\Log-Lava-Env-{new_log_number}.txt')

    for setting in root.findall('MutatorLogs'):
        setting.set('path', f'Results Log\\Lava Env\\GuidedFuzz\\hpc\\60\\Mutator-Log-Lava-Env-{new_log_number}.txt')

    for setting in root.findall('InstructionLog'):
        setting.set('path', f'Results Log\\Lava Env\\GuidedFuzz\\hpc\\60\\Log-Lava-Env.json')

    # Save the changes to the Setting.xml file
    tree.write(setting_xml_path)
    tree.write(setting_xml_path)

def main():
    setting_xml_path = 'Settings.xml'


    current_env_mutauion = 4
    while current_env_mutauion <=4:
        #mutate_lava_positions()
        message = f"---------- Running For the Env no {current_env_mutauion} ------------"
        send_slack_message(message)
        current_log_number = 1
        while current_log_number <= 10:  # Run continuously until the log number exceeds 6

            update_setting_xml(setting_xml_path, current_log_number,current_env_mutauion)

            try:
                proc = subprocess.Popen(['python', 'mutate.py'])
                proc.wait()  # Wait for the subprocess to finish
            except subprocess.CalledProcessError as e:
                print(f"Error running mutator.py: {e}")
                return

            current_log_number += 1

        message = f"---------- Fuzzed process completed successfully ------------"
        send_slack_message(message)
        print("Mutation process completed successfully.")
        current_env_mutauion+=1


def mutate_lava_positions():
    file_path = os.path.join('.', 'Config.xml')
    test_environment, gridSize = load_InitialState(file_path)
    valid_positions = list(range(1, gridSize - 1))  # Valid positions excluding boundaries

    tree = ET.parse(file_path)
    root = tree.getroot()

    print("Initial Lava Tiles:")
    lava_elements = list(root.findall('.//Lava'))

    # Sync initial lava positions from XML for display
    for lava, lava_tile in zip(lava_elements, test_environment.lava_tiles):
        print(f"  Lava Tile at ({lava.get('x')}, {lava.get('y')}) - Present: {lava.get('is_present')}")

    mutation_chance = 0.80  # 80% chance to attempt moving each lava tile

    # Mutate lava positions
    for lava, lava_tile in zip(lava_elements, test_environment.lava_tiles):
        if random.random() < mutation_chance:
            new_x, new_y = random.choice(valid_positions), random.choice(valid_positions)
            if ((new_x, new_y) != (1, 1) and (new_x, new_y) != (int(lava.get('x')), int(lava.get('y')))):
                print(f"Moving Lava Tile from ({lava.get('x')}, {lava.get('y')}) to ({new_x}, {new_y})")
                lava.set('x', str(new_x))
                lava.set('y', str(new_y))
                lava.set('is_present', '1')  # Ensure the lava tile is marked as present after moving

    # Save the mutated XML
    tree.write(file_path)

    print("Final Lava Tiles:")
    for lava in root.findall('.//Lava'):
        print(f"  Lava Tile at ({lava.get('x')}, {lava.get('y')}) - Present: {lava.get('is_present')}")


if __name__ == "__main__":
    main()
