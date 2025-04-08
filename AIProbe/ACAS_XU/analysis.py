import os
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np
from collections import defaultdict

def parse_value(value_str, dtype):
    if value_str.lower() == "unknown":
        return None
    try:
        return float(value_str) if dtype == "float" else int(value_str)
    except ValueError:
        return None

def safe_parse_bound(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def extract_mutable_floats_with_constraints(xml_path):
    if not os.path.exists(xml_path):
        print(f"File not found: {xml_path}")
        return []

    tree = ET.parse(xml_path)
    root = tree.getroot()
    values = []

    def process_attributes(attr_list):
        for attr in attr_list:
            dtype = attr.find("DataType").get("value")
            mutable = attr.find("Mutable").get("value").lower() == "true"
            val_str = attr.find("Value").get("value")
            value = parse_value(val_str, dtype)
            if not (mutable and dtype in {"float", "int"} and value is not None):
                continue
            constraint = attr.find("Constraint")
            min_val = safe_parse_bound(constraint.get("Min")) if constraint is not None else None
            max_val = safe_parse_bound(constraint.get("Max")) if constraint is not None else None
            values.append((value, min_val, max_val))

    for section in ["Agents", "Objects"]:
        parent = root.find(section)
        if parent is not None:
            for entity in parent:
                process_attributes(entity.findall("Attribute"))

    process_attributes(root.findall("Attribute"))
    return values

def bin_vector_with_constraints(values_with_bounds, n_bins):
    binned = []
    for value, min_val, max_val in values_with_bounds:
        if min_val is None or max_val is None or max_val <= min_val:
            continue
        norm = (value - min_val) / (max_val - min_val)
        norm = np.clip(norm, 0, 1)
        bin_idx = int(norm * (n_bins - 1))
        binned.append(bin_idx)
    return tuple(binned)

def build_crash_dict_from_csv(csv_path, n_bins=10, model_id=1):
    df = pd.read_csv(csv_path)
    df_filtered = df[(df["Terminated"] == True) & (df["Invalid Initial State"] == False)]

    all_seeds = set(df["Seed Number"])
    crash_dict = defaultdict(list)
    per_seed_crash_bins = defaultdict(set)
    per_seed_total_crashes = defaultdict(int)

    for _, row in df_filtered.iterrows():
        seed = row["Seed Number"]
        dir_path = os.path.dirname(row["File Path"])
        init_path = os.path.join(dir_path, "finalState.xml")
        crash_path = os.path.join(dir_path, f"model{model_id}_crash_result.xml")

        init_vector = extract_mutable_floats_with_constraints(init_path)
        crash_vector = extract_mutable_floats_with_constraints(crash_path)

        if not init_vector or not crash_vector:
            continue

        init_bin = bin_vector_with_constraints(init_vector, n_bins)
        crash_bin = bin_vector_with_constraints(crash_vector, n_bins)

        # Track total
        per_seed_total_crashes[seed] += 1

        if crash_bin not in crash_dict[init_bin]:
            crash_dict[init_bin].append(crash_bin)
            per_seed_crash_bins[seed].add(crash_bin)
    

    return crash_dict, per_seed_crash_bins, per_seed_total_crashes, all_seeds

def compare_models(base_path, model_versions, n_bins=5):
    model_crash_maps = {}
    for version in model_versions:
        csv_path = os.path.join(base_path, f"model_{version}_simulation_results_parallel.csv")
        model_name = f"model{version}"
        print(f" Processing Model {version}")
        crash_map = build_crash_dict_from_csv(csv_path, n_bins, model_name=model_name)
        model_crash_maps[version] = crash_map
        print(f"Model {version} → Total init bins: {len(crash_map)}")

    model1_map = model_crash_maps[1]
    model1_crashes = set((k, tuple(v)) for k, vs in model1_map.items() for v in vs)

    for version in model_versions:
        if version == 1:
            continue
        other_map = model_crash_maps[version]
        all_crashes = set((k, tuple(v)) for k, vs in other_map.items() for v in vs)
        unique_crashes = all_crashes - model1_crashes
        print(f"\n Model {version} Summary:")
        print(f"  Total Initial States with Crashes: {len(other_map)}")
        print(f"  Total Crashes: {sum(len(v) for v in other_map.values())}")
        print(f"  Unique Crashes not in Model 1: {len(unique_crashes)}")

# Example usage
if __name__ == "__main__":
    model_ids = [1, 2, 3,4,5,6,7,8,9]
    n_bins = 5
    base_dir = "/scratch/projects/AIProbe-Main/Result/ACAS_XU_Domain/Result/5_bin_copy"

    total = 0
    for model_id in model_ids:
        csv_path = os.path.join(base_dir, f"model_{model_id}_simulation_results_parallel.csv")
        crash_mapping, per_seed_crash_bins, per_seed_total_crashes, all_seeds = build_crash_dict_from_csv(csv_path, n_bins, model_id=model_id)

        total_crashes = sum(len(v) for v in crash_mapping.values())
        total += total_crashes
        unique_init_states = len(crash_mapping)

        print(f"\n Model {model_id} Statistics:")
        print(f"   - Total crash bin entries: {total_crashes}")
        print(f"   - Unique bins: {unique_init_states}")

        per_seed_csv = os.path.join(base_dir, f"model_{model_id}_per_seed_crash_summary.csv")
        with open(per_seed_csv, "w") as f:
            f.write("Seed,Unique Crash Bins,Total Crash Bins\n")
            for seed in sorted(all_seeds):
                unique_crashes = len(per_seed_crash_bins[seed]) if seed in per_seed_crash_bins else 0
                total_crashes = per_seed_total_crashes.get(seed, 0)
                f.write(f"{seed},{unique_crashes},{total_crashes}\n")
     

        print(f"Per-seed crash summary saved to: {per_seed_csv}")
        for seed in sorted(per_seed_crash_bins.keys(), key=int):
            for crash_bin in per_seed_crash_bins[seed]:
                print(f"Seed {seed}: Crash Bin = {crash_bin}")
    print(total)
    print(f"Average unique crash: {total/90}")