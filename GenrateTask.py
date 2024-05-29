import random
import xml.etree.ElementTree as ET


def generate_random_task(grid_size):
    task_type = random.choice(["navigate", "pickup", "drop"])
    x_source, y_source = random.randint(1, grid_size), random.randint(1, grid_size)
    task = {"type": task_type, "source": (x_source, y_source)}

    if task_type == "navigate":
        x_dest, y_dest = random.randint(1, grid_size), random.randint(1, grid_size)
        task["destination"] = (x_dest, y_dest)
        task["description"] = "Navigate from source to destination avoiding obstacles"
    elif task_type == "pickup":
        task["object"] = "key"
        task["color"] = random.choice(["red", "blue"])
        task["description"] = f"Pick up the {task['color']} key"
    elif task_type == "drop":
        task["object"] = "key"
        task["color"] = random.choice(["red", "blue"])
        x_dest, y_dest = random.randint(1, grid_size), random.randint(1, grid_size)
        task["destination"] = (x_dest, y_dest)
        task["description"] = f"Drop the {task['color']} key at the destination"

    return task


if __name__ == '__main__':
    for i in range(10):
        task = generate_random_task(7)
        print(f"Task {i+1}:")
        for key, value in task.items():
            print(f"  {key}: {value}")
        print()
