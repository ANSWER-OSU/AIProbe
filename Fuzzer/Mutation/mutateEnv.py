from enum import Enum
import xml.etree.ElementTree as ET
import random
import os

# Define the global colors list
colors = ["red", "blue", "green", "yellow", "grey"]
key_color = ["red", "blue", "green", "yellow", "grey"]

class EnvName(Enum):
    FLAPPY_BIRD = "flappy_bird"
    MINIGRID = "minigrid"
    CATCHER = "catcher"
    Four_Room = "four_room"

# Generate random attributes for elements of minigrid env
def randomize_attributes(element, attributes, grid_size, walls_positions=None, agent_pos=None, dest_pos=None,used_colors=None):
    walls_positions = walls_positions or set()
    used_colors = used_colors or set()
    available_colors = key_color

    for attr in attributes:
        if attr in ["x", "x_init", "y_init", "pick_x", "pick_y", "drop_x", "drop_y"]:
            while True:
                x = random.randint(1, grid_size - 2)  # Exclude boundaries 0 and grid_size - 1
                y = random.randint(1, grid_size - 2)
                if 1 <= x <= grid_size - 2 and 1 <= y <= grid_size - 2 and (x, y) not in walls_positions and (x, y) != agent_pos and (x, y) != dest_pos:
                    element.set(attr, str(x))
                    if(attr == "x"):
                        element.set("y",str(y))
                    break
        elif attr in ["is_present"]:
            #element.set(attr, str(random.choice([0, 1])))
            element.set(attr, '1')
        elif attr in ["is_picked", "pickStatus", "dropStatus"]:
            element.set(attr, "0")  # Always set pickStatus and dropStatus to 0
        elif attr == "color":
            if available_colors:
                color = random.choice(key_color)
                element.set(attr, color)
                key_color.remove(color)

            else:
                element.set(attr, random.choice(colors))
        elif attr == "theta":
            element.set(attr, random.choice(["n", "e", "s", "w"]))

def create_walls_based_on_doors(root, grid_size, agent_pos):
    doors = root.find("Doors")
    walls = root.find("Walls")

    for door in doors.findall("Door"):
        door_x = int(door.get("x"))
        door_y = int(door.get("y"))

        # Randomly decide whether the wall will be horizontal or vertical
        if random.choice(["horizontal", "vertical"]) == "horizontal":
            # Create a random number of horizontal walls around the door
            num_walls = random.randint(1, grid_size - 2)  # Random number of walls, excluding boundaries
            for x in range(max(1, door_x - num_walls), min(grid_size - 1, door_x + num_walls + 1)):
                if (x, door_y) != agent_pos and x != door_x:  # Ensure not to place a wall on the door or agent's position
                    wall = ET.SubElement(walls, "Wall")
                    wall.set("x", str(x))
                    wall.set("y", str(door_y))
        else:
            # Create a random number of vertical walls around the door
            num_walls = random.randint(1, grid_size - 2)  # Random number of walls, excluding boundaries
            for y in range(max(1, door_y - num_walls), min(grid_size - 1, door_y + num_walls + 1)):
                if (door_x, y) != agent_pos and y != door_y:  # Ensure not to place a wall on the door or agent's position
                    wall = ET.SubElement(walls, "Wall")
                    wall.set("x", str(door_x))
                    wall.set("y", str(y))

