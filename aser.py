import random
import xml.etree.ElementTree as ET
import os

def parse_environment(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    agent = root.find("Agent")
    agent_pos = (int(agent.find("InitialPosition").get("x")), int(agent.find("InitialPosition").get("y")))
    destination_pos = (int(agent.find("DestinationPosition").get("x")), int(agent.find("DestinationPosition").get("y")))

    keys = root.find("Keys").findall("Key") if root.find("Keys") is not None else []
    key_positions = [(int(key.get("x_init")), int(key.get("y_init"))) for key in keys]

    objects = root.find("Objects").findall("Object") if root.find("Objects") is not None else []
    object_positions = [(int(obj.get("pick_x")), int(obj.get("pick_y"))) for obj in objects]

    return {
        "agent_pos": agent_pos,
        "destination_pos": destination_pos,
        "key_positions": key_positions,
        "object_positions": object_positions
    }


def generate_random_task(grid_size, env_elements):
    task_type = random.choice(["navigate", "pickup", "drop", "move"])
    x_source, y_source = env_elements["agent_pos"]
    task = {"type": task_type, "source": (x_source, y_source)}

    if task_type == "navigate":
        x_dest, y_dest = env_elements["destination_pos"]
        task["destination"] = (x_dest, y_dest)
        task["description"] = "Navigate from source to destination avoiding obstacles"
    elif task_type == "pickup" and env_elements["key_positions"]:
        task["object"] = "key"
        task["color"] = random.choice(["red", "blue"])
        key_pos = random.choice(env_elements["key_positions"])
        task["key_position"] = key_pos
        task["description"] = f"Pick up the {task['color']} key at {key_pos}"
    elif task_type == "drop" and env_elements["key_positions"]:
        task["object"] = "key"
        task["color"] = random.choice(["red", "blue"])
        x_dest, y_dest = env_elements["destination_pos"]
        task["destination"] = (x_dest, y_dest)
        task["description"] = f"Drop the {task['color']} key at the destination {task['destination']}"
    elif task_type == "move" and env_elements["object_positions"]:
        obj_pos = random.choice(env_elements["object_positions"])
        task["object"] = "box"
        x_dest, y_dest = env_elements["destination_pos"]
        task["source"] = obj_pos
        task["destination"] = (x_dest, y_dest)
        task["description"] = f"Move the box from {obj_pos} to {task['destination']}"
    else:
        task["type"] = "navigate"
        x_dest, y_dest = env_elements["destination_pos"]
        task["destination"] = (x_dest, y_dest)
        task["description"] = "Navigate from source to destination avoiding obstacles"

    return task


def create_task_xml(task, output_file):
    tasks_root = ET.Element("Tasks")
    task_element = ET.SubElement(tasks_root, "Task")

    for key, value in task.items():
        if isinstance(value, tuple):
            value = f"{value[0]},{value[1]}"
        ET.SubElement(task_element, key).text = str(value)

    tree = ET.ElementTree(tasks_root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    xml_file_path = "path_to_your_environment.xml"
    env_elements = parse_environment(xml_file_path)

    for i in range(10):
        task = generate_random_task(7, env_elements)
        output_file = f"task_{i+1}.xml"
        create_task_xml(task, output_file)
        print(f"Task {i+1} has been saved to {output_file}")
