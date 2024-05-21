import xml.etree.ElementTree as ET
from EnvironmentState import Agent, Door, Key, Object, Lava, State

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
            is_present=int(obj_elem.get('is_present'))
        )
        initialEnvironment.objects.append(obj)

    for lava_elem in root.find('LavaTiles').findall('Lava'):
        lava = Lava(
             x=int(lava_elem.get('x')),  # x coordinate of lava tile
             y=int(lava_elem.get('y')),  # y coordinate of lava tile
             is_present=int(lava_elem.get('is_present')) #check if lava is present
        )
        initialEnvironment.lava_tiles.append(lava)


    return initialEnvironment,GridSize


class Setting:
    def __init__(self, environment_logs_path, mutator_logs_path,Instruction_logs_path,EnvName,color,timout):
        self.environment_logs_path = environment_logs_path
        self.mutator_logs_path = mutator_logs_path
        self.EnvName = EnvName
        self.color = color
        self.Instruction_logs_path = Instruction_logs_path
        self.timout =timout


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

    # Create Setting object with extracted data
    setting = Setting(environment_logs_path, mutator_logs_path,Instruction_logs_path,EnvName,color,timout)

    return setting

def load_Script_Setting(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Extract data from the XML
    environment_logs_path = root.find("./EnviromentLogs").attrib['path']
    mutator_logs_path = root.find("./MutatorLogs").attrib['path']
    Instruction_logs_path = root.find("./InstructionLog").attrib['path']

    # Create Setting object with extracted data
    setting = Setting(environment_logs_path, mutator_logs_path, Instruction_logs_path)

    return setting





