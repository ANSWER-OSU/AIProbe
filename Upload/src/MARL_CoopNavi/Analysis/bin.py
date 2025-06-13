import os
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np

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

    all_coords = []  # stores raw (x1,y1,x2,y2,x3,y3) per file

    for _, row in df.iterrows():
        seed = str(row["Seed"])
        env = str(row["Environment"])
        task = str(row["Task"])
        xml_path = os.path.join(base_dir, seed, env, task, "initialState.xml")
        if not os.path.exists(xml_path):
            continue

        agent_positions = extract_3_agent_positions(xml_path)
        if agent_positions:
            flat = [coord for pair in agent_positions for coord in pair]  # flatten (x1,y1),(x2,y2),(x3,y3)
            all_coords.append(flat)

    if not all_coords:
        print("No valid agent positions found.")
        exit()

    # Transpose columns to get list of all X1, Y1, ..., Y3 separately
    columns = list(zip(*all_coords))
    binned_columns = [bin_values(col, n_bins=n_bins) for col in columns]

    # Rebuild binned tuples
    binned_combinations = set()
    for i in range(len(all_coords)):
        combo = tuple(col[i] for col in binned_columns)
        binned_combinations.add(combo)

    for entry in sorted(binned_combinations):
        print(entry)
    print(f"\n📦 Total unique (x1_bin, y1_bin, x2_bin, y2_bin, x3_bin, y3_bin) tuples: {len(binned_combinations)}")
    