def mutate_minigrid_environment(xml_file_path):
    # Read the XML content from the file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Get the grid size
    grid = root.find("Grid")
    grid_size = 7  # Default value if not found
    if grid is not None:
        size_element = grid.find("Size")
        if size_element is not None:
            grid_size = int(size_element.get("grid_Size"))

    # Change agent's initial position and direction
    agent = root.find("Agent")
    agent_pos = (1, 1)  # Default value if not found
    if agent is not None:
        initial_position = agent.find("InitialPosition")
        if initial_position is not None:
            initial_position.set("x", str(random.randint(1, grid_size - 2)))  # Exclude boundaries
            initial_position.set("y", str(random.randint(1, grid_size - 2)))  # Exclude boundaries
            agent_pos = (int(initial_position.get("x")), int(initial_position.get("y")))
        initial_direction = agent.find("InitialDirection")
        if initial_direction is not None:
            randomize_attributes(initial_direction, ["theta"], grid_size)
        destination_position = agent.find("DestinationPosition")
        if destination_position is not None:
            randomize_attributes(destination_position, ["x", "y"], grid_size)
        destination_direction = agent.find("DestinationDirection")
        if destination_direction is not None:
            randomize_attributes(destination_direction, ["theta"], grid_size)

    # Change positions of keys
    keys = root.find("Keys")
    if keys is not None:
        # Remove existing keys
        for key in list(keys):
            keys.remove(key)

        # Add a random number of new keys
        num_keys = random.randint(1, grid_size - 2)
        for _ in range(num_keys):
            new_key = ET.SubElement(keys, "Key")
            while True:
                randomize_attributes(new_key, ["x_init", "y_init", "is_picked", "is_present", "color"], grid_size)
                key_pos = (int(new_key.get("x_init")), int(new_key.get("y_init")))
                if key_pos != agent_pos and 1 <= key_pos[0] <= grid_size - 2 and 1 <= key_pos[1] <= grid_size - 2:
                    break

    # Randomly add or remove doors
    doors = root.find("Doors")
    if doors is not None:
        # Remove some doors
        for door in list(doors):
            doors.remove(door)

        # Add new doors
        for _ in range(random.randint(0, 3)):  # Add up to 3 new doors
            new_door = ET.SubElement(doors, "Door")
            while True:
                randomize_attributes(new_door, ["x", "y", "door_open", "color", "door_locked"], grid_size)
                door_positions = (int(new_door.get("x")), int(new_door.get("y")))
                if door_positions != agent_pos and 1 <= door_positions[0] <= grid_size - 2 and 1 <= door_positions[1] <= grid_size - 2:
                    break

    # Change positions and attributes of objects
    objects = root.find("Objects")
    if objects is not None:
        # Remove existing objects
        for obj in list(objects):
            objects.remove(obj)

        # Add a random number of new objects
        num_objects = random.randint(1, grid_size - 2)
        for _ in range(num_objects):
            new_obj = ET.SubElement(objects, "Object")
            while True:
                randomize_attributes(new_obj, ["pick_x", "pick_y", "pickStatus", "drop_x", "drop_y", "dropStatus", "is_present", "color"], grid_size)
                obj_pos = (int(new_obj.get("pick_x")), int(new_obj.get("pick_y")))
                if obj_pos != agent_pos and 1 <= obj_pos[0] <= grid_size - 2 and 1 <= obj_pos[1] <= grid_size - 2:
                    break

    # Randomly add or remove lava tiles
    lava_tiles = root.find("LavaTiles")
    if lava_tiles is not None:
        # Remove some lava tiles
        for lava in list(lava_tiles):
            lava_tiles.remove(lava)

        # Add new lava tiles
        for _ in range(random.randint(0, grid_size)):  # Add up to 5 new lava tiles
            new_lava = ET.SubElement(lava_tiles, "Lava")
            while True:
                randomize_attributes(new_lava, ["x", "y", "is_present"], grid_size)
                lava_pos = (int(new_lava.get("x")), int(new_lava.get("y")))
                if 1 <= lava_pos[0] <= grid_size - 2 and 1 <= lava_pos[1] <= grid_size - 2:
                    break

    # Remove existing walls
    walls = root.find("Walls")
    if walls is not None:
        for wall in list(walls):
            walls.remove(wall)

    # Create walls based on doors
    create_walls_based_on_doors(root, grid_size, agent_pos)

    # Preserve the Grid element without changes
    if grid is not None:
        grid_size_element = grid.find("Size").get("grid_Size")

    # Convert the mutated tree back to a string
    mutated_xml_string = ET.tostring(root, encoding="unicode")

    # Parse the mutated string again to reinsert the unchanged Grid element
    mutated_root = ET.fromstring(mutated_xml_string)
    if grid is not None:
        grid_element = mutated_root.find("Grid")
        size_element = grid_element.find("Size")
        size_element.set("grid_Size", grid_size_element)

    final_xml_string = ET.tostring(mutated_root, encoding="unicode")

    # Write the mutated XML content back to a new file
    mutated_file_path = os.path.splitext(xml_file_path)[0] + ".xml"
    with open(mutated_file_path, "w", encoding="utf-8") as f:
        f.write(final_xml_string)

    return final_xml_string


