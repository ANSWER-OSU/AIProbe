import os
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict
import numpy as np
import argparse

# === CONFIG ===
parser = argparse.ArgumentParser(description="Analyze FlappyBird crash stats and unique state coverage.")
parser.add_argument("--csv_path", type=str, required=True, help="Path to summary_accurate.csv")
parser.add_argument("--base_dir", type=str, required=True, help="Root directory containing XML seeds")
args = parser.parse_args()

csv_path = args.csv_path
base_dir = args.base_dir
NUM_BINS = 100

# === Step 1: Read and filter the CSV ===
df = pd.read_csv(csv_path)
df.columns = [col.strip() for col in df.columns]  # Clean whitespace
filtered_df = df[df["BugFound"] == True]

# === Step 2: Bin function ===
def bin_value(value, min_val, max_val, bins=NUM_BINS):
    value = float(value)
    min_val = float(min_val)
    max_val = float(max_val)
    if value < min_val: value = min_val
    if value > max_val: value = max_val
    bin_width = (max_val - min_val) / bins
    if bin_width == 0:
        return 0
    return int((value - min_val) / bin_width)

# === Step 3: Parse XML and get binned sequence ===
def get_binned_sequence(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    binned_seq = []

    for elem in root.iter("Attribute"):
        name_elem = elem.find("Name")
        value_elem = elem.find("Value")
        constraint = elem.find("Constraint")

        if name_elem is None or value_elem is None or constraint is None:
            continue

        try:
            value = float(value_elem.attrib.get("value"))
            min_val = float(constraint.attrib.get("Min"))
            max_val = float(constraint.attrib.get("Max"))
            bin_idx = bin_value(value, min_val, max_val)
            binned_seq.append(bin_idx)
        except Exception:
            continue

    return binned_seq

# === Step 4: Process each crash ===
seed_to_sequences = defaultdict(list)
for _, row in filtered_df.iterrows():
    env = row["Environment"]
    task = row["Task"]
    seed = row["Seed"]

    task_path = os.path.join(base_dir, str(seed), env, f"{task}")
    init_xml_path = os.path.join(task_path, "initialState.xml")
    crash_xml_path = os.path.join(task_path, "finalState.xml")

    if not os.path.exists(crash_xml_path) or not os.path.exists(init_xml_path):
        print(f"Missing XMLs for Seed={seed}, Env={env}, Task={task}")
        continue

    try:
        init_bins = get_binned_sequence(init_xml_path)
        crash_bins = get_binned_sequence(crash_xml_path)
        seed_to_sequences[seed].append({
            "Env": env,
            "Task": task,
            "InitBins": init_bins,
            "CrashBins": crash_bins
        })
    except Exception as e:
        print(f"Error processing {seed}/{env}/{task}: {e}")

# === Step 5: Output crash count and sequences ===
crash_stats = []
print("\n=== Per-Seed Crash Stats ===")
print("Seed,Total_Crashes,Unique_InitBins")
for seed, sequences in seed_to_sequences.items():
    total_crashes = len(sequences)
    unique_init_bins = {tuple(entry['InitBins']) for entry in sequences}
    unique_count = len(unique_init_bins)
            
    print(f"{seed},{total_crashes},{unique_count}")
    crash_stats.append((seed, total_crashes, unique_count))
            
        # Calculate total/average/std
crash_totals = [x[1] for x in crash_stats]
unique_counts = [x[2] for x in crash_stats]
        
# === Step 6: unique state count ===        
print("\n=== Aggregate Crash Stats ===")
print(f"Total Crashes: {sum(crash_totals)}")
print(f"Average Crashes: {np.mean(crash_totals):.2f}, Std Dev: {np.std(crash_totals):.2f}")
print(f"Average Unique InitBins: {np.mean(unique_counts):.2f}, Std Dev: {np.std(unique_counts):.2f}")


print("\n=== Total Unique State Coverage per Seed ===")
print("Seed,Unique_Binned_States")
unique_state = []
for seed in os.listdir(base_dir):
    seed_path = os.path.join(base_dir, seed)
    if not os.path.isdir(seed_path) or seed.startswith("._") or seed == ".DS_Store":
        continue

    all_binned = []
    for env in os.listdir(seed_path):
        env_path = os.path.join(seed_path, env)
        if not os.path.isdir(env_path) or env.startswith("._") or env == ".DS_Store":
                continue
        for task in os.listdir(env_path):
            task_path = os.path.join(env_path, task)
            if not os.path.isdir(task_path) or task.startswith("._") or task == ".DS_Store":
                    continue
            init_xml_path = os.path.join(task_path, "initialState.xml")
            if not os.path.exists(init_xml_path):
                continue
            try:
                bins = get_binned_sequence(init_xml_path)[:2]
                #bins = get_binned_sequence(init_xml_path)
                #print(bins)
                all_binned.append(tuple(bins))
            except Exception as e:
                print(f"Error reading {init_xml_path}: {e}")

    total = len(all_binned)
    unique = len(set(all_binned))
    unique_vale = unique/100
    print(f"{seed},{unique}")
    unique_state.append(unique_vale)

print("\n=== Unique State Stats ===")
print(f"Average Unique state: {np.mean(unique_state):.4f}")
print(f"Std Dev of Unique state: {np.std(unique_state):.4f}")