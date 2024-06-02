from enum import Enum
import xml.etree.ElementTree as ET
import random
import os

class EnvName(Enum):
    FLAPPY_BIRD = "flappy_bird"
    MINIGRID = "minigrid"
    CATCHER = "catcher"

# Generate random attributes for elements of minigrid env
def randomize_attributes(element, attributes, grid_size):
    for attr in attributes:
        if attr in ["x", "y", "x_init", "y_init", "pick_x", "pick_y", "drop_x", "drop_y"]:
            while True:
                value = random.randint(1, grid_size - 2)  # Exclude boundaries 0 and grid_size - 1
                if 1 <= value <= grid_size - 2:  # Ensure value is not on boundary
                    element.set(attr, str(value))
                    break
        elif attr in ["is_picked", "is_present", "door_open", "door_locked"]:
            element.set(attr, str(random.choice([0, 1])))
        elif attr in ["pickStatus", "dropStatus"]:
            element.set(attr, "0")  # Always set pickStatus and dropStatus to 0
        elif attr == "color":
            element.set(attr, random.choice(["red", "blue", "green", "purple", "yellow", "grey"]))
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
    mutated_file_path = os.path.splitext(xml_file_path)[0] + "_mutated.xml"
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
