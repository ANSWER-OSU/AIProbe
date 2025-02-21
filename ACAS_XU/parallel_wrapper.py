import os
import pandas as pd
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor

from main import run_simulation 


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
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # Parse Environment Attributes (like Timestep_Count)
        for attr in root.findall("Attribute"):
            name = attr.find("Name").get("value")
            value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
            self.attributes[name] = value

        # Parse Agents
        for agent in root.findall(".//Agent"):
            agent_id = agent.get("id")
            agent_data = {"id": agent_id}

            for attr in agent.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                agent_data[name] = value

            self.agents[agent_id] = agent_data

        # Parse Objects
        for obj in root.findall(".//Object"):
            obj_id = obj.get("id")
            obj_type = obj.get("type")
            obj_data = {"id": obj_id, "type": obj_type}

            for attr in obj.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                obj_data[name] = value

            self.objects[obj_id] = obj_data

    def get_agent(self, agent_id):
        """Retrieve a specific agent's attributes."""
        return self.agents.get(agent_id, None)

    def get_object(self, obj_id):
        """Retrieve a specific object's attributes."""
        return self.objects.get(obj_id, None)

    def get_environment_attributes(self):
        """Retrieve environment-level attributes."""
        return self.attributes



def find_xml_files(base_folder):
    """
    Recursively find all 'finalState.xml' files inside nested subdirectories.
    Returns a list of (xml_file_path, env_folder, task_folder, seed_number, bin_number).
    """
    xml_files = []

    for root, dirs, files in os.walk(base_folder):  # Walk through all directories
        if "finalState.xml" in files:
            xml_file_path = os.path.join(root, "finalState.xml")

            # Extract folder names dynamically
            parts = root.split(os.sep)

            # Extract environment and task folder names correctly
            env_folder = "Unknown_Env"
            task_folder = "Unknown_Task"

            # Locate "Env_X" and "Task_Y" dynamically
            for part in parts:
                if part.startswith("Env_"):
                    env_folder = part
                if part.startswith("Task_"):
                    task_folder = part

            # Extract seed number and bin number
            seed_number = "Unknown"
            bin_number = "Unknown"

            for part in parts:
                cleaned_part = part.replace(" ", "")  # Remove extra spaces
                if cleaned_part.startswith("Result_ACAS_Xu"):
                    seed_parts = cleaned_part.split("_")

                    # Extract the last numeric value as seed number
                    if seed_parts[-1].isdigit():
                        seed_number = seed_parts[-1]

                    # Extract bin number and format it (removing 'bin')
                    for segment in seed_parts:
                        if "bin" in segment:
                            bin_number = segment.replace("bin", "")  # Convert '10bin' -> '10'

            xml_files.append((xml_file_path, env_folder, task_folder, seed_number, bin_number))

    return xml_files

def process_simulation(xml_file_path, env_folder, task_folder, seed_number, bin_number):
    """Process a single simulation in a parallel process."""
    env_data = Environment(xml_file_path)

    # Extract initial conditions
    ownship = env_data.get_agent("1")
    intruder = env_data.get_object("2")
    global_attrs = env_data.get_environment_attributes()

    if ownship is None or intruder is None or "Timestep_Count" not in global_attrs:
        print(f"⚠️ Skipping {xml_file_path} (missing data)")
        return None

    start_time = time.time()

    is_terminate = run_simulation(
        ownship_speed=ownship.get("Ownship_Speed", 300),
        ownship_x=ownship.get("X", 0),
        ownship_y=ownship.get("Y", 0),
        ownship_theta=ownship.get("Theta", 0),
        intruder_speed=intruder.get("Intruder_Speed", 200),
        intruder_x=intruder.get("X", 500),
        intruder_y=intruder.get("Y", 500),
        intruder_theta=intruder.get("Auto_Theta", 0.7854),
        timestep_count=int(global_attrs.get("Timestep_Count", 1000)),
        gif_folder=os.path.dirname(xml_file_path)
    )

    execution_time = round(time.time() - start_time, 2)

    return {
        "Seed Number": seed_number,
        "Bin Number": bin_number,
        "Environment": env_folder,
        "Task": task_folder,
        "Terminated": is_terminate,
        "Execution Time (s)": execution_time
    }


def process_wrapper(task):
    """Helper function to allow process_simulation to run in parallel."""
    return process_simulation(*task)


def initialize_and_run_simulations_parallel(base_folder, output_csv="simulation_results_parallel.csv", num_workers=4):
    """
    Recursively finds 'finalState.xml' in all subdirectories and runs simulations in parallel.
    """
    results = []
    tasks = find_xml_files(base_folder)  

    print(f"🔍 Found {len(tasks)} simulation files in {base_folder}")

    # Run simulations in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_wrapper, tasks))  

    results = [r for r in results if r is not None]

    df = pd.DataFrame(results)
    csv_path = os.path.join(base_folder, output_csv)
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Results saved to {csv_path}")


# Example Usage:
if __name__ == "__main__":
    parent_directory = "/scratch/projects/AIProbe/csharp/news/csharp/results"

    # Use all available CPU cores
    num_workers = os.cpu_count()

    print(num_workers)

    # Run parallel simulations
    initialize_and_run_simulations_parallel(parent_directory, num_workers=num_workers)