import os
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict

# === CONFIG ===
csv_path = "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_accurate.csv"  # Update with your CSV path
base_dir = "/scratch/projects/AIProbe-Main/Result/FlappyBird/Flappybird/Approch_1/100_Bin"  # Where XML folders are
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
for seed, sequences in seed_to_sequences.items():
    total_crashes = len(sequences)
    unique_init_bins = {tuple(entry['InitBins']) for entry in sequences}
    unique_count = len(unique_init_bins)

    print(f"{seed},{total_crashes},{unique_count}")


print("\n=== Total Unique State Coverage per Seed ===")
print("Seed,Total_Tasks,Unique_Binned_States")

for seed in os.listdir(base_dir):
    seed_path = os.path.join(base_dir, seed)
    if not os.path.isdir(seed_path):
        continue

    all_binned = []
    for env in os.listdir(seed_path):
        env_path = os.path.join(seed_path, env)
        for task in os.listdir(env_path):
            task_path = os.path.join(env_path, task)
            init_xml_path = os.path.join(task_path, "initialState.xml")
            if not os.path.exists(init_xml_path):
                continue
            try:
                bins = get_binned_sequence(init_xml_path)
                all_binned.append(tuple(bins))
            except Exception as e:
                print(f"Error reading {init_xml_path}: {e}")

    total = len(all_binned)
    unique = len(set(all_binned))
    print(f"{seed},{total},{unique}")