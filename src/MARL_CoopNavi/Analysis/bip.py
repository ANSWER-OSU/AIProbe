# import csv
# from collections import defaultdict

# def count_bugs_sorted_by_seed(csv_file_path):
#     bug_count = defaultdict(int)

#     with open(csv_file_path, 'r') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             seed = row["Env"].strip()
#             if row["Bug Detected"].strip().lower() == "true":
#                 bug_count[int(seed)] += 1  # Convert to int for numeric sorting

#     print("Seed,BugCount")
#     for seed in sorted(bug_count):
#         print(f"{seed},{bug_count[seed]}")

# # Example usage
# csv_path = "/scratch/projects/AIProbe-Main/Result/BIpedal/5_bin/tqc_simulation_results.csv"  # Replace with your actual CSV file path
# count_bugs_sorted_by_seed(csv_path)

import pandas as pd

# === Load the CSV file ===
csv_path = "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/100_Bin/inaccurate_reward_results.csv"  # Replace with your actual file path
df = pd.read_csv(csv_path)

# === Clean column names (if needed) ===
df.columns = df.columns.str.strip()

# === Filter rows where BugFound is True ===
bug_found_df = df[df["BugFound"] == True]

# === Output result ===
total_bugs = len(bug_found_df)
print(f"✅ Total crashes where BugFound == True: {total_bugs}")