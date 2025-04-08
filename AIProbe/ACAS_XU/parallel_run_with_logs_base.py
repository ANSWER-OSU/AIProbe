import os
import pandas as pd
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
from main_base import run_simulation
import csv
import re
import sys

def parse_value(value_str, dtype):
    if value_str.lower() == "unknown":
        return None
    try:
        return float(value_str) if dtype == "float" else int(value_str)
    except ValueError:
        return None

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
            dtype = attr.find("DataType").get("value")
            value_str = attr.find("Value").get("value")
            value = parse_value(value_str, dtype)
            self.attributes[name] = value

        for agent in root.findall(".//Agent"):
            agent_id = agent.get("id")
            agent_data = {"id": agent_id}
            for attr in agent.findall("Attribute"):
                name = attr.find("Name").get("value")
                dtype = attr.find("DataType").get("value")
                value_str = attr.find("Value").get("value")
                value = parse_value(value_str, dtype)
                agent_data[name] = value
            self.agents[agent_id] = agent_data

        for obj in root.findall(".//Object"):
            obj_id = obj.get("id")
            obj_type = obj.get("type")
            obj_data = {"id": obj_id, "type": obj_type}
            for attr in obj.findall("Attribute"):
                name = attr.find("Name").get("value")
                dtype = attr.find("DataType").get("value")
                value_str = attr.find("Value").get("value")
                value = parse_value(value_str, dtype)
                obj_data[name] = value
            self.objects[obj_id] = obj_data
    
    def get_agent(self, agent_id):
        return self.agents.get(agent_id, None)
    
    def get_object(self, obj_id):
        return self.objects.get(obj_id, None)
    
    def get_environment_attributes(self):
        return self.attributes

def find_seeds(base_path):
    return [os.path.join(base_path, seed) for seed in os.listdir(base_path) if seed.isdigit()]

def find_xml_files(base_folder):
    xml_files = []
    for root_dir, _, files in os.walk(base_folder):
        if "finalState.xml" in files:
            xml_file_path = os.path.join(root_dir, "finalState.xml")
            parts = root_dir.split(os.sep)
            env_folder, task_folder, seed_number, bin_number = "Unknown_Env", "Unknown_Task", "Unknown", "Unknown"
            for part in parts:
                if part.startswith("Env_"):
                    env_folder = part
                if part.startswith("Task_"):
                    task_folder = part
                if part.isdigit():
                    seed_number = part
                if "bin" in part:
                    bin_number = part.replace("bin", "")
            xml_files.append((xml_file_path, env_folder, task_folder, seed_number, bin_number))
    return xml_files

def process_simulation(xml_file_path, env_folder, task_folder, seed_number, bin_number, crash_counter, model_version):
    env_data = Environment(xml_file_path)
    ownship = env_data.get_agent("1")
    intruder = env_data.get_object("1")
    global_attrs = env_data.get_environment_attributes()

    if ownship is None or intruder is None or "Timestep_Count" not in global_attrs:
        print(f"⚠️ Skipping {xml_file_path} (missing critical data)")
        return None

    # Skip if essential attributes are missing
    if any(v is None for v in [
        ownship.get("Ownship_Speed"), ownship.get("X"), ownship.get("Y"), ownship.get("Theta"),
        intruder.get("Intruder_Speed"), intruder.get("X"), intruder.get("Y"), intruder.get("Auto_Theta"),
        global_attrs.get("Timestep_Count")
    ]):
        print(f"⚠️ Skipping {xml_file_path} (missing attribute values)")
        return None

    start_time = time.time()
    is_terminate, is_invalid_state = run_simulation(
        ownship_speed=ownship.get("Ownship_Speed"),
        ownship_x=ownship.get("X"),
        ownship_y=ownship.get("Y"),
        ownship_theta=ownship.get("Theta"),
        intruder_speed=intruder.get("Intruder_Speed"),
        intruder_x=intruder.get("X"),
        intruder_y=intruder.get("Y"),
        intruder_theta=intruder.get("Auto_Theta"),
        timestep_count=int(global_attrs.get("Timestep_Count")),
        gif_folder=os.path.dirname(xml_file_path),
        model=model_version
    )
    execution_time = round(time.time() - start_time, 2)

    if is_terminate:
        if seed_number not in crash_counter:
            crash_counter[seed_number] = 0
        crash_counter[seed_number] += 1
        print(f"💥 Crash detected in Seed {seed_number}! Total for this seed: {crash_counter[seed_number]}")

    return {
        "Seed Number": seed_number,
        "Bin Number": bin_number,
        "Environment": env_folder,
        "Task": task_folder,
        "Terminated": is_terminate,
        "Invalid Initial State": is_invalid_state,
        "Execution Time (s)": execution_time,
        "File Path": xml_file_path
    }

