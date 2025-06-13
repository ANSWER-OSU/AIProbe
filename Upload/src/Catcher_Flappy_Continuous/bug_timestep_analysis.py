# # # import os
# # # import pandas as pd
# # # import xml.etree.ElementTree as ET
# # # import matplotlib.pyplot as plt
# # # from collections import Counter

# # # # === Parameters ===
# # # csv_path = "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_accurate.csv"  # Replace with your actual CSV path
# # # base_dir = "/scratch/projects/AIProbe-Main/Result/FlappyBird/Flappybird/Approch_1/100_Bin"  # Replace with your actual base directory
# # # output_image = "bug_timestep_histogram.png"
# # # timestep_list = []

# # # # === Step 1: Load and filter CSV ===
# # # df = pd.read_csv(csv_path)
# # # df.columns = df.columns.str.strip()  # Clean whitespace
# # # buggy_df = df[df["BugFound"] == True]

# # # # === Step 2: Extract Timestep_Count from XMLs ===
# # # for _, row in buggy_df.iterrows():
# # #     seed = str(row["Seed"])
# # #     env = row["Environment"]
# # #     task = f"{row['Task']}"
# # #     xml_path = os.path.join(base_dir, seed, env, task, "finalState.xml")

# # #     if not os.path.exists(xml_path):
# # #         print(f"⚠️ Missing: {xml_path}")
# # #         continue

# # #     try:
# # #         tree = ET.parse(xml_path)
# # #         root = tree.getroot()

# # #         timestep_elem = next(
# # #             (attr for attr in root.findall("Attribute")
# # #              if attr.find("Name").get("value") == "Timestep_Count"),
# # #             None
# # #         )

# # #         if timestep_elem is not None:
# # #             timestep = int(timestep_elem.find("Value").get("value"))
# # #             timestep_list.append(timestep)
# # #         else:
# # #             print(f"❌ Timestep_Count not found in {xml_path}")

# # #     except Exception as e:
# # #         print(f"❌ Failed to parse {xml_path}: {e}")

# # # # === Step 3: Save histogram ===
# # # if timestep_list:
# # #     plt.figure(figsize=(10, 6))
# # #     plt.hist(timestep_list, bins=200, edgecolor='black')
# # #     plt.xlabel("Timestep at crash (Timestep_Count)")
# # #     plt.ylabel("Number of Bugs")
# # #     plt.title("Bug Count Distribution by Timestep")
# # #     plt.grid(True)
# # #     plt.tight_layout()
# # #     plt.savefig(output_image)
# # #     print(f"✅ Histogram saved to {output_image}")
# # # else:
# # #     print("No valid timesteps collected. Nothing to plot.")


# # import os
# # import pandas as pd
# # import xml.etree.ElementTree as ET
# # import matplotlib.pyplot as plt
# # import csv

# # # === Parameters ===
# # csv_path = "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_accurate.csv"
# # base_dir = "/scratch/projects/AIProbe-Main/Result/FlappyBird/Flappybird/Approch_1/100_Bin"
# # output_image = "bug_timestep_histogram.png"
# # low_timestep_csv = "low_timestep_bugs.csv"
# # timestep_list = []
# # low_timestep_entries = []

# # # === Step 1: Load and filter CSV ===
# # df = pd.read_csv(csv_path)
# # df.columns = df.columns.str.strip()  # Clean whitespace
# # buggy_df = df[df["BugFound"] == True]

# # # === Step 2: Extract Timestep_Count from XMLs ===
# # for _, row in buggy_df.iterrows():
# #     seed = str(row["Seed"])
# #     env = row["Environment"]
# #     task = f"{row['Task']}"
# #     xml_path = os.path.join(base_dir, seed, env, task, "finalState.xml")

# #     if not os.path.exists(xml_path):
# #         print(f"⚠️ Missing: {xml_path}")
# #         continue

# #     try:
# #         tree = ET.parse(xml_path)
# #         root = tree.getroot()

# #         timestep_elem = next(
# #             (attr for attr in root.findall("Attribute")
# #              if attr.find("Name").get("value") == "Timestep_Count"),
# #             None
# #         )

# #         if timestep_elem is not None:
# #             timestep = int(timestep_elem.find("Value").get("value"))
# #             timestep_list.append(timestep)

# #             # ✅ Save if timestep < 2000
# #             if timestep < 2000:
# #                 low_timestep_entries.append([seed, env, task, timestep])
# #         else:
# #             print(f"❌ Timestep_Count not found in {xml_path}")

# #     except Exception as e:
# #         print(f"❌ Failed to parse {xml_path}: {e}")

