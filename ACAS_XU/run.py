import os
import pandas as pd
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from itertools import islice
from main import run_simulation


class Environment:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.agents = {}
        self.objects = {}
        self.attributes = {}
        self.load_environment()

    def load_environment(self):
        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        for attr in root.findall("Attribute"):
            name = attr.find("Name").get("value")
            value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
            self.attributes[name] = value

        for agent in root.findall(".//Agent"):
            agent_id = agent.get("id")
            agent_data = {"id": agent_id}

            for attr in agent.findall("Attribute"):
                name = attr.find("Name").get("value")
                value = float(attr.find("Value").get("value")) if attr.find("DataType").get("value") == "float" else int(attr.find("Value").get("value"))
                agent_data[name] = value

            self.agents[agent_id] = agent_data

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
        return self.agents.get(agent_id, None)

    def get_object(self, obj_id):
        return self.objects.get(obj_id, None)

    def get_environment_attributes(self):
        return self.attributes


def find_xml_files(base_folder):
    for root, dirs, files in os.walk(base_folder):
        if "finalState.xml" in files:
            xml_file_path = os.path.join(root, "finalState.xml")
            parts = root.split(os.sep)
            env_folder = next((p for p in parts if p.startswith("Env_")), "Unknown_Env")
            task_folder = next((p for p in parts if p.startswith("Task_")), "Unknown_Task")
            seed_number = next((p.split("_")[-1] for p in parts if p.startswith("Result_ACAS_Xu") and p.split("_")[-1].isdigit()), "Unknown")
            bin_number = next((p.replace("bin", "") for p in parts if "bin" in p), "Unknown")
            yield xml_file_path, env_folder, task_folder, seed_number, bin_number


def process_simulation(task, crash_counter):
    xml_file_path, env_folder, task_folder, seed_number, bin_number = task
    env_data = Environment(xml_file_path)
    ownship = env_data.get_agent("1")
    intruder = env_data.get_object("2")
    global_attrs = env_data.get_environment_attributes()

    if ownship is None or intruder is None or "Timestep_Count" not in global_attrs:
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

    if is_terminate:
        crash_counter["count"] += 1

    return {
        "Seed Number": seed_number,
        "Bin Number": bin_number,
        "Environment": env_folder,
        "Task": task_folder,
        "Terminated": is_terminate,
        "Execution Time (s)": execution_time,
    }


def batch_iterator(iterable, batch_size):
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch


def process_wrapper(args):
    """Unpacks the arguments and calls process_simulation."""
    return process_simulation(*args)

def run_simulations_in_batches(base_folder, output_csv="simulation_results_parallel.csv", num_workers=4, batch_size=10):
    """
    Runs simulations in batches to optimize memory usage.
    """
    with Manager() as manager:
        crash_counter = manager.dict({"count": 0})  # Shared counter

        xml_files = find_xml_files(base_folder)

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            for batch in batch_iterator(xml_files, batch_size):  # Process in batches
                tasks = [(task, crash_counter) for task in batch]

                # Use process_wrapper instead of lambda
                results = list(executor.map(process_wrapper, tasks))

                results = [r for r in results if r is not None]

                df = pd.DataFrame(results)

                # Append results in batches to avoid memory overload
                df.to_csv(output_csv, mode='a', index=False, header=not os.path.exists(output_csv))

                print(f"Processed batch of {len(results)} simulations.")

        print(f"Final Total Crashes: {crash_counter['count']}")

if __name__ == "__main__":
    parent_directory = "/scratch/projects/AIProbe/csharp/new/csharp/results/NEW/tes5t"
    num_workers = os.cpu_count()
    batch_size = 10
    run_simulations_in_batches(parent_directory, num_workers=num_workers, batch_size=batch_size)
