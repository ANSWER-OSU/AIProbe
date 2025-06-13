import os
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np
from collections import defaultdict

# === CONFIG ===
csv_path = "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_2/10-20_seed/100_Bin/accurate_model.csv"
base_dir = "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_2/10-20_seed/100_Bin"
n_bins = 100

# === HELPERS ===
def parse_float(value_str):
    try:
        return float(value_str)
    except:
        return None

def extract_3_agent_positions(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        agents = root.find("Agents")
        if agents is None:
            return None

        coords = []
        for agent in agents[:3]:
            x = y = None
            for attr in agent.findall("Attribute"):
                name = attr.find("Name").get("value").lower()
                value = parse_float(attr.find("Value").get("value"))
                if name == "x":
                    x = value
                elif name == "y":
                    y = value
            if None in (x, y):
                return None
            coords.append((x, y))

        return coords if len(coords) == 3 else None
    except Exception as e:
        print(f"Error reading {xml_path}: {e}")
        return None

def bin_values(values, n_bins=5):
    min_val, max_val = min(values), max(values)
    if min_val == max_val:
        return [0] * len(values)
    return [int(np.clip((v - min_val) / (max_val - min_val) * (n_bins - 1), 0, n_bins - 1)) for v in values]

# === MAIN ===
if __name__ == "__main__":
    df = pd.read_csv(csv_path)
    grouped = df.groupby("Seed")

    for seed, seed_df in grouped:
        all_coords = []

        for _, row in seed_df.iterrows():
            env = str(row["Environment"])
            task = str(row["Task"])
            xml_path = os.path.join(base_dir, str(seed), env, task, "simulation_final.xml")
            if not os.path.exists(xml_path):
                continue

            agent_positions = extract_3_agent_positions(xml_path)
            if agent_positions:
                flat = [coord for pair in agent_positions for coord in pair]  # (x1,y1,x2,y2,x3,y3)
                all_coords.append(flat)

        if not all_coords:
            print(f"🚫 Seed {seed}: No valid agent positions found.")
            continue

        # Transpose and bin each column independently
        x1s, y1s, x2s, y2s, x3s, y3s = zip(*all_coords)

# Bin each independently
        x1_bins = bin_values(x1s, n_bins=n_bins)
        y1_bins = bin_values(y1s, n_bins=n_bins)
        x2_bins = bin_values(x2s, n_bins=n_bins)
        y2_bins = bin_values(y2s, n_bins=n_bins)
        x3_bins = bin_values(x3s, n_bins=n_bins)
        y3_bins = bin_values(y3s, n_bins=n_bins)

        # Combine the bins into tuples
        binned_combinations = set()
        for i in range(len(x1_bins)):
            combo = (x1_bins[i], y1_bins[i], x2_bins[i], y2_bins[i], x3_bins[i], y3_bins[i])
            binned_combinations.add(combo)

        print(f"\n🎯 Seed {seed} — 📦 Unique binned (x1,y1,x2,y2,x3,y3) tuples: {len(binned_combinations)}")
        for entry in sorted(binned_combinations):
             print(entry)