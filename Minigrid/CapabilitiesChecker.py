import os
import traceback


import xml.etree.ElementTree as ET
from Minigrid.EnvironmentState import Agent, Door, Key, Object, Lava, State


def hypothesisCapabilities(initial_state, final_state,instructions):
    sc = 'Agent reached the destination '
    if (initial_state.agent.dest_pos != final_state.agent.dest_pos):
        sc = 'Agent never reached the destination '

    logFile_Setting = loadSetting(os.path.join('.', 'Settings.xml'))

    if logFile_Setting.EnvName == 'Empty':
        if initial_state.agent.dest_pos == final_state.agent.dest_pos:
            return True, sc, 'get to the goal square'
        else:
            return True, sc, 'Could no get to the goal square'

    elif logFile_Setting.EnvName == 'Crossing':
        if initial_state.agent.dest_pos == final_state.agent.dest_pos:
            is_Crossing = CrossingEnv(final_state.agent.path)
            if is_Crossing == True:
                return is_Crossing, sc, 'Avoided Lava tiles and reached the goal square'
            else:
                return is_Crossing, sc, 'Did not Avoid Lava tiles and reached the goal square'
        else:
            return False ,sc, 'Agent never reached the goal square'

    elif logFile_Setting.EnvName == 'Dist_Shift':
        if initial_state.agent.dest_pos == final_state.agent.dest_pos:
            is_Crossing = CrossingEnv(final_state.agent.path)
            if is_Crossing == True:
                return is_Crossing, sc, 'Avoided Lava tiles and reached the goal square'
            else:
                return is_Crossing, sc, 'Did not Avoid Lava tiles and reached the goal square'
        else:
            return False, sc, 'Agent never reached the goal square'

    elif logFile_Setting.EnvName == 'Go_To_Door':
            is_achived, message =  Go_To_Door(final_state.agent.dest_pos, instructions, logFile_Setting)
            if is_achived == True:
                return True,sc, message
            else:
                return False, sc, message
    elif logFile_Setting.EnvName == 'Door_Key':
        if initial_state.agent.dest_pos == final_state.agent.dest_pos:
            return True, sc, 'used the key get to the goal square'
        else:
            return False, sc, 'Could not use the key to get to the goal square'

    else:
        return False, sc, 'Invalid Environment'


    #is_three_room_explode , visited_room = threeRoomExplore(final_state.agent.path)
    #if is_three_room_explode:
        #if initial_state.agent.dest_pos == final_state.agent.dest_pos:
            #return True,sc,visited_room
        #else:
            #return False, sc, visited_room

        # elif FourRoomExplore(initial_state,final_state):
        # return  True





def threeRoomExplore(finalPath):
    rooms = {
        "Room1": {"x_min": 0, "y_min": 0, "x_max": 9, "y_max": 9},
        "Room2": {"x_min": 11, "y_min": 0, "x_max": 19, "y_max": 9},
        "Room3": {"x_min": 0, "y_min": 11, "x_max": 9, "y_max": 19},
        "Room4": {"x_min": 11, "y_min": 11, "x_max": 19, "y_max": 19},
    }

    def find_room(x, y, rooms):
        for room_name, boundaries in rooms.items():
            if (boundaries["x_min"] <= x <= boundaries["x_max"] and
                    boundaries["y_min"] <= y <= boundaries["y_max"]):
                return room_name
        return None

    visited_rooms = set()

    for position in finalPath:
        room = find_room(position[0], position[1], rooms)
        if room:
            visited_rooms.add(room)

    print(visited_rooms)

    if len(visited_rooms) == 3:
        return True,visited_rooms
    #if len(visited_rooms) == 1:
        #return True,visited_rooms
    #elif len(visited_rooms) == 4:
        #return True, visited_rooms
    #elif len(visited_rooms) == 3:
        #return True, visited_rooms
    else:
        return False,visited_rooms

def FourRoomExplore():
    return True


def CrossingEnv(finalPath):
    tree = ET.parse(os.path.join('.', 'Config.xml'))
    root = tree.getroot()
    lavaTile = []
    for lava_elem in root.find('LavaTiles').findall('Lava'):
        lava = Lava(
             x=int(lava_elem.get('x')),  # x coordinate of lava tile
             y=int(lava_elem.get('y')),  # y coordinate of lava tile
             is_present=int(lava_elem.get('is_present')) #check if lava is present
        )
        lavaTile.append(lava)

    for position in finalPath:
        # Check if the position exists in the lavaTile array
        if any(lava.x == position[0] and lava.y == position[1] for lava in lavaTile):
            return False

    return True