def create_four_room_structure(root, grid_size, agent_pos, dest_pos):
    walls = root.find("Walls")
    if walls is None:
        walls = ET.SubElement(root, "Walls")

    mid_x = grid_size // 2
    mid_y = grid_size // 2

    walls_positions = set()

    # Create vertical wall
    for i in range(1, grid_size - 1):
        if i != mid_y and (mid_x, i) != agent_pos and (mid_x, i) != dest_pos:
            wall = ET.SubElement(walls, "Wall")
            wall.set("x", str(mid_x))
            wall.set("y", str(i))
            walls_positions.add((mid_x, i))

    # Create horizontal wall
    for i in range(1, grid_size - 1):
        if i != mid_x and (i, mid_y) != agent_pos and (i, mid_y) != dest_pos:
            wall = ET.SubElement(walls, "Wall")
            wall.set("x", str(i))
            wall.set("y", str(mid_y))
            walls_positions.add((i, mid_y))

    # Randomize doorways in the walls
    vertical_door_y = random.randint(1, grid_size - 2)
    horizontal_door_x = random.randint(1, grid_size - 2)
    doorways = [(mid_x, vertical_door_y), (horizontal_door_x, mid_y)]
    for dx, dy in doorways:
        for wall in walls.findall("Wall"):
            if wall.get("x") == str(dx) and wall.get("y") == str(dy):
                walls.remove(wall)
                walls_positions.remove((dx, dy))

    return walls_positions

