import random
import xml.etree.ElementTree as ET
import os

# Define the global colors list
colors = ["red", "blue", "green", "yellow", "grey"]


def parse_environment(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    agent = root.find("Agent")
    agent_pos = (int(agent.find("InitialPosition").get("x")), int(agent.find("InitialPosition").get("y")))
    destination_pos = (int(agent.find("DestinationPosition").get("x")), int(agent.find("DestinationPosition").get("y")))

    keys = root.find("Keys").findall("Key") if root.find("Keys") is not None else []
    key_positions = [(int(key.get("x_init")), int(key.get("y_init")), key.get("color")) for key in keys]

    objects = root.find("Objects").findall("Object") if root.find("Objects") is not None else []
    object_positions = [(int(obj.get("pick_x")), int(obj.get("pick_y")), obj.get("color")) for obj in objects]

    return {
        "agent_pos": agent_pos,
        "destination_pos": destination_pos,
        "key_positions": key_positions,
        "object_positions": object_positions
    }


def generate_random_task(task_type, grid_size, env_elements):
    x_source, y_source = env_elements["agent_pos"]
    task = {"type": task_type, "source": (x_source, y_source)}

    if task_type == "navigate":
        task["destination"] = (random.randint(1, grid_size - 2), random.randint(1, grid_size - 2))
        task["description"] = "Navigate from source to destination avoiding obstacles"
    elif task_type == "pickup" and env_elements["key_positions"]:
        key_pos = random.choice(env_elements["key_positions"])
        task["object"] = "key"
        task["color"] = key_pos[2]
        task["source"] = key_pos[:2]
        task["description"] = f"Pick up the {task['color']} key at {task['source']}"
    elif task_type == "drop" and env_elements["key_positions"]:
        key_pos = random.choice(env_elements["key_positions"])
        task["object"] = "key"
        task["color"] = key_pos[2]
        task["source"] = key_pos[:2]
        task["destination"] = (random.randint(1, grid_size - 2), random.randint(1, grid_size - 2))
        task["description"] = f"Drop the {task['color']} key at the destination {task['destination']}"
    elif task_type == "move" and env_elements["object_positions"]:
        obj_pos = random.choice(env_elements["object_positions"])
        task["object"] = "ball"
        task["color"] = random.choice(colors)
        task["source"] = obj_pos[:2]
        task["destination"] = (random.randint(1, grid_size - 2), random.randint(1, grid_size - 2))
        task["description"] = f"Move the {task['color']} box from {task['source']} to {task['destination']}"
    else:
        task["type"] = "navigate"
        task["destination"] = (random.randint(1, grid_size - 2), random.randint(1, grid_size - 2))
        task["description"] = "Navigate from source to destination avoiding obstacles"

    return task


def create_task_xml(task, output_file):
    output_file = os.path.join(output_file, 'task.xml')
    tasks_root = ET.Element("Tasks")
    task_element = ET.SubElement(tasks_root, "Task")

    for key, value in task.items():
        if isinstance(value, tuple):
            value = f"{value[0]},{value[1]}"
        ET.SubElement(task_element, key).text = str(value)

    tree = ET.ElementTree(tasks_root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)


def GenrateTask(xml_file_path, result_path):
    env_elements = parse_environment(xml_file_path)
    task_types = ["navigate", "pickup", "drop",'move']
    #task_types = ['move']
    task_type = random.choice(task_types)
    task = generate_random_task(task_type,7, env_elements)

    if not os.path.exists(result_path):
        os.makedirs(result_path)
    create_task_xml(task, result_path)


def generate_green_key_pickup_task(grid_size, env_elements):
    task_type = "pickup"
    green_key_positions = [pos for pos in env_elements["key_positions"] if pos[2] == "green"]

    if green_key_positions:
        key_pos = random.choice(green_key_positions)
    else:
        key_pos = (random.randint(1, grid_size - 2), random.randint(1, grid_size - 2), "green")

    destination = env_elements["destination_pos"]

    task = {
        "type": task_type,
        "object": "key",
        "color": "green",
        "source": key_pos[:2],
        "destination": destination,
        "description": f"Pick up the green key at {key_pos[:2]} and navigate to {destination}"
    }

    return task


def PickupTask(xml_file_path, result_path):
    env_elements = parse_environment(xml_file_path)
    task = generate_green_key_pickup_task(11,env_elements)
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    create_task_xml(task, result_path)



#if __name__ == '__main__':
    #env_elements = parse_environment("A:\Github repos\Answer\AIProbe\Minigrid\Config.xml")

    #task_types = ["navigate", "pickup", "drop", "move"]
    #task_count = 1

    #for task_type in task_types:
        #task = generate_random_task(task_type, 7, env_elements)
        #print(f"Task {task_count}:")
        #for key, value in task.items():
            #print(f"{key}: {value}")
        #task_count += 1
        #print("\n")
