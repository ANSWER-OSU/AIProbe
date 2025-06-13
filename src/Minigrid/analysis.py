### import os
### import pandas as pd
### import xml.etree.ElementTree as ET
### from collections import defaultdict
##
### # === CONFIG ===
### csv_path = "/scratch/projects/AIProbe-Main/AIProbe/Minigrid/computePolicy/results_for_fuzzer_gen_configs/Seed_789/_accurate_reward_accurate_state_rep_results.csv"
### base_db_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_new_50/100_Bin"
### NUM_BINS = 100
##
### # === Step 1: Load and filter the CSV ===
### df = pd.read_csv(csv_path)
### df.columns = [col.strip() for col in df.columns]  # remove column name whitespace
### filtered_df = df[(df["#Lava"] == 1.0) & (df["#AgentToGoal"] == 0)]
##
### # === Step 2: Define XML binning function ===
### def parse_bins_from_xml(xml_path, num_bins=NUM_BINS):
###     try:
###         tree = ET.parse(xml_path)
###         root = tree.getroot()
###         bins = []
##
###         for attr in root.iter("Attribute"):
###             name_elem = attr.find("Name")
###             value_elem = attr.find("Value")
###             constraint_elem = attr.find("Constraint")
##
###             if name_elem is not None and value_elem is not None and constraint_elem is not None:
###                 try:
###                     val = float(value_elem.attrib["value"])
###                     min_val = float(constraint_elem.attrib.get("Min", 0))
###                     max_val = float(constraint_elem.attrib.get("Max", min_val + 1))
##
###                     if max_val > min_val:
###                         bin_width = (max_val - min_val) / num_bins
###                         bin_index = int((val - min_val) / bin_width)
###                         bin_index = min(bin_index, num_bins - 1)
###                         bins.append(bin_index)
###                 except (ValueError, KeyError):
###                     continue  # skip invalid values
###         return tuple(bins)
###     except Exception as e:
###         print(f"[ERROR] Failed to parse {xml_path}: {e}")
###         return None
##
### # === Step 3: Process each filtered row and build crash dict ===
### unique_crash_dict = {}
##
### for _, row in filtered_df.iterrows():
###     seed = int(row["Seed"])
###     env = int(row["Env#"])
###     task = int(row["Task#"])
##
###     task_dir = os.path.join(base_db_dir, f"{seed}", f"Env_{env}", f"Task_{task}")
###     init_path = os.path.join(task_dir, "initialState.xml")
###     final_path = os.path.join(task_dir, "finalState.xml")
##
###     if not os.path.exists(init_path) or not os.path.exists(final_path):
###         print(f"[WARNING] Missing XMLs for Seed {seed}, Env {env}, Task {task}")
###         continue
##
###     initial_bins = parse_bins_from_xml(init_path)
###     final_bins = parse_bins_from_xml(final_path)
##
###     if initial_bins and final_bins:
###         if initial_bins not in unique_crash_dict:
###             unique_crash_dict[initial_bins] = final_bins
##
### # === Step 4: Print summary ===
### print(f"\n✅ Total unique crash initial states: {len(unique_crash_dict)}")
### print(f"📌 Total crash tasks processed (filtered rows): {len(filtered_df)}")
##
### # Optional: Print sample entries
### for i, (k, v) in enumerate(unique_crash_dict.items()):
###     print(f"Initial: {k} -> Final: {v}")
###     if i >= 1:
###         break
##
##import os
##os.environ["OPENBLAS_NUM_THREADS"] = "1"
##os.environ["OMP_NUM_THREADS"] = "1"
##os.environ["MKL_NUM_THREADS"] = "1"
##
##
##
##
##
##
##
##import pandas as pd
##import xml.etree.ElementTree as ET
##
### === CONFIG ===
##results_base_dir = "/scratch/projects/AIProbe-Main/AIProbe/Minigrid/accurate_reward_accurate_state_rep_results_1.csv"
##base_db_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50/100_Bin"
##NUM_BINS = 100
##
### === Step 1: XML binning function ===
##def parse_bins_from_xml(xml_path, num_bins=NUM_BINS):
##   try:
##       tree = ET.parse(xml_path)
##       root = tree.getroot()
##       bins = []
##
##       for attr in root.iter("Attribute"):
##           name_elem = attr.find("Name")
##           value_elem = attr.find("Value")
##           constraint_elem = attr.find("Constraint")
##
##           if name_elem is not None and value_elem is not None and constraint_elem is not None:
##               try:
##                   val = float(value_elem.attrib["value"])
##                   min_val = float(constraint_elem.attrib.get("Min", 0))
##                   max_val = float(constraint_elem.attrib.get("Max", min_val + 1))
##
##                   if max_val > min_val:
##                       bin_width = (max_val - min_val) / num_bins
##                       bin_index = int((val - min_val) / bin_width)
##                       bin_index = min(bin_index, num_bins - 1)
##                       bins.append(bin_index)
##               except (ValueError, KeyError):
##                   continue
##       return tuple(bins)
##   except Exception as e:
##       print(f"[ERROR] Failed to parse {xml_path}: {e}")
##       return None
##
### === Step 2: Process each Seed folder ===
##for seed_folder in os.listdir(results_base_dir):
##   if not seed_folder.startswith("Seed_"):
##       continue
##
##   seed_id = int(seed_folder.split("_")[1])
##   csv_path = os.path.join(results_base_dir, seed_folder, "_accurate_reward_accurate_state_rep_results.csv")
##
##   if not os.path.exists(csv_path):
##       print(f"[SKIP] No CSV in {seed_folder}")
##       continue
##
##   print(f"\n🔍 Processing Seed {seed_id}...")
##
##   try:
##       df = pd.read_csv(csv_path)
##       df.columns = [col.strip() for col in df.columns]
##       filtered_df = df[(df["#Lava"] == 1.0) & (df["#AgentToGoal"] == 0)]
##   except Exception as e:
##       print(f"[ERROR] Failed to load or parse CSV: {e}")
##       continue
##
##   unique_crash_dict = {}
##
##   for _, row in filtered_df.iterrows():
##       env = int(row["Env#"])
##       task = int(row["Task#"])
##
##       task_dir = os.path.join(base_db_dir, f"{seed_id}", f"Env_{env}", f"Task_{task}")
##       init_path = os.path.join(task_dir, "initialState.xml")
##       final_path = os.path.join(task_dir, "finalState.xml")
##
##       if not os.path.exists(init_path) or not os.path.exists(final_path):
##           print(f"[WARN] Missing XMLs for Env {env}, Task {task}")
##           continue
##
##       initial_bins = parse_bins_from_xml(init_path)
##       final_bins = parse_bins_from_xml(final_path)
##
##       if initial_bins and final_bins:
##           if initial_bins not in unique_crash_dict:
##               unique_crash_dict[initial_bins] = final_bins
##
##   # === Summary per seed ===
##   print(f"✅ Seed {seed_id}: {len(unique_crash_dict)} unique crash initial states")
##   print(f"📌 Total crash tasks processed: {len(filtered_df)}")
##
##   # Print 1 example
##   for i, (k, v) in enumerate(unique_crash_dict.items()):
##       print(f"🧪 Example → Initial: {k} -> Final: {v}")
##       break
#
#
#import os
#os.environ["OPENBLAS_NUM_THREADS"] = "1"
#os.environ["OMP_NUM_THREADS"] = "1"
#os.environ["MKL_NUM_THREADS"] = "1"
#
#
#
#
#
#
#
#import pandas as pd
#import xml.etree.ElementTree as ET
#
## === CONFIG ===
#csv_path = "/scratch/projects/AIProbe-Main/AIProbe/Minigrid/accurate_reward_accurate_state_rep_results_1.csv"
#base_db_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50_Fixed/100_Bin"
#NUM_BINS = 100
#
## === Function: Parse bin indices from XML ===
#def parse_bins_from_xml(xml_path, num_bins=NUM_BINS):
#   try:
#       tree = ET.parse(xml_path)
#       root = tree.getroot()
#       bins = []
#       
#       for attr in root.iter("Attribute"):
#           name_elem = attr.find("Name")
#           value_elem = attr.find("Value")
#           constraint_elem = attr.find("Constraint")
#           
#           if name_elem is not None and value_elem is not None and constraint_elem is not None:
#               try:
#                   val = float(value_elem.attrib["value"])
#                   min_val = float(constraint_elem.attrib.get("Min", 0))
#                   max_val = float(constraint_elem.attrib.get("Max", min_val + 1))
#                   
#                   if max_val > min_val:
#                       bin_width = (max_val - min_val) / num_bins
#                       bin_index = int((val - min_val) / bin_width)
#                       bin_index = min(bin_index, num_bins - 1)
#                       bins.append(bin_index)
#               except (ValueError, KeyError):
#                   continue
#       return tuple(bins)
#   except Exception as e:
#       print(f"[ERROR] Failed to parse {xml_path}: {e}")
#       return None
#   
## === Step 1: Load and filter global CSV ===
#df = pd.read_csv(csv_path)
#df.columns = df.columns.str.strip()
#filtered_df = df[(df["#Lava"] == 1.0) & (df["#AgentToGoal"] == 0)]
#
## === Step 2: Per-seed unique crash state analysis ===
#global_unique_crashes = set()
#per_seed_crash_dict = {}
#
#print(f"\n🧪 Processing {len(filtered_df)} crash task rows")
#
#for _, row in filtered_df.iterrows():
#   try:
#       seed = int(row["Seed"])
#       env = int(row["Env#"])
#       task = int(row["Task#"])
#   except Exception as e:
#       print(f"[ERROR] Failed to parse row: {e}")
#       continue
#   
#   task_dir = os.path.join(base_db_dir, str(seed), f"Env_{env}", f"Task_{task}")
#   init_path = os.path.join(task_dir, "initialState.xml")
#   final_path = os.path.join(task_dir, "finalState.xml")
#   print(final_path)
#   
#   if not os.path.exists(init_path) or not os.path.exists(final_path):
#       print(f"[WARN] Missing XMLs for Seed {seed}, Env {env}, Task {task}")
#       continue
#   
#   initial_bins = parse_bins_from_xml(init_path)
#   final_bins = parse_bins_from_xml(final_path)
#   
#   if initial_bins is None or final_bins is None:
#       continue
#   
#   # Track globally and per seed
#   if initial_bins not in global_unique_crashes:
#       global_unique_crashes.add(initial_bins)
#       
#       if seed not in per_seed_crash_dict:
#           per_seed_crash_dict[seed] = {}
#       if initial_bins not in per_seed_crash_dict[seed]:
#           per_seed_crash_dict[seed][initial_bins] = final_bins
#           
## === Step 3: Summary ===
#print(f"\n✅ Total global unique initial crash bins: {len(global_unique_crashes)}")
#print(f"📌 Total seeds processed: {len(per_seed_crash_dict)}")
#
#for seed, crash_map in per_seed_crash_dict.items():
#   print(f"\n🔹 Seed {seed}: {len(crash_map)} unique crashes")
#   for i, (k, v) in enumerate(crash_map.items()):
#       print(f"   🧪 Example → Initial: {k} -> Final: {v}")
#       break  # print one example per seedci