def process_wrapper(task_crash_counter_model):
    task, crash_counter, model_version = task_crash_counter_model
    return process_simulation(*task, crash_counter, model_version)

def initialize_and_run_simulations_parallel(base_folder, log, output_csv, num_workers=4, model_version=1):
    with Manager() as manager:
        crash_counter = manager.dict()
        seed_folders = find_seeds(base_folder)
        all_tasks = []

        for seed_folder in seed_folders:
            tasks = find_xml_files(seed_folder)
            print(f"🔍 Found {len(tasks)} simulation files in Seed {os.path.basename(seed_folder)}")
            log.write(f"🔍 Found {len(tasks)} simulation files in Seed {os.path.basename(seed_folder)}\n")
            log.flush()
            all_tasks.extend(tasks)

        task_data = [(task, crash_counter, model_version) for task in all_tasks]

        # Prepare CSV file: open once to write header
        csv_file_path = os.path.join(base_folder, output_csv)
        fieldnames = ["Seed Number", "Bin Number", "Environment", "Task", "Terminated",
                      "Invalid Initial State", "Execution Time (s)", "File Path"]
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        # Execute tasks in parallel and write results to CSV as they complete
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(process_wrapper, t): t for t in task_data}
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    # Append each result as it is ready
                    with open(csv_file_path, 'a', newline='') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerow(result)

        print(f"\n✅ Results saved to {csv_file_path}")
        log.write(f"\n✅ Results saved to {csv_file_path}\n")
        log.flush()

        print("\n💥 Final Total Crashes Per Seed:")
        total_crashes = 0
        for seed, count in crash_counter.items():
            print(f"Seed {seed}: {count} crashes")
            log.write(f"Seed {seed}: {count} crashes\n")
            total_crashes += count

        print(f"🔥 Total Crashes Across All Seeds: {total_crashes}")
        log.write(f"🔥 Total Crashes Across All Seeds: {total_crashes}\n")
        log.flush()

def update_read_onnx_versions(script_path, new_version=2):
    """
    Replaces all occurrences of read_onnx(n, x) with read_onnx(n, new_version)
    where n and x are any integers. Only the second argument (version) is updated.
    """
    with open(script_path, "r") as file:
        content = file.read()

    pattern = r'read_onnx\(\s*(\d+)\s*,\s*\d+\s*\)'
    replacement = lambda m: f'read_onnx({m.group(1)}, {new_version})'
    updated_content = re.sub(pattern, replacement, content)

    with open(script_path, "w") as file:
        file.write(updated_content)

    print(f"✅ Updated all read_onnx(n, x) to read_onnx(n, {new_version})")

class LoggerWrapper:
    def __init__(self, log_file_obj):
        self.log_file_obj = log_file_obj
        self.stdout = sys.stdout  

    def write(self, message):
        self.log_file_obj.write(message)
        self.stdout.write(message)

    def flush(self):
        self.log_file_obj.flush()
        self.stdout.flush()

if __name__ == "__main__":
    parent_directory = "/scratch/projects/AIProbe-Main/Result/ACAS_XU_Domain/Result/10_bin_new"
    model_script_path = "/scratch/projects/AIProbe-Main/AIProbe/ACAS_XU/environment.py"
    num_workers = 100


    for model_version in range(1, 10):  # 1 to 9 inclusive
        log_file_path = os.path.join(parent_directory, f"model_{model_version}_simulation_log.txt")
        with open(log_file_path, "w") as log_file:
            sys.stdout = sys.stderr = LoggerWrapper(log_file)
            print(f"\n🚀 Running simulations for model version: {model_version}")
            update_read_onnx_versions(model_script_path, new_version=model_version)

            output_csv = f"model_{model_version}_simulation_results_parallel.csv"
            print(output_csv)

            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"Simulation started at: {start_time}\n")

            initialize_and_run_simulations_parallel(
                    base_folder=parent_directory,
                    log=log_file,
                    output_csv=output_csv,
                    num_workers=num_workers,
                    model_version=model_version
            )

            end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"\nSimulation ended at: {end_time}\n")

            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__