# # # === Step 3: Save histogram ===
# # if timestep_list:
# #     plt.figure(figsize=(10, 6))
# #     plt.hist(timestep_list, bins=50, edgecolor='black')
# #     plt.xlabel("Timestep at crash (Timestep_Count)")
# #     plt.ylabel("Number of Bugs")
# #     plt.title("Bug Count Distribution by Timestep")
# #     plt.grid(True)
# #     plt.tight_layout()
# #     plt.savefig(output_image)
# #     print(f"✅ Histogram saved to {output_image}")
# # else:
# #     print("No valid timesteps collected. Nothing to plot.")

# # # === Step 4: Save low-timestep list ===
# # if low_timestep_entries:
# #     with open(low_timestep_csv, "w", newline="") as f:
# #         writer = csv.writer(f)
# #         writer.writerow(["Seed", "Environment", "Task", "Timestep_Count"])
# #         writer.writerows(low_timestep_entries)
# #     print(f"📄 Saved {len(low_timestep_entries)} low-timestep bug entries to {low_timestep_csv}")
# # else:
# #     print("⚠️ No bugs found with Timestep_Count < 2000.")




# import os
# import pandas as pd
# import xml.etree.ElementTree as ET
# import matplotlib.pyplot as plt
# import csv

# # === Parameters ===
# csv_path = "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_accurate.csv"
# base_dir = "/scratch/projects/AIProbe-Main/Result/FlappyBird/Flappybird/Approch_1/100_Bin"
# summary_csv = "/scratch/projects/AIProbe-Main/AIProbe/Catcher_Flappy_Continuous/instruction_generation_summary.csv"
# output_image = "bug_timestep_histogram.png"
# low_timestep_csv = "low_timestep_bugs.csv"
# timestep_list = []
# low_timestep_entries = []

# # === Step 1: Load and filter bug summary CSV ===
# df = pd.read_csv(csv_path)
# df.columns = df.columns.str.strip()
# buggy_df = df[df["BugFound"] == True]

# # === Step 2: Extract Timestep_Count from XMLs ===
# for _, row in buggy_df.iterrows():
#     seed = str(row["Seed"])
#     env = row["Environment"]
#     task = f"{row['Task']}"
#     xml_path = os.path.join(base_dir, seed, env, task, "finalState.xml")

#     if not os.path.exists(xml_path):
#         print(f"⚠️ Missing: {xml_path}")
#         continue

#     try:
#         tree = ET.parse(xml_path)
#         root = tree.getroot()
#         timestep_elem = next(
#             (attr for attr in root.findall("Attribute")
#              if attr.find("Name").get("value") == "Timestep_Count"),
#             None
#         )

#         if timestep_elem is not None:
#             timestep = int(timestep_elem.find("Value").get("value"))
#             timestep_list.append(timestep)

#             if timestep < 2000:
#                 low_timestep_entries.append([seed, env, task, timestep])
#         else:
#             print(f"❌ Timestep_Count not found in {xml_path}")
#     except Exception as e:
#         print(f"❌ Failed to parse {xml_path}: {e}")

# # === Step 3: Save histogram ===
# if timestep_list:
#     plt.figure(figsize=(10, 6))
#     plt.hist(timestep_list, bins=50, edgecolor='black')
#     plt.xlabel("Timestep at crash (Timestep_Count)")
#     plt.ylabel("Number of Bugs")
#     plt.title("Bug Count Distribution by Timestep")
#     plt.grid(True)
#     plt.tight_layout()
#     plt.savefig(output_image)
#     print(f"✅ Histogram saved to {output_image}")
# else:
#     print("No valid timesteps collected. Nothing to plot.")

# # === Step 4: Check if already solved in instruction_generation_summary.csv ===
# done_list = []
# not_done_list = []

# if os.path.exists(summary_csv):
#     solved_df = pd.read_csv(summary_csv)
#     solved_df.columns = solved_df.columns.str.strip()
#     solved_paths = set(
#         solved_df[solved_df["Solved"] == True]["Task_Dir"].apply(lambda x: os.path.normpath(x))
#     )
# else:
#     print(f"⚠️ Summary file {summary_csv} not found.")
#     solved_paths = set()

# # Normalize and check against solved entries
# for seed, env, task, timestep in low_timestep_entries:
#     task_path = os.path.normpath(os.path.join(base_dir, seed, env, f"Task_{task}"))
#     if task_path in solved_paths:
#         done_list.append([seed, env, task, timestep])
#     else:
#         not_done_list.append([seed, env, task, timestep])

# # === Step 5: Save filtered CSV for remaining bugs
# with open(low_timestep_csv, "w", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(["Seed", "Environment", "Task", "Timestep_Count"])
#     writer.writerows(not_done_list)

# print(f"✅ Remaining (unsolved) low-timestep bugs saved to {low_timestep_csv}")
# print(f"✅ Total entries with timestep < 2000: {len(low_timestep_entries)}")
# print(f"✅ Already solved: {len(done_list)}")
# print(f"✅ Still to do: {len(not_done_list)}")

