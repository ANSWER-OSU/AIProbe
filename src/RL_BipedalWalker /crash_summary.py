import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict


parser = argparse.ArgumentParser(description="Crash analysis for BipedalWalker")
parser.add_argument("--csv_path", required=True, help="Path to the simulation results CSV file")
parser.add_argument("--base_dir", required=True, help="Path to the folder containing task directories")
args = parser.parse_args()
csv_path =args.csv_path
base_dir =args.base_dir
output_csv = "crash_stats_per_seed.csv"


df = pd.read_csv(csv_path)
bug_df = df[df["Bug Detected"] == True]

def extract_terrain_array(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for obj in root.findall(".//Object"):
            for attr in obj.findall("Attribute"):
                name = attr.find("Name")
                if name is not None and name.attrib.get("value") == "Terrain":
                    value = attr.find("Value")
                    if value is not None:
                        return value.attrib["value"]
    except Exception as e:
        print(f"Failed to parse: {xml_path}, Error: {e}")
    return None


terrain_by_seed = defaultdict(set)
crash_count_by_seed = defaultdict(int)

for _, row in bug_df.iterrows():
    seed = int(row["Seed"])
    env = row["Env"].replace("Env_", "")
    task = row["Task"].replace("Task_", "")
    xml_path = os.path.join(base_dir, str(seed), f"Env_{env}", f"Task_{task}", "initialState.xml")
    
    terrain_str = extract_terrain_array(xml_path)
    crash_count_by_seed[seed] += 1
    if terrain_str:
        terrain_by_seed[seed].add(terrain_str)


output_rows = []
for seed in sorted(crash_count_by_seed):
    output_rows.append({
        "Seed": seed,
        "Crash_Count": crash_count_by_seed[seed],
        "Unique_Terrain_Sequences": len(terrain_by_seed[seed])
    })

out_df = pd.DataFrame(output_rows)
out_df.to_csv(output_csv, index=False)

print(f"Saved per-seed crash and unique terrain stats to: {output_csv}")