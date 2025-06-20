import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import pandas as pd
import xml.etree.ElementTree as ET
from multiprocessing import Pool, cpu_count
import csv 
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description="Minigrid LavaRoom Crash Analysis")
parser.add_argument("--csv_path", type=str, required=True, help="Path to the CSV result file")
parser.add_argument("--base_dir", type=str, required=True, help="Base directory of the XML simulation results")
args = parser.parse_args()

# === CONFIG ===
CSV_PATH    = args.csv_path
BASE_DB_DIR = args.base_dir
base_dir = args.base_dir
NUM_BINS    = 100
NUM_PROCS   = 2  # number of worker processes in the Pool


def parse_bins_from_xml(xml_path, num_bins=NUM_BINS):
    """
    Parse all <Attribute> elements in xml_path and return a tuple of bin indices.
    Returns None on parse failure.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        bins = []
        for attr in root.iter("Attribute"):
            val_elem        = attr.find("Value")
            constraint_elem = attr.find("Constraint")
            if val_elem is None or constraint_elem is None:
                continue
            try:
                val     = float(val_elem.attrib["value"])
                min_val = float(constraint_elem.attrib.get("Min", 0))
                max_val = float(constraint_elem.attrib.get("Max", min_val + 1))
                if max_val > min_val:
                    width     = (max_val - min_val) / num_bins
                    bin_index = int((val - min_val) / width)
                    bins.append(min(bin_index, num_bins - 1))
            except Exception:
                continue
        return tuple(bins)
    except Exception as e:
        print(f"[ERROR] Failed to parse XML {xml_path}: {e}")
        return None
    
def process_task(args):
    """
    Given (seed, env, task), locate the XMLs, parse bins, and return (seed, init_bins, final_bins)
    or None if any step fails.
    """
    seed, env, task = args
    task_dir   = os.path.join(BASE_DB_DIR, str(seed), f"Env_{env}", f"Task_{task}")
    init_path  = os.path.join(task_dir, "initialState.xml")
    final_path = os.path.join(task_dir, "finalState.xml")
    
    if not (os.path.exists(init_path) and os.path.exists(final_path)):
        return None
    
    init_bins  = parse_bins_from_xml(init_path)
    final_bins = parse_bins_from_xml(final_path)
    if init_bins is None or final_bins is None:
        return None
    
    return (seed, init_bins, final_bins)

if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    filtered = df[(df["#Lava"] == 1.0) & (df["#AgentToGoal"] == 0)]
    print(f"Loaded {len(filtered)} crash-task rows from CSV")
    
    tasks = []
    for _, row in filtered.iterrows():
        try:
            tasks.append((int(row["Seed"]), int(row["Env#"]), int(row["Task#"])))
        except Exception as e:
            print(f"[WARN] Skipping row due to parse error: {e}")
            
    print(f"Prepared {len(tasks)} tasks for processing")
    
    print(f"Spawning {NUM_PROCS} worker processes...")
    with Pool(processes=NUM_PROCS) as pool:
        results = pool.map(process_task, tasks)
        
    global_unique = set()
    per_seed_map  = {}  # seed -> {init_bins: final_bins}
    per_seed_total = {}  # seed -> total crash count
    
    for res in results:
        if res is None:
            continue
        seed, init_bins, final_bins = res
        per_seed_total[seed] = per_seed_total.get(seed, 0) + 1
        
        if init_bins not in global_unique:
            global_unique.add(init_bins)
            per_seed_map.setdefault(seed, {})[init_bins] = final_bins
            
    print(f"\nTotal global unique initial crash bins: {len(global_unique)}")
    print(f"Total seeds with at least one unique crash: {len(per_seed_map)}")
    
    total_crashes_sum = 0
    unique_crash_sum = 0
    num_seeds = len(per_seed_total)
    
    for seed in sorted(per_seed_total):
        total = per_seed_total[seed]
        unique = len(per_seed_map.get(seed, {}))
        total_crashes_sum += total
        unique_crash_sum += unique
        print(f"\nSeed {seed}: {unique} unique / {total} total crashes")
        
        avg_total = total_crashes_sum / num_seeds if num_seeds > 0 else 0
    avg_unique = unique_crash_sum / num_seeds if num_seeds > 0 else 0
    
    print(f"\nAverages across {num_seeds} seeds:")
    print(f"Average Total Crashes: {avg_total:.2f}")
    print(f"Average Unique Crash Bins: {avg_unique:.2f}")
    #   if unique > 0:
    #       init_example, final_example = next(iter(per_seed_map[seed].items()))
    #       print(f"Example → Initial: {init_example} -> Final: {final_example}")
    

def extract_key_from_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Grid size
        grid_size = None
        for attr in root.findall("Attribute"):
            name = attr.find("Name").attrib["value"]
            if name == "Grid":
                grid_size = int(attr.find("Value").attrib["value"])
                
        # Agent position
        agent_elem = root.find(".//Agent[@id='1']")
        agent_x = agent_y = None
        for attr in agent_elem.findall("Attribute"):
            name = attr.find("Name").attrib["value"]
            val = int(attr.find("Value").attrib["value"])
            if name == "X":
                agent_x = val
            elif name == "Y":
                agent_y = val
                
        # Lava positions
        lava_tiles = []
        for lava_obj in root.findall(".//Object[@type='Lava']"):
            lava_x = lava_y = None
            for attr in lava_obj.findall("Attribute"):
                name = attr.find("Name").attrib["value"]
                val = int(attr.find("Value").attrib["value"])
                if name == "X":
                    lava_x = val
                elif name == "Y":
                    lava_y = val
            lava_tiles.append((lava_x, lava_y))
            
        total_lava = len(lava_tiles)
        return (grid_size, agent_x, agent_y, total_lava, tuple(sorted(lava_tiles)))
    
    except Exception as e:
        return None
    
def process_seed(seed_path):
    seed = os.path.basename(seed_path)
    unique_keys = set()
    
    for env in os.listdir(seed_path):
        env_path = os.path.join(seed_path, env)
        if not os.path.isdir(env_path):
            continue
        
        for task in os.listdir(env_path):
            task_path = os.path.join(env_path, task)
            if not os.path.isdir(task_path):
                continue
            
            for xml_file in ["finalState.xml", "initialState.xml"]:
                xml_path = os.path.join(task_path, xml_file)
                if os.path.exists(xml_path):
                    key = extract_key_from_xml(xml_path)
                    if key:
                        unique_keys.add(key)
                    break  # One XML per task
                
    return seed, unique_keys

def geometric_sum(base, start_exp, end_exp):
    return sum(base**i for i in range(start_exp, end_exp + 1))
from decimal import Decimal, getcontext

def geometric_sum_e_format(base, start_exp, end_exp):
    getcontext().prec = 100  # Set high precision for large numbers
    total = Decimal(0)
    
    for i in range(start_exp, end_exp + 1):
        value = Decimal(base) ** i
        total += value
        sci_str = f"{value:.6e}"  # format in scientific notation
        
    print(f"\nTotal sum in scientific notation: {total:.6e}")
    return total


def main_parallel_coverage(base_dir):
    seed_paths = [
        os.path.join(base_dir, seed)
        for seed in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, seed))
    ]
    
    norm_divisor = geometric_sum_e_format(3, 9, 400)
    coverage_results = {}
    
    print(f"Processing {len(seed_paths)} seeds with 20 processes...\n")
    with ProcessPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_seed, path): path for path in seed_paths}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Progress"):
            seed, keys = future.result()
            raw = len(keys)
            #normalized = raw / norm_divisor
            from decimal import Decimal, getcontext
            
            getcontext().prec = 4  # set high precision
            
            
            large_value = Decimal("6.3553e+1192")
            normalized = (raw * 100) / large_value
            
            print(normalized)
            
            coverage_results[seed] = (raw, normalized)
            
    print("\nNormalized Unique State Coverage per Seed:\n")
    for seed in sorted(coverage_results):
        raw, normalized = coverage_results[seed]
        print(f"Seed {seed}: {raw} unique states → normalized = {normalized:.8e}")
        
    csv_path = "state_coverage_per_seed.csv"
    with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Seed", "Unique_States", "Normalized_Coverage"])
        
            for seed in sorted(coverage_results, key=lambda s: int(s)):
                raw, normalized = coverage_results[seed]
                writer.writerow([seed, raw, normalized])
                

    print(f"\nResults saved to {csv_path}")
    normalized_values = [normalized for (_, normalized) in coverage_results.values()]
    average_normalized = sum(normalized_values) / len(normalized_values) if normalized_values else 0
    
    print(f"\nAverage normalized coverage across {len(normalized_values)} seeds: {average_normalized:.8e}")
    
    
def analyze_gpt_all_configs_as_one_seed(gpt_base_dir):
    import glob
    
    norm_divisor = geometric_sum(3, 3, 50)
    unique_keys = set()
    
    config_paths = sorted([
        os.path.join(gpt_base_dir, config)
        for config in os.listdir(gpt_base_dir)
        if os.path.isdir(os.path.join(gpt_base_dir, config))
    ])

    print(f"Scanning all {len(config_paths)} GPT Configs as one seed (initialState.xml only)...\n")
    
    for config_path in tqdm(config_paths, desc="Scanning XMLs"):
        # Only include initialState.xml files
        xml_files = glob.glob(os.path.join(config_path, "initialState.xml"))
        for xml_path in xml_files:
            key = extract_key_from_xml(xml_path)
            if key:
                unique_keys.add(key)
                
    # Compute results
    raw = len(unique_keys)
    from decimal import Decimal, getcontext
    
    getcontext().prec = 4  # set high precision
    
    large_value = Decimal("6.3553e+1192")
    normalized = (raw * 100) / large_value
    
    print(normalized)
    summary.append((os.path.basename(csv_path), raw, normalized))
    
    
    print("\nTotal Unique State Coverage (ALL GPT Configs as one seed):")
    print(f"Unique States: {raw}")
    print(f"Normalized Coverage: {normalized:.8e}")
    
    csv_path = "gpt_all_configs_as_one_seed.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Seed", "Unique_States", "Normalized_Coverage"])
        writer.writerow(["GPT_ALL_CONFIGS", raw, normalized])
        
    normalized_values = [row[2] for row in summary]
    
    from decimal import Decimal, getcontext
    getcontext().prec = 4
    
    def compute_stats(values):
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            stddev = variance.sqrt()
            return mean, stddev
    
    avg, std_dev = compute_stats(normalized_values)
    print(f"\nAverage Normalized Coverage: {avg:.3e}")
    print(f"Standard Deviation: {std_dev:.3e}")
    
    print(f"\nSummary saved to: {output_path}")
    
    print(f"\nSaved to {csv_path}")
    
    
def parse_initial_xml(xml_path):
    """Parse the XML file to extract grid size, agent/goal positions, and lava tiles."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        def find_attr(name):
            elem = root.find(f".//Attribute[Name='{name}']/Value")
            return int(elem.attrib["value"]) if elem is not None and "value" in elem.attrib else None
        
        grid_size = find_attr("Grid_Size")
        agent_x = find_attr("Agent_X")
        agent_y = find_attr("Agent_Y")
        goal_x = find_attr("Goal_X")
        goal_y = find_attr("Goal_Y")
        
        # If any of the required fields are missing, skip this file
        if None in (grid_size, agent_x, agent_y, goal_x, goal_y):
            print(f"Missing required fields in {xml_path}. Skipping.")
            return None, None
        
        # Parse lava tiles (optional)
        lava_coords = []
        for attr in root.findall(".//Attribute[Name='Lava_Tile']"):
            val_elem = attr.find("Value")
            if val_elem is None or "value" not in val_elem.attrib:
                continue
            val_str = val_elem.attrib["value"]
            coords = list(map(int, val_str.strip("()").split(",")))
            lava_coords.append(tuple(coords))
            
        total_lava = len(lava_coords)
        return grid_size, (agent_x, agent_y, goal_x, goal_y, total_lava, tuple(sorted(lava_coords)))
    
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None, None
    
