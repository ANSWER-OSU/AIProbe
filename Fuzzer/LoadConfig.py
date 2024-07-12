import xml.etree.ElementTree as ET
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '/Minigrid'))
from Minigrid.EnvironmentState import Agent, Door, Key, Object, Lava, State , Wall,Landmines

def load_InitialState(file_path):
    initialEnvironment = State()


    tree = ET.parse(file_path)
    root = tree.getroot()

    agentInitialState = root.find('Agent')
    initialPosition = (int(agentInitialState.find('InitialPosition').get('x')),int(agentInitialState.find('InitialPosition').get('y')))
    initialDirection = agentInitialState.find('InitialDirection').get('theta')
    destinationPosition = (int(agentInitialState.find('DestinationPosition').get('x')),int(agentInitialState.find('DestinationPosition').get('y')))
    destinationDirection = agentInitialState.find('DestinationDirection').get('theta')
    agentFollowedPath =  []
    initialEnvironment.agent = Agent(initialPosition,initialDirection,destinationPosition,destinationDirection,agentFollowedPath)

    Grid = root.find('Grid')

    GridSize = int(Grid.find('Size').get('grid_Size'))

    for door_elem in root.find('Doors').findall('Door'):
        door = Door(int(door_elem.get('x')), int(door_elem.get('y')), int(door_elem.get('door_open')),door_elem.get('color'),int(door_elem.get('door_locked')))
        initialEnvironment.doors.append(door)


    for key_elem in root.find('Keys').findall('Key'):
        key = Key(
            x_init=int(key_elem.get('x_init')), # x coordinate of key
            y_init=int(key_elem.get('y_init')), # y coordiante of key
            is_picked=int(key_elem.get('is_picked')),  # Assuming picked is 0 (not picked) or 1 (picked)
            is_present=int(key_elem.get('is_present')), # Assuming is_present is 1 when key is present, else 0
            color = key_elem.get('color')
        )
        initialEnvironment.keys.append(key)


    for obj_elem in root.find('Objects').findall('Object'):
        obj = Object(
            x=int(obj_elem.get('pick_x')),  # pick_x represents x coordinate of key
            y=int(obj_elem.get('pick_y')),  # pick_y represents y coordinate of key
            pick_status=int(obj_elem.get('pickStatus')),  # pick_status is 0 (not picked) or 1 (picked) 
            v=int(obj_elem.get('drop_x')),  # drop_x represents x coordinate of point where key is dropped
            w=int(obj_elem.get('drop_y')),  # drop_y represents y coordinate of point where key is dropped
            drop_status=int(obj_elem.get('dropStatus')),  # drop_status is 0 (not dropped) or 1 (dropped) 
            is_present=int(obj_elem.get('is_present')),
            color = obj_elem.get('color')
        )
        initialEnvironment.objects.append(obj)

    for lava_elem in root.find('LavaTiles').findall('Lava'):
        lava = Lava(
             x=int(lava_elem.get('x')),  # x coordinate of lava tile
             y=int(lava_elem.get('y')),  # y coordinate of lava tile
             is_present=int(lava_elem.get('is_present')) #check if lava is present
        )
        initialEnvironment.lava_tiles.append(lava)

    for wall_elem in root.find('Walls').findall('Wall'):
        wall = Wall(
            x=int(wall_elem.get('x')),
            y=int(wall_elem.get('y'))
        )
        initialEnvironment.walls.append(wall)

    for lava_elem in root.find('Landmines').findall('Landmine'):
        landmine = Landmines(
            x=int(lava_elem.get('x')),
            y=int(lava_elem.get('y')),
            is_present=int(lava_elem.get('is_present'))
        )
        initialEnvironment.landmines.append(landmine)
    return initialEnvironment,GridSize


class Setting:
    def __init__(self, environment_logs_path, mutator_logs_path,Instruction_logs_path,EnvName,color,timout,seed):
        self.environment_logs_path = environment_logs_path
        self.mutator_logs_path = mutator_logs_path
        self.EnvName = EnvName
        self.color = color
        self.Instruction_logs_path = Instruction_logs_path
        self.timout =timout
        self.seed = seed


class Script_Setting:
    def __init__(self, environment_logs_path, mutator_logs_path,Instruction_logs_path):
        self.environment_logs_path = environment_logs_path
        self.mutator_logs_path = mutator_logs_path
        self.Instruction_logs_path = Instruction_logs_path



def loadSetting(xml_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Extract data from the XML
    environment_logs_path = root.find("./EnviromentLogs").attrib['path']
    mutator_logs_path = root.find("./MutatorLogs").attrib['path']
    Instruction_logs_path = root.find("./InstructionLog").attrib['path']
    EnvName = root.find("./Enviroment").attrib['name']
    color = root.find("./Enviroment").attrib['color']
    timout = root.find("./timeout").attrib['time']
    seed = root.find("./seed").attrib['seed_number']

    # Create Setting object with extracted data
    setting = Setting(environment_logs_path, mutator_logs_path,Instruction_logs_path,EnvName,color,timout,seed)

    return setting

def load_Script_Setting(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Extract data from the XML
    environment_logs_path = root.find("./EnviromentLogs").attrib['path']
    mutator_logs_path = root.find("./MutatorLogs").attrib['path']
    Instruction_logs_path = root.find("./InstructionLog").attrib['path']

    # Create Setting object with extracted data
    setting = Script_Setting(environment_logs_path, mutator_logs_path, Instruction_logs_path)

    return setting



class FuzzerSetting:
    def __init__(self, EnvName, timeout, seeds, log_file_path, mutators, env_config_path,mutate_env, mutate_task, mutate_env_time, task_mutate_time, instruction_generation_time):
        self.EnvName = EnvName
        self.timeout = timeout
        self.seeds = seeds
        self.log_file_path = log_file_path
        self.mutators = mutators
        self.env_path = env_config_path
        self.mutate_env = mutate_env
        self.mutate_task = mutate_task
        self.mutate_env_time = mutate_env_time
        self.task_mutate_time = task_mutate_time
        self.instruction_generation_time = instruction_generation_time


def load_fuzzer_setting(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Extract data from the XML
    timeout = int(root.find("./Settings/Timeout").text)
    log_file_path = root.find("./Settings/LogFilePath").text
    Env_name = root.find("./Settings/Enviroment").text
    env_config_path = root.find("./Settings/EnviromentConfig").text
    mutate_env = root.find("./Settings/MutateEnv").text.lower() == 'true'
    mutate_task = root.find("./Settings/MutateTask").text.lower() == 'true'
    mutate_env_time = int(root.find("./Settings/MutateEnvTime").text)
    task_mutate_time = int(root.find("./Settings/TaskMutateTime").text)
    instruction_generation_time = int(root.find("./Settings/InstructionGenerationTime").text)


    # Extract seeds
    seeds = [int(seed.text) for seed in root.find("./SeedList").findall("Seed")]

    # Extract mutators
    mutators = []
    for mutator_elem in root.find("./Mutators").findall("Mutator"):
        mutator = {
            'Name': mutator_elem.find("Name").text,
            'Enabled': mutator_elem.find("Enabled").text.lower() == 'true',
            'Probability': float(mutator_elem.find("Probability").text)
        }
        mutators.append(mutator)

    # Create Setting object with extracted data
    setting = FuzzerSetting(Env_name, timeout, seeds, log_file_path, mutators,env_config_path,mutate_env, mutate_task, mutate_env_time, task_mutate_time, instruction_generation_time)

    return setting