#!/usr/bin/env python3
import os
# ─── Limit BLAS/OpenMP Threads ─────────────────────────────────────────────────
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# ─── Standard Imports ──────────────────────────────────────────────────────────
import pandas as pd
import xml.etree.ElementTree as ET
from multiprocessing import Pool, cpu_count

# ─── CONFIG ────────────────────────────────────────────────────────────────────
CSV_PATH    = "/scratch/projects/AIProbe-Main/AIProbe/Minigrid/accurate_reward_accurate_state_rep_results_1.csv"
BASE_DB_DIR = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1_Grid_50_Fixed/100_Bin"
NUM_BINS    = 100
NUM_PROCS   = 20  # number of worker processes in the Pool

# ─── FUNCTIONS ─────────────────────────────────────────────────────────────────
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

# ─── MAIN SCRIPT ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1. Load and filter the CSV
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    filtered = df[(df["#Lava"] == 1.0) & (df["#AgentToGoal"] == 0)]
    print(f"🧪 Loaded {len(filtered)} crash-task rows from CSV")
    
    # 2. Build a simple list of (seed, env, task) tuples
    tasks = []
    for _, row in filtered.iterrows():
        try:
            tasks.append((int(row["Seed"]), int(row["Env#"]), int(row["Task#"])))
        except Exception as e:
            print(f"[WARN] Skipping row due to parse error: {e}")
            
    print(f"🔧 Prepared {len(tasks)} tasks for processing")
    
    # 3. Parallel processing with a Pool
    print(f"⚙️  Spawning {NUM_PROCS} worker processes...")
    with Pool(processes=NUM_PROCS) as pool:
        results = pool.map(process_task, tasks)
        
    # 4. Aggregate unique crashes