def analyze_from_custom_csv(csv_path):
    norm_divisor = geometric_sum(3, 3, 50)
    unique_keys = set()
    
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            
            grid_size = int(row[0])
            agent_x = int(row[1])
            agent_y = int(row[2])
            goal_x = int(row[3])
            goal_y = int(row[4])
            
            # Parse lava tiles
            lava_coords = list(map(int, row[5:]))
            lava_tiles = list(zip(lava_coords[::2], lava_coords[1::2]))
            total_lava = len(lava_tiles)
            
            key = (agent_x, agent_y, goal_x, goal_y, total_lava, tuple(sorted(lava_tiles)))
            unique_keys.add(key)
            
    raw = len(unique_keys)
    #normalized = raw / norm_divisor
    from decimal import Decimal, getcontext
    
    getcontext().prec = 4  # set high precision
    
    large_value = Decimal("6.3553e+1192")
    normalized = (raw * 100) / large_value
    
    print(normalized)
    summary.append((os.path.basename(csv_path), raw, normalized))
    
    print("\nCustom CSV State Coverage:")
    print(f"Unique States: {raw}")
    print(f"Normalized Coverage: {normalized:.8e}")
    
    csv_out = "custom_csv_state_coverage.csv"
    with open(csv_out, "w", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["Source", "Unique_States", "Normalized_Coverage"])
        writer.writerow(["custom_csv", raw, normalized])
        
    normalized_values = [row[2] for row in summary]
    
    from decimal import Decimal, getcontext
    getcontext().prec = 4
    
    def compute_stats(values):
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            stddev = variance.sqrt()
            return mean, stddev
    
    avg, std_dev = compute_stats(normalized_values)
    print(f"\nAverage Normalized Coverage: {avg:.3e}")
    print(f"Standard Deviation: {std_dev:.3e}")
    
    print(f"\nSummary saved to: {output_path}")
    print(f"\nResults saved to {csv_out}")
    
    
