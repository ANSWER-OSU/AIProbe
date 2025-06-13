import pandas as pd

# === Step 1: Provide CSV paths manually ===
csv_paths = [
    "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/mereges result /inacurate_reward/inaccurate_reward_results.csv",
    "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/mereges result /inacurate_reward/inaccurate_reward_results (3).csv",
    "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/mereges result /inacurate_reward/inaccurate_reward_results (2).csv",
    "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/mereges result /inacurate_reward/inaccurate_reward_results (1).csv"
    #,"/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/mereges result /basemodel/accurate_model4.csv"
    # Add more paths as needed
]

# === Step 2: Load and concatenate ===
df_list = []
for path in csv_paths:
    try:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        df_list.append(df)
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")

if not df_list:
    print("⚠️ No valid CSVs found. Check file paths.")
    exit()

# === Step 3: Merge and deduplicate ===
merged_df = pd.concat(df_list, ignore_index=True)
dedup_df = merged_df.drop_duplicates()

# === Step 4: Save result ===
output_path = "merged_output.csv"
dedup_df.to_csv(output_path, index=False)
print(f"✅ Merged and deduplicated CSV saved to: {output_path}")