def Go_To_Door(destination_pos, instructions,logFile_Setting):
    tree = ET.parse(os.path.join('.', 'Config.xml'))
    root = tree.getroot()
    door_regions = []
    Grid = root.find('Grid')
    grid_size = int(Grid.find('Size').get('grid_Size'))

    try:
        for door_elem in root.find('Doors').findall('Door'):
            if(logFile_Setting.color == door_elem.get('color')):
                door_x = int(door_elem.get('x'))
                door_y = int(door_elem.get('y'))

                # Define neighboring positions to the door coordinates
                neighbor_positions = [
                    (door_x + dx, door_y + dy)  # Calculate new position by adding dx and dy to door coordinates
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    # Consider only horizontal (left and right) and vertical (up and down) movements
                    # Filter out positions that fall within the grid boundaries, excluding the boundary states
                    if (0 < door_x + dx < grid_size - 1) and (0 < door_y + dy < grid_size - 1)
                ]

                door_regions.append(neighbor_positions)



        for region in door_regions:
            if destination_pos in region and instructions[-1] == "done":
                return True, f"Agent stands next the {logFile_Setting.color} door"
            elif destination_pos in region and instructions[-1] != "done":
                return False, f"Agent stands next the {logFile_Setting.color} door but last instruction was not done"
            else:
                return False, f"Agent did not stands next the {logFile_Setting.color} door"

    except Exception as e:
        error_stack = traceback.format_exc()
        error_message = f"An error occurred during mutation: {str(e)}\nError stack:\n{error_stack}"
        print(error_message)

    return False, 'An exception Occured'



def is_path_safe(agent_path, lava_tiles):
    for position in agent_path:
        for lava in lava_tiles:
            if lava.is_present and (lava.x, lava.y) == position:
                return False
    return True

def check_navigate_task(initial_state, final_state, task):
    if not is_path_safe(final_state.agent.path, final_state.lava_tiles):
        return False
    return final_state.agent.dest_pos == task.destination

def check_pickup_task(initial_state, final_state, task):
    if not is_path_safe(final_state.agent.path, final_state.lava_tiles):
        return False
    for key in final_state.keys:
        if key.color == task.color and key.is_picked == 1 and (key.x_init,key.y_init) == task.source:
            if(final_state.agent.dest_pos == task.destination):
                return True

    return False

def check_drop_task(initial_state, final_state, task):
    if not is_path_safe(final_state.agent.path, final_state.lava_tiles):
        return False
    for key in final_state.keys:
        if key.color == task.color :
            if key.is_picked == 1 and key.is_present == 1 :
                if (key.x_init, key.y_init) == task.destination:
                    return True
    return False

def check_move_task(initial_state, final_state, task):
    if not is_path_safe(final_state.agent.path, final_state.lava_tiles):
        return False
    for obj in final_state.objects:
        if obj.is_present == 1 and (obj.x, obj.y) == task.source and (obj.v,obj.w) == task.destination and obj.color == task.color:
            return True
    return False

def check_task_achieved(initial_state, final_state, task_path):
    parent_dir = os.path.dirname(task_path)
    task_path = os.path.join(parent_dir,'task.xml')
    tasks = parse_tasks(task_path)
    for task in tasks:
        if task.task_type == "navigate":
            return check_navigate_task(initial_state, final_state, task)
        elif task.task_type == "pickup":
            return check_pickup_task(initial_state, final_state, task)
        elif task.task_type == "drop":
            return check_drop_task(initial_state, final_state, task)
        elif task.task_type == "move":
            return check_move_task(initial_state, final_state, task)
        return False




class Task:
    def __init__(self, task_type, source, destination=None, obj=None, color=None, key_position=None, description=None):
        self.task_type = task_type
        self.source = source
        self.destination = destination
        self.object = obj
        self.color = color
        self.key_position = key_position
        self.description = description

    def __repr__(self):
        return (f"Task(task_type={self.task_type}, source={self.source}, destination={self.destination}, "
                f"object={self.object}, color={self.color}, key_position={self.key_position}, description={self.description})")

def parse_tasks(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    tasks = []

    for task_elem in root.findall('Task'):
        task_type = task_elem.find('type').text
        source = tuple(map(int, task_elem.find('source').text.split(',')))
        destination = task_elem.find('destination')
        destination = tuple(map(int, destination.text.split(','))) if destination is not None else None
        obj = task_elem.find('object').text if task_elem.find('object') is not None else None
        color = task_elem.find('color').text if task_elem.find('color') is not None else None
        key_position = task_elem.find('key_position')
        key_position = tuple(map(int, key_position.text.split(','))) if key_position is not None else None
        description = task_elem.find('description').text

        task = Task(task_type, source, destination, obj, color, key_position, description)
        tasks.append(task)

    return tasks