import glob

def analyze_state_coverage_by_seed(csv_folder):
    seed_grid_data = defaultdict(lambda: defaultdict(set))  # seed -> grid_size -> set of keys
    
    csv_files = sorted(glob.glob(os.path.join(csv_folder, "*.csv")))
    print(f"Found {len(csv_files)} CSV files in: {csv_folder}\n")
    
    for csv_path in tqdm(csv_files, desc="Processing CSVs"):
        seed_name = os.path.basename(csv_path).split('.')[0]  # e.g., seed123.csv -> "seed123"
        
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                
                try:
                    grid_size = int(row[0])
                    agent_x = int(row[1])
                    agent_y = int(row[2])
                    goal_x = int(row[3])
                    goal_y = int(row[4])
                    
                    lava_coords = list(map(int, row[5:]))
                    lava_tiles = list(zip(lava_coords[::2], lava_coords[1::2]))
                    total_lava = len(lava_tiles)
                    
                    key = (agent_x, agent_y, goal_x, goal_y, total_lava, tuple(sorted(lava_tiles)))
                    seed_grid_data[seed_name][grid_size].add(key)
                except Exception as e:
                    print(f"Error parsing row in {os.path.basename(csv_path)}: {e}")
                    continue
                
    summary = []
    for seed, grid_map in seed_grid_data.items():
        norm_sum = Decimal(0)
        for grid_size, keys in grid_map.items():
            raw = Decimal(len(keys))
            max_possible = Decimal(pow(3, grid_size*grid_size))  # 3^grid_size
            normalized = raw / max_possible
            norm_sum += normalized
            print(f"  ➤ Grid Size {grid_size}:")
            print(f"     Found: {int(raw)} unique combinations")
            print(f"     Max Possible: {int(max_possible)}")
            print(f"     Average: {float(normalized):.10f}")
        summary.append((seed, float(norm_sum)))
        
    # Save final summary
    output_path = os.path.join(csv_folder, "seedwise_state_coverage.csv")
    with open(output_path, "w", newline="") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["Seed", "Normalized_Coverage_Sum"])
        for row in summary:
            writer.writerow(row)
            
    print(f"\nFinal seed-level normalized state coverage saved to: {output_path}")
    
    
