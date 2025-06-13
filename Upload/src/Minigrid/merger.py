import os
import pandas as pd

# ------ SETTINGS ------
base_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1/100_Bin/results_for_fuzzer_gen_configs"
target_filename = "_accurate_reward_accurate_state_rep_results.csv"
output_csv_path = os.path.join(base_dir, "merger.csv")
# ----------------------

# Empty list to collect all filtered DataFrames
all_filtered_rows = []

# Go through each Seed_* folder
for seed_folder in os.listdir(base_dir):
    seed_path = os.path.join(base_dir, seed_folder)
    if not os.path.isdir(seed_path):
        continue
    if not seed_folder.startswith("Seed_"):
        continue

    input_csv = os.path.join(seed_path, target_filename)

    if not os.path.exists(input_csv):
        print(f"⚠️ File not found: {input_csv}")
        continue

    try:
        # Read the CSV
        df = pd.read_csv(input_csv)

        # Filter rows where Env# <= 100 and Task# <= 100
        filtered_df = df[(df[" Env#"] <= 100) & (df[" Task#"] <= 100)]

        if not filtered_df.empty:
            all_filtered_rows.append(filtered_df)

    except Exception as e:
        print(f"❌ Error processing {input_csv}: {e}")

# After all folders are processed, merge everything
if all_filtered_rows:
    merged_df = pd.concat(all_filtered_rows, ignore_index=True)
    merged_df.to_csv(output_csv_path, index=False)
    print(f"✅ Merged file saved at: {output_csv_path}")
else:
    print("⚠️ No valid filtered data found.")