def mutate_four_room_environment(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Get the grid size
    grid = root.find("Grid")
    grid_size = 7  # Default value if not found
    if grid is not None:
        size_element = grid.find("Size")
        if size_element is not None:
            grid_size = int(size_element.get("grid_Size"))

    # Change agent's initial position and direction
    agent = root.find("Agent")
    agent_pos = (1, 1)  # Default value if not found
    dest_pos = (grid_size - 2, grid_size - 2)  # Default value if not found
    if agent is not None:
        initial_position = agent.find("InitialPosition")
        if initial_position is not None:
            initial_position.set("x", str(random.randint(1, grid_size - 2)))  # Exclude boundaries
            initial_position.set("y", str(random.randint(1, grid_size - 2)))  # Exclude boundaries
            agent_pos = (int(initial_position.get("x")), int(initial_position.get("y")))
        initial_direction = agent.find("InitialDirection")
        if initial_direction is not None:
            randomize_attributes(initial_direction, ["theta"], grid_size)
        destination_position = agent.find("DestinationPosition")
        if destination_position is not None:
            randomize_attributes(destination_position, ["x", "y"], grid_size)
            dest_pos = (int(destination_position.get("x")), int(destination_position.get("y")))
        destination_direction = agent.find("DestinationDirection")
        if destination_direction is not None:
            randomize_attributes(destination_direction, ["theta"], grid_size)

    occupied_positions = set()

    # Remove existing keys
    keys = root.find("Keys")
    if keys is not None:
        for key in list(keys):
            keys.remove(key)

    # Remove existing walls
    walls = root.find("Walls")
    if walls is not None:
        for wall in list(walls):
            walls.remove(wall)

    walls_positions = create_four_room_structure(root, grid_size, agent_pos, dest_pos)
    for wall in walls_positions:
        occupied_positions.add(wall)

    # Remove existing lava tiles
    lava_tiles = root.find("LavaTiles")
    if lava_tiles is not None:
        for lava in list(lava_tiles):
            lava_tiles.remove(lava)


    # if lava_tiles is None:
    #     lava_tiles = ET.SubElement(root, "LavaTiles")
    #
    # lava_positions = set()
    # no_of_lava = random.randint(10, 15)
    # for _ in range(no_of_lava):  # Add up to grid_size new lava tiles
    #     new_lava = ET.SubElement(lava_tiles, "Lava")
    #     while True:
    #         randomize_attributes(new_lava, ["x", "y", "is_present"], grid_size)
    #         lava_pos = (int(new_lava.get("x")), int(new_lava.get("y")))
    #         if(new_lava.get("is_present") == '1'):
    #             if lava_pos != agent_pos and 1 <= lava_pos[0] <= grid_size - 2 and 1 <= lava_pos[1] <= grid_size - 2 and lava_pos not in walls_positions:
    #                 lava_positions.add(lava_pos)
    #                 break

    # Remove existing doors
    doors = root.find("Doors")
    if doors is not None:
        for door in list(doors):
            doors.remove(door)

    # Remove existing objects
    objects = root.find("Objects")
    if objects is not None:
        for obj in list(objects):
            objects.remove(obj)

    # Create four-room structure and get wall positions

    used_colors = set()

    # Add a random number of new keys
    if keys is not None:
        num_keys = random.randint(1, 5)
        for _ in range(num_keys):
            new_key = ET.SubElement(keys, "Key")
            while True:
                randomize_attributes(new_key, ["x_init", "y_init", "is_picked", "is_present", "color"], grid_size,
                                     walls_positions, agent_pos, dest_pos, used_colors)
                key_pos = (int(new_key.get("x_init")), int(new_key.get("y_init")))
                if key_pos != agent_pos and key_pos not in walls_positions:
                    occupied_positions.add(key_pos)
                    break

    # Preserve the Grid element without changes
    if grid is not None:
        grid_size_element = grid.find("Size").get("grid_Size")



    landmines = root.find("Landmines")

    if landmines is not None:
        for landmine in list(landmines):
            landmines.remove(landmine)

    if landmines is None:
        landmines = ET.SubElement(root, "Landmines")

    num_landmines = random.randint(1, (grid_size* grid_size)// 2)  # Define the number of landmines to add
    for _ in range(num_landmines):
            new_landmine = ET.SubElement(landmines, "Landmine")
            randomize_attributes(new_landmine, ["x", "y", "is_present"], grid_size, walls_positions, agent_pos, dest_pos)





    # Convert the mutated tree back to a string
    mutated_xml_string = ET.tostring(root, encoding="unicode")

    # Parse the mutated string again to reinsert the unchanged Grid element
    mutated_root = ET.fromstring(mutated_xml_string)
    if grid is not None:
        grid_element = mutated_root.find("Grid")
        size_element = grid_element.find("Size")
        size_element.set("grid_Size", grid_size_element)

    final_xml_string = ET.tostring(mutated_root, encoding="unicode")

    # Write the mutated XML content back to a new file
    mutated_file_path = os.path.splitext(xml_file_path)[0] + ".xml"
    with open(mutated_file_path, "w", encoding="utf-8") as f:
        f.write(final_xml_string)

    return final_xml_string

def mutate_environment(xml_file_path, env_name):
    match env_name:
        case EnvName.MINIGRID:
            return mutate_minigrid_environment(xml_file_path)
        case EnvName.FLAPPY_BIRD:
            # Add mutation logic for Flappy Bird environment
            pass
        case EnvName.CATCHER:
            # Add mutation logic for Catcher environment
            pass
        case EnvName.Four_Room:
            return mutate_four_room_environment(xml_file_path)

def use_exsisting_enviroment(xml_file_path, mutated_env_path):
    tree = ET.parse(mutated_env_path)
    root = tree.getroot()
    mutated_xml_string = ET.tostring(root, encoding="unicode")
    mutated_file_path = os.path.splitext(xml_file_path)[0] + ".xml"
    with open(mutated_file_path, "w", encoding="utf-8") as f:
        f.write(mutated_xml_string)

#mutate_four_room_environment("A:\Github repos\Answer\AIProbe\Four_Room\Config.xml")