getcontext().prec = 10  # High precision for decimals

def extract_key_from_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Grid size
        grid_size = None
        for attr in root.findall("Attribute"):
            name = attr.find("Name").attrib["value"]
            if name == "Grid":
                grid_size = int(attr.find("Value").attrib["value"])
                
        # Agent position
        agent_elem = root.find(".//Agent[@id='1']")
        agent_x = agent_y = None
        if agent_elem is not None:
            for attr in agent_elem.findall("Attribute"):
                name = attr.find("Name").attrib["value"]
                val = int(attr.find("Value").attrib["value"])
                if name == "X":
                    agent_x = val
                elif name == "Y":
                    agent_y = val
                    
        # Lava positions
        lava_tiles = []
        for lava_obj in root.findall(".//Object[@type='Lava']"):
            lava_x = lava_y = None
            for attr in lava_obj.findall("Attribute"):
                name = attr.find("Name").attrib["value"]
                val = int(attr.find("Value").attrib["value"])
                if name == "X":
                    lava_x = val
                elif name == "Y":
                    lava_y = val
            lava_tiles.append((lava_x, lava_y))
            
        total_lava = len(lava_tiles)
        
        # If essential fields are missing, skip
        if None in (grid_size, agent_x, agent_y):
            print(f"Missing required fields in {xml_path}. Skipping.")
            return None, None
        
        return grid_size, (agent_x, agent_y, total_lava, tuple(sorted(lava_tiles)))
    
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None, None
    
