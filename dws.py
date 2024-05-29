import xml.etree.ElementTree as ET
import random
import os

# Function to generate random attributes for elements
def randomize_attributes(element, attributes, grid_size):
    for attr in attributes:
        if attr in ["x", "y", "x_init", "y_init", "pick_x", "pick_y", "drop_x", "drop_y"]:
            element.set(attr, str(random.randint(1, grid_size - 1)))
        elif attr in ["is_picked", "is_present", "pickStatus", "dropStatus", "door_open", "door_locked"]:
            element.set(attr, str(random.choice([0, 1])))
        elif attr == "color":
            element.set(attr, random.choice(["red", "blue"]))
        elif attr == "theta":
            element.set(attr, random.choice(["n", "e", "s", "w"]))

def create_walls_based_on_doors(root, grid_size, agent_pos):
    doors = root.find("Doors")
    walls = root.find("Walls")

    if doors is not None and walls is not None:
        for door in doors.findall("Door"):
            door_x = int(door.get("x"))
            door_y = int(door.get("y"))

            # Randomly decide whether the wall will be horizontal or vertical
            if random.choice(["horizontal", "vertical"]) == "horizontal":
                # Create a random number of horizontal walls around the door
                num_walls = random.randint(1, 3)  # Random number of walls
                for x in range(max(1, door_x - num_walls), min(grid_size - 1, door_x + num_walls + 1)):
                    if (x, door_y) != agent_pos and x != door_x:  # Ensure not to place a wall on the door or agent's position
                        wall = ET.SubElement(walls, "Wall")
                        wall.set("x", str(x))
                        wall.set("y", str(door_y))
            else:
                # Create a random number of vertical walls around the door
                num_walls = random.randint(1, 3)  # Random number of walls
                for y in range(max(1, door_y - num_walls), min(grid_size - 1, door_y + num_walls + 1)):
                    if (door_x, y) != agent_pos and y != door_y:  # Ensure not to place a wall on the door or agent's position
                        wall = ET.SubElement(walls, "Wall")
                        wall.set("x", str(door_x))
                        wall.set("y", str(y))

def mutate_environment(xml_file_path):
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
            initial_position.set("x", str(random.randint(0, grid_size - 2)))
            initial_position.set("y", str(random.randint(0, grid_size - 2)))
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
        for key in keys.findall("Key"):
            randomize_attributes(key, ["x_init", "y_init", "is_picked", "is_present", "color"], grid_size)

    # Randomly add or remove doors
    doors = root.find("Doors")
    if doors is not None:
        # Remove some doors
        for door in list(doors):
            if random.choice([True, False]):
                doors.remove(door)

        # Add new doors
        for _ in range(random.randint(0, 3)):  # Add up to 3 new doors
            new_door = ET.SubElement(doors, "Door")
            randomize_attributes(new_door, ["x", "y", "door_open", "color", "door_locked"], grid_size)

    # Change positions and attributes of objects
    objects = root.find("Objects")
    if objects is not None:
        for obj in objects.findall("Object"):
            randomize_attributes(obj, ["pick_x", "pick_y", "pickStatus", "drop_x", "drop_y", "dropStatus", "is_present", "color"], grid_size)

    # Randomly add or remove lava tiles
    lava_tiles = root.find("LavaTiles")
    if lava_tiles is not None:
        # Remove some lava tiles
        for lava in list(lava_tiles):
            if random.choice([True, False]):
                lava_tiles.remove(lava)

        # Add new lava tiles
        for _ in range(random.randint(0, 5)):  # Add up to 5 new lava tiles
            new_lava = ET.SubElement(lava_tiles, "Lava")
            randomize_attributes(new_lava, ["x", "y", "is_present"], grid_size)

    # Randomly remove some walls
    walls = root.find("Walls")
    if walls is not None:
        for wall in list(walls):
            if random.choice([True, False]):
                walls.remove(wall)

    # Change positions of walls
    if walls is not None:
        for wall in walls.findall("Wall"):
            randomize_attributes(wall, ["x", "y"], grid_size)

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

    return mutated_file_path


# Example usage
xml_file_path = "Minigrid/Config.xml"
mutated_file_path = mutate_environment(xml_file_path)
print(f"Mutated XML file saved to: {mutated_file_path}")
