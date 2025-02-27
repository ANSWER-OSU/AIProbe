import os
import pandas as pd
import time
import xml.etree.ElementTree as ET
import json


class Environment:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.agents = {}
        self.objects = {}
        self.attributes = {}

        # Load and parse the XML
        self.load_environment()

    def load_environment(self):
        """Loads and parses the XML environment file."""
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()

            # Parse Environment Attributes (like Timestep_Count)
            for attr in root.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(
                    attr.find("Value").get("value"))
                self.attributes[name] = value

            # Parse Agents
            for agent in root.findall(".//Agent"):
                agent_id = agent.get("id")
                agent_data = {"id": agent_id}

                for attr in agent.findall("Attribute"):
                    name = attr.find("Name").get("value")
                    value = float(attr.find("Value").get("value")) if attr.find("DataType").get(
                        "value") == "float" else int(attr.find("Value").get("value"))
                    agent_data[name] = value

                self.agents[agent_id] = agent_data

            # Parse Objects
            for obj in root.findall(".//Object"):
                obj_id = obj.get("id")
                obj_type = obj.get("type")
                obj_data = {"id": obj_id, "type": obj_type}

                for attr in obj.findall("Attribute"):
                    name = attr.find("Name").get("value")
                    value = float(attr.find("Value").get("value")) if attr.find("DataType").get(
                        "value") == "float" else int(attr.find("Value").get("value"))
                    obj_data[name] = value

                self.objects[obj_id] = obj_data

        except ET.ParseError as e:
            print(f"Error parsing XML file {self.xml_path}: {e}")
        except FileNotFoundError:
            print(f"XML file not found: {self.xml_path}")
        except Exception as e:
            print(f"Unexpected error while loading environment: {e}")

    def get_agent(self, agent_id):
        """Retrieve a specific agent's attributes."""
        return self.agents.get(agent_id)

    def get_object(self, obj_id):
        """Retrieve a specific object's attributes."""
        return self.objects.get(obj_id)

    def get_environment_attributes(self):
        """Retrieve environment-level attributes."""
        return self.attributes

    def to_json(self):
        """
        Converts the environment into a JSON string for hashing and comparison.
        """
        env_dict = {
            "attributes": self.attributes,
            "agents": self.agents,
            "objects": self.objects
        }
        return json.dumps(env_dict, sort_keys=True)

    def hash_environment(self):
        """
        Generates a hash value for the environment using its JSON representation.
        """
        return hash(self.to_json())


def find_xml_files(base_folder):
    """
    Recursively find all 'finalState.xml' files inside nested subdirectories.
    Returns a list of (xml_file_path, env_folder, task_folder).
    """
    xml_files = []

    for root, _, files in os.walk(base_folder):
        if "finalState.xml" in files:
            xml_file_path = os.path.join(root, "finalState.xml")
            parts = root.split(os.sep)
            env_folder = parts[-2] if len(parts) > 1 else "Unknown_Env"
            task_folder = parts[-1] if len(parts) > 0 else "Unknown_Task"
            xml_files.append((xml_file_path, env_folder, task_folder))

    return xml_files


def dfs_search(initial_state, final_state):
    """
    Perform Depth-First Search to find a path from the initial environment to the final state.
    """
    stack = [(initial_state, [])]  # Stack holds (current_state, path_taken)
    visited = set()

    final_hash = final_state.hash_environment()

    while stack:
        current_state, path = stack.pop()

        # Generate hash for the current state using JSON serialization
        current_hash = current_state.hash_environment()

        if current_hash in visited:
            continue

        visited.add(current_hash)

        # Check if current state matches the final state
        if current_hash == final_hash:
            print(f"Found path: {' -> '.join(path)}")
            return path

        # Explore possible actions (for demonstration, dummy actions are used)
        for action in ["action1", "action2", "action3"]:
            new_state = Environment(current_state.xml_path)  # Simulate environment change
            new_state.attributes["last_action"] = action  # Example mutation

            stack.append((new_state, path + [action]))

    print("No path found.")
    return []


def dfs_search(initial_state, final_state, gif_folder):
    """
    Perform Depth-First Search to find a path from the initial environment to the final state.
    """
    stack = [(initial_state, [])]  # Stack holds (current_state, path_taken)
    visited = set()

    final_hash = final_state.hash_environment()

    while stack:
        current_state, path = stack.pop()

        # Generate hash for the current state using JSON serialization
        current_hash = current_state.hash_environment()

        if current_hash in visited:
            continue

        visited.add(current_hash)

        # Check if current state matches the final state
        if current_hash == final_hash:
            print(f"Found path: {' -> '.join(path)}")
            return path

        # Simulate the environment for the current state
        terminate, is_invalid_state = run_simulation_from_environment(current_state, gif_folder)

        if terminate:
            print(f"Termination reached at path: {' -> '.join(path)}")
            continue  # Skip invalid paths

        # Explore possible actions
        for action in ["increase_speed", "decrease_speed", "turn_left", "turn_right", "hold_position"]:
            # Apply the action to modify the current environment
            new_state = apply_action_to_environment(current_state, action)

            # Simulate the environment after applying the action
            terminate, is_invalid_state = run_simulation_from_environment(new_state, gif_folder)

            if not is_invalid_state:
                stack.append((new_state, path + [action]))

    print("No path found.")
    return []






if __name__ == "__main__":
    parent_directory = "/scratch/projects/AIProbe/csharp/new/csharp/results/NEW/534"
    num_workers = os.cpu_count()
    log_file = "instruction_generation_log.txt"

    print(f"Using {num_workers} workers.")

    # Load initial and final environment XMLs
    initial_environment = Environment("/Users/rahil/Downloads/Task_492/initialState.xml")
    final_environment = Environment("/Users/rahil/Downloads/Task_492/finalState.xml")

    # Perform DFS search
    path = dfs_search(initial_environment, final_environment)

    if path:
        print(f"DFS Path Found: {' -> '.join(path)}")
    else:
        print("No path found.")