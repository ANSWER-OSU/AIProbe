import os
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from collections import defaultdict

# === CONFIG ===
csv_path = "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/10_Bin_Copy/accurate_model.csv"
base_dir = "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/10_Bin_Copy/"
n_bins = 10

# === HELPERS ===
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
        print(f"⚠️ File not found: {xml_path}")
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
            print(f"⚠️ Skipping binning: value={value}, min={min_val}, max={max_val}")
            continue
        norm = (value - min_val) / (max_val - min_val)
        norm = np.clip(norm, 0, 1)
        bin_idx = int(norm * (n_bins - 1))
        binned.append(bin_idx)
    return tuple(binned)

# === CORE FUNCTION ===
def build_bug_crash_dict_from_csv(csv_path, base_dir, n_bins=5):
    df = pd.read_csv(csv_path)
    df_filtered = df[df["BugFound"] == True]

    all_seeds = set(str(s) for s in df["Seed"])
    crash_dict = defaultdict(list)
    per_seed_crash_bins = defaultdict(set)
    per_seed_total_crashes = defaultdict(int)

    for _, row in df_filtered.iterrows():
        seed = str(row["Seed"])
        env = str(row["Environment"])
        task = str(row["Task"])

        xml_path = os.path.join(base_dir, seed, env, task, "finalState.xml")
        print(f"🔍 Reading: {xml_path}")

        crash_vector = extract_mutable_floats_with_constraints(xml_path)
        if not crash_vector:
            print(f"⛔ Skipped (no valid crash vector) for seed {seed}")
            continue

        crash_bin = bin_vector_with_constraints(crash_vector, n_bins)
        if not crash_bin:
            print(f"⚠️ Empty bin vector for {xml_path}")
            continue

        per_seed_total_crashes[seed] += 1

        if crash_bin not in crash_dict[seed]:
            crash_dict[seed].append(crash_bin)
            per_seed_crash_bins[seed].add(crash_bin)

        print(f"[✓] Seed {seed} → crash_bin: {crash_bin}")

    return crash_dict, per_seed_crash_bins, per_seed_total_crashes, all_seeds

# === MAIN ===
if __name__ == "__main__":
    crash_mapping, per_seed_crash_bins, per_seed_total_crashes, all_seeds = build_bug_crash_dict_from_csv(
        csv_path, base_dir, n_bins
    )

    # Unique bins across all seeds
    all_unique_bins = set()
    for bins in crash_mapping.values():
        all_unique_bins.update(bins)

    print(f"\n📊 MARL CoopNavi Bug Statistics:")
    print(f"   - Total crash bin entries: {sum(len(b) for b in crash_mapping.values())}")
    print(f"   - Unique seeds with crashes: {len(crash_mapping)}")

    print(f"\n🧩 Unique Crash Binned States ({len(all_unique_bins)}):")
    for b in sorted(all_unique_bins):
        print(b)

    # Save per-seed summary
    per_seed_csv = os.path.join(base_dir, "marl_per_seed_crash_summary.csv")
    with open(per_seed_csv, "w") as f:
        f.write("Seed,Unique Crash Bins,Total Crash Bins\n")
        for seed in sorted(all_seeds):
            unique = len(per_seed_crash_bins[seed])
            total = per_seed_total_crashes[seed]
            f.write(f"{seed},{unique},{total}\n")

    print(f"\n📄 Per-seed crash summary saved to: {per_seed_csv}")

    total_bins = sum(len(b) for b in per_seed_crash_bins.values())
    avg_bins = total_bins / max(len(all_seeds), 1)
    print(f"🧮 Total crash bins: {total_bins}")
    print(f"🧮 Average crash bins per seed: {avg_bins:.2f}")