import os
import pandas as pd
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import csv

# === Parameters ===
csv_files = [
    "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_accurate.csv",
    "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_inaccurate_reward.csv",
    "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_inaccurate_state_and_reward.csv",
    "/scratch/projects/AIProbe-Main/Result/FlappyBird/20_seed_100_Bin_results/summary_inaccurate_state.csv"
]
base_dir = "/scratch/projects/AIProbe-Main/Result/FlappyBird/Flappybird/Approch_1/100_Bin"
summary_csv = "/scratch/projects/AIProbe-Main/AIProbe/Catcher_Flappy_Continuous/instruction_generation_summary.csv"
output_image = "bug_timestep_histogram.png"
low_timestep_csv = "low_timestep_bugs_new.csv"
solved_csv = "solved_new.csv"

# === Step 1: Load and intersect buggy paths ===
buggy_sets = []
row_maps = []

for file in csv_files:
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    buggy_df = df[df["BugFound"] == True].copy()
    buggy_df["Task_Dir"] = buggy_df.apply(
        lambda row: os.path.normpath(os.path.join(base_dir, str(row["Seed"]), row["Environment"], f"{row['Task']}")), axis=1
    )
    buggy_sets.append(set(buggy_df["Task_Dir"]))
    row_maps.append(buggy_df.set_index("Task_Dir"))

common_buggy_paths = sorted(set.intersection(*buggy_sets))
print(f"🧠 Found {len(common_buggy_paths)} common buggy task paths across all CSVs")

# === Step 2: Extract Timestep_Count and filter <2000 ===
timestep_list = []
low_timestep_rows = []

for path in common_buggy_paths:
    xml_path = os.path.join(path, "finalState.xml")
    if not os.path.exists(xml_path):
        print(f"⚠️ Missing: {xml_path}")
        continue

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        timestep_elem = next(
            (attr for attr in root.findall("Attribute")
             if attr.find("Name").get("value") == "Timestep_Count"),
            None
        )
        if timestep_elem is not None:
            timestep = int(timestep_elem.find("Value").get("value"))
            timestep_list.append(timestep)

            if timestep < 2000:
                ref_row = row_maps[0].loc[path].copy()
                ref_row["Timestep_Count"] = timestep
                ref_row["Task_Dir"] = path
                low_timestep_rows.append(ref_row)
        else:
            print(f"❌ Timestep_Count not found in {xml_path}")
    except Exception as e:
        print(f"❌ Failed to parse {xml_path}: {e}")

# === Step 3: Histogram ===
if timestep_list:
    plt.figure(figsize=(10, 6))
    plt.hist(timestep_list, bins=50, edgecolor='black')
    plt.xlabel("Timestep at crash (Timestep_Count)")
    plt.ylabel("Number of Bugs")
    plt.title("Bug Count Distribution by Timestep (Common Bugs Only)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_image)
    print(f"✅ Histogram saved to {output_image}")
else:
    print("No valid timesteps collected. Nothing to plot.")

# === Step 4: Check solved ===
if os.path.exists(summary_csv):
    solved_df = pd.read_csv(summary_csv)
    solved_df.columns = solved_df.columns.str.strip()
    solved_paths = set(
        solved_df[solved_df["Solved"] == True]["Task_Dir"].apply(lambda x: os.path.normpath(x))
    )
else:
    print(f"⚠️ Summary file {summary_csv} not found.")
    solved_paths = set()

# Separate into solved / unsolved
solved_rows = []
unsolved_rows = []

for row in low_timestep_rows:
    if row["Task_Dir"] in solved_paths:
        solved_rows.append(row)
    else:
        unsolved_rows.append(row)

# === Step 5: Save files ===
# === Step 5: Save files ===
# Save solved.csv with full rows
df_unsolved = pd.DataFrame(unsolved_rows)  # full info
df_unsolved_sorted = df_unsolved.sort_values(by="Timestep_Count")
df_unsolved_sorted[["Seed", "Environment", "Task"]].to_csv(low_timestep_csv, index=False)
print(f"✅ Unsolved low-timestep entries (for re-use) saved to {low_timestep_csv}")

# Save only paths to low_timestep_bugs.csv (unsolved and sorted)
df_unsolved = pd.DataFrame(unsolved_rows)
df_unsorted_paths = df_unsolved[["Task_Dir", "Timestep_Count"]].sort_values(by="Timestep_Count")
df_unsorted_paths["Task_Dir"].to_csv(low_timestep_csv, index=False, header=False)
print(f"✅ Unsolved low-timestep paths saved to {low_timestep_csv}")

# === Final Stats ===
print(f"📉 Total with timestep < 2000: {len(low_timestep_rows)}")
print(f"✅ Already solved: {len(solved_rows)}")
print(f"🚧 Still to do: {len(unsolved_rows)}")