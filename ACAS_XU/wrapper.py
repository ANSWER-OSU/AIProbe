import os
import pandas as pd
import time
import xml.etree.ElementTree as ET
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


def initialize_and_run_simulations(base_folder, output_csv="simulation_results.csv"):
    """
    Iterates through all 'Env_X/Task_Y/initialState.xml' files within the base_folder,
    runs simulations, and saves results in a CSV file.
    """
    results = []  # Store results for CSV
    total_terminate = 0

    for env_folder in sorted(os.listdir(base_folder)):
        env_path = os.path.join(base_folder, env_folder)
        
        # Ensure it's an environment directory
        if not os.path.isdir(env_path) or not env_folder.startswith("Env_"):
            continue  

        for task_folder in sorted(os.listdir(env_path)):
            task_path = os.path.join(env_path, task_folder)

            # Ensure it's a task directory
            if not os.path.isdir(task_path) or not task_folder.startswith("Task_"):
                continue  

            # Look for initialState.xml in the task directory
            xml_file_path = os.path.join(task_path, "finalState.xml")
            if os.path.exists(xml_file_path):
                #print(f"Processing: {xml_file_path}")

                # Load environment data
                env_data = Environment(xml_file_path)

                # Extract initial conditions
                ownship = env_data.get_agent("1")  # Ownship Aircraft
                intruder = env_data.get_object("2")  # Intruder Aircraft
                global_attrs = env_data.get_environment_attributes()  # Environment attributes

                # Check if data is valid
                if ownship is None:
                    print(f"⚠️ Warning: Ownship not found in {xml_file_path}")
                    continue
                if intruder is None:
                    print(f"⚠️ Warning: Intruder not found in {xml_file_path}")
                    continue
                if "Timestep_Count" not in global_attrs:
                    print(f"⚠️ Warning: Timestep_Count not found in {xml_file_path}")
                    continue

                # Start tracking time
                start_time = time.time()

                # Run simulation and capture termination status
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
                    gif_folder=task_path  # Store results in the task folder
                )

                end_time = time.time()
                execution_time = round(end_time - start_time, 2)

                #print(f"Execution Time: {execution_time} seconds")

                if is_terminate:
                    total_terminate += 1
                    print(f"Total Terminations: {total_terminate}")

                # Store result in list
                results.append({
                    "Environment": env_folder,
                    "Task": task_folder,
                    "Terminated": is_terminate,
                    "Execution Time (s)": execution_time
                })

    # Convert results to DataFrame and save as CSV
    df = pd.DataFrame(results)
    csv_path = os.path.join(base_folder, output_csv)
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Results saved to {csv_path}")


def run_on_all_acas_folders(parent_folder):
    """
    Finds all `Result_ACAS_Xu_*` folders inside the given parent folder
    and runs `initialize_and_run_simulations` for each.
    """
    for folder in sorted(os.listdir(parent_folder)):
        folder_path = os.path.join(parent_folder, folder)

        if os.path.isdir(folder_path) :
            if folder.startswith("Result_ACAS _Xu_"):
                print(f"\n🚀 Running simulation for: {folder_path}")
                initialize_and_run_simulations(folder_path)


# Example Usage:
if __name__ == "__main__":
    # Define the parent directory containing all `Result_ACAS_Xu_*` folders
    parent_directory = "/Users/rahil/Documents/GitHub/AIProbe/csharp/results/10_10"
    
    # Run simulations on all ACAS_Xu result folders
    run_on_all_acas_folders(parent_directory)