def process_seed(seed_path):
        seed_name = os.path.basename(seed_path)
        grid_data = defaultdict(set)  # grid_size -> set of unique states
    
        for env in os.listdir(seed_path):
            env_path = os.path.join(seed_path, env)
            if not os.path.isdir(env_path):
                continue
            
            for task in os.listdir(env_path):
                task_path = os.path.join(env_path, task)
                if not os.path.isdir(task_path):
                    continue
                
                init_xml_path = os.path.join(task_path, "initialState.xml")
                if not os.path.exists(init_xml_path):
                    continue
                
                grid_size, key = extract_key_from_xml(init_xml_path)
                if grid_size and key:
                    grid_data[grid_size].add(key)
                    
        # Compute normalized per grid size and average them
        norm_values = []
        for grid_size, keys in grid_data.items():
            raw = Decimal(len(keys))
            max_possible = Decimal(pow(3, grid_size * grid_size))  # 3^(grid_size * grid_size)
            normalized = raw / max_possible
            norm_values.append(normalized)
            
            print(f"Seed {seed_name} ➜ Grid Size {grid_size}:")
            print(f"  Found: {int(raw)} unique")
            print(f"  Max Possible: {int(max_possible)}")
            print(f"  Normalized: {float(normalized):.10f}")
            
        avg_normalized = sum(norm_values) / len(norm_values) if norm_values else Decimal(0)
        return seed_name, avg_normalized

    
def main_parallel_coverage(base_dir):
        seed_paths = [
            os.path.join(base_dir, seed)
            for seed in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, seed))
        ]
    
        coverage_results = {}
        print(f"Processing {len(seed_paths)} seeds with 20 processes...\n")
    
        with ProcessPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(process_seed, path): path for path in seed_paths}
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Progress"):
                seed, avg_normalized = future.result()
                coverage_results[seed] = avg_normalized
                
        print("\nAverage Normalized State Coverage per Seed:\n")
        for seed in sorted(coverage_results, key=lambda s: int(s)):
            avg_norm = coverage_results[seed]
            print(f"Seed {seed}: Average state coverage = {float(avg_norm):.10f}")
            
        # === Save to CSV ===
        csv_path = "state_coverage_per_seed_avg.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Seed", "Average_Normalized_Coverage"])
            for seed in sorted(coverage_results, key=lambda s: int(s)):
                writer.writerow([seed, float(coverage_results[seed])])
                
        print(f"\nResults saved to {csv_path}")
    
        normalized_values = [float(avg_norm) for avg_norm in coverage_results.values()]
        average_normalized = sum(normalized_values) / len(normalized_values) if normalized_values else 0
        print(f"\nAverage of average-state coverages across {len(normalized_values)} seeds: {average_normalized:.10f}")
    
    
    
def extract_key_from_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Grid size
        grid_size = None
        for attr in root.findall("Attribute"):
            name = attr.find("Name").attrib["value"]
            if name == "Grid":
                grid_size = int(attr.find("Value").attrib["value"])
                
        # Agent position
        agent_elem = root.find(".//Agent[@id='1']")
        agent_x = agent_y = None
        if agent_elem is not None:
            for attr in agent_elem.findall("Attribute"):
                name = attr.find("Name").attrib["value"]
                val = int(attr.find("Value").attrib["value"])
                if name == "X":
                    agent_x = val
                elif name == "Y":
                    agent_y = val
                    
        # Lava positions
        lava_tiles = []
        for lava_obj in root.findall(".//Object[@type='Lava']"):
            lava_x = lava_y = None
            for attr in lava_obj.findall("Attribute"):
                name = attr.find("Name").attrib["value"]
                val = int(attr.find("Value").attrib["value"])
                if name == "X":
                    lava_x = val
                elif name == "Y":
                    lava_y = val
            lava_tiles.append((lava_x, lava_y))
            
        total_lava = len(lava_tiles)
        
        # If essential fields are missing, skip
        if None in (grid_size, agent_x, agent_y):
            print(f"Missing required fields in {xml_path}. Skipping.")
            return None, None
        
        return grid_size, (agent_x, agent_y, total_lava, tuple(sorted(lava_tiles)))
    
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return None, None
    
    
def process_config(config_path):
    config_name = os.path.basename(config_path)
    init_xml_path = os.path.join(config_path, "initialState.xml")
    
    if not os.path.exists(init_xml_path):
        print(f"{init_xml_path} does not exist. Skipping.")
        return config_name, Decimal(0)
    
    grid_size, key = extract_key_from_xml(init_xml_path)
    if grid_size is None or key is None:
        print(f"Skipping config {config_name} due to missing data.")
        return config_name, Decimal(0)
    
    # Compute normalized coverage for this config
    raw = Decimal(1)  # only one XML, so "1 unique"
    max_possible = Decimal(pow(3, grid_size * grid_size))
    normalized = raw / max_possible
    
    print(f"Config {config_name}:")
    print(f"  Grid Size: {grid_size}")
    print(f"  Max Possible States: {int(max_possible)}")
    print(f"  Normalized Coverage: {float(normalized):.10f}")
    
    return config_name, normalized


def main_parallel_coverage_single_level(base_dir):
    config_paths = [
        os.path.join(base_dir, config)
        for config in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, config))
    ]
    
    coverage_results = {}
    print(f"Processing {len(config_paths)} configs with 20 processes...\n")
    
    with ProcessPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_config, path): path for path in config_paths}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Progress"):
            config, normalized = future.result()
            coverage_results[config] = normalized
            
    print("\nNormalized Coverage per Config:\n")
    for config in sorted(coverage_results, key=lambda s: int(s.replace("Config_", ""))):
        norm = coverage_results[config]
        print(f"{config}: Normalized coverage = {float(norm):.10f}")
        
    # === Save to CSV ===
    csv_path = "state_coverage_per_config.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Config", "Normalized_Coverage"])
        for config in sorted(coverage_results, key=lambda s: int(s.replace("Config_", ""))):
            writer.writerow([config, float(coverage_results[config])])
            
    print(f"\nResults saved to {csv_path}")
    
    normalized_values = [float(norm) for norm in coverage_results.values()]
    average_normalized = sum(normalized_values) / len(normalized_values) if normalized_values else 0
    print(f"\nAverage normalized coverage across {len(normalized_values)} configs: {average_normalized:.10f}")
    
    
    
if __name__ == "__main__":
    #base_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50_Fixed/100_Bin"
    main_parallel_coverage(base_dir)