#   global_unique = set()
#   per_seed_map  = {}
#   
#   for res in results:
#       if res is None:
#           continue
#       seed, init_bins, final_bins = res
#       if init_bins not in global_unique:
#           global_unique.add(init_bins)
#           per_seed_map.setdefault(seed, {})[init_bins] = final_bins
#           
#   # 5. Print summary
#   print(f"\n✅ Total global unique initial crash bins: {len(global_unique)}")
#   print(f"📌 Total seeds with at least one unique crash: {len(per_seed_map)}")
#   
#   for seed, crash_map in per_seed_map.items():
#       print(f"\n🔹 Seed {seed}: {len(crash_map)} unique crashes")
#       # show one example:
#       init_example, final_example = next(iter(crash_map.items()))
#       print(f"   🧪 Example → Initial: {init_example} -> Final: {final_example}")
        
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
        
# 5. Print summary
print(f"\n✅ Total global unique initial crash bins: {len(global_unique)}")
print(f"📌 Total seeds with at least one unique crash: {len(per_seed_map)}")
#
for seed in sorted(per_seed_total):
    total = per_seed_total[seed]
    unique = len(per_seed_map.get(seed, {}))
    print(f"\n🔹 Seed {seed}: {unique} unique / {total} total crashes")
#   if unique > 0:
#       init_example, final_example = next(iter(per_seed_map[seed].items()))
#       print(f"   🧪 Example → Initial: {init_example} -> Final: {final_example}")