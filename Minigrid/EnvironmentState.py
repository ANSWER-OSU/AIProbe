import xml.etree.ElementTree as ET
class Door:
    def __init__(self, x, y, status,color=None,locked=None):
        self.x = x
        self.y = y
        self.door_status = status
        self.color = color
        self.door_locked = locked

class Key:
    def __init__(self, x_init, y_init, is_picked, is_present,color):
        self.x_init = x_init
        self.y_init = y_init
        self.is_picked = is_picked
        self.is_present = is_present
        self.color = color

class Object:
    def __init__(self, x, y, pick_status, v, w, drop_status, is_present,color):
        self.x = x
        self.y = y
        self.pick_status = pick_status
        self.v = v
        self.w = w
        self.drop_status = drop_status
        self.is_present = is_present
        self.color = color

class Lava:
    def __init__(self, x, y, is_present):
        self.x = x
        self.y = y
        self.is_present = is_present

class Agent:
    def __init__(self, init_pos, init_direction, dest_pos, dest_direction, path):
        self.init_pos = init_pos
        self.init_direction = init_direction
        self.dest_pos = dest_pos
        self.dest_direction = dest_direction
        self.path = path

class Wall:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class State:
    def __init__(self):
        self.agent = None
        self.doors = []
        self.keys = []
        self.objects = []
        self.lava_tiles = []
        self.walls = []




def load_InitialState(file_path):
    initialEnvironment = State()

    tree = ET.parse(file_path)
    root = tree.getroot()

    agentInitialState = root.find('Agent')
    initialPosition = (int(agentInitialState.find('InitialPosition').get('x')), int(agentInitialState.find('InitialPosition').get('y')))
    initialDirection = agentInitialState.find('InitialDirection').get('theta')
    destinationPosition = (int(agentInitialState.find('DestinationPosition').get('x')), int(agentInitialState.find('DestinationPosition').get('y')))
    destinationDirection = agentInitialState.find('DestinationDirection').get('theta')
    agentFollowedPath = []
    initialEnvironment.agent = Agent(initialPosition, initialDirection, destinationPosition, destinationDirection, agentFollowedPath)

    Grid = root.find('Grid')
    GridSize = int(Grid.find('Size').get('grid_Size'))

    for door_elem in root.find('Doors').findall('Door'):
        door = Door(
            int(door_elem.get('x')),
            int(door_elem.get('y')),
            int(door_elem.get('door_open')),
            door_elem.get('color'),
            int(door_elem.get('door_locked'))
        )
        initialEnvironment.doors.append(door)

    for key_elem in root.find('Keys').findall('Key'):
        key = Key(
            x_init=int(key_elem.get('x_init')),
            y_init=int(key_elem.get('y_init')),
            is_picked=int(key_elem.get('is_picked')),
            is_present=int(key_elem.get('is_present')),
            color=key_elem.get('color')
        )
        initialEnvironment.keys.append(key)

    for obj_elem in root.find('Objects').findall('Object'):
        obj = Object(
            x=int(obj_elem.get('pick_x')),
            y=int(obj_elem.get('pick_y')),
            pick_status=int(obj_elem.get('pickStatus')),
            v=int(obj_elem.get('drop_x')),
            w=int(obj_elem.get('drop_y')),
            drop_status=int(obj_elem.get('dropStatus')),
            is_present=int(obj_elem.get('is_present')),
            color=obj_elem.get('color')
        )
        initialEnvironment.objects.append(obj)

    for lava_elem in root.find('LavaTiles').findall('Lava'):
        lava = Lava(
            x=int(lava_elem.get('x')),
            y=int(lava_elem.get('y')),
            is_present=int(lava_elem.get('is_present'))
        )
        initialEnvironment.lava_tiles.append(lava)

    for wall_elem in root.find('Walls').findall('Wall'):
        wall = Wall(
            x=int(wall_elem.get('x')),
            y=int(wall_elem.get('y'))
        )
        initialEnvironment.walls.append(wall)

    return initialEnvironment, GridSize