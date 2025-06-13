import pandas as pd
import os
import pickle

# Path to your CSV file
csv_file_path = "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/Approch_1/100_Bin/inaccurate_reward_results.csv"  # 🔁 Replace with actual CSV path

# Dynamically get the base directory (same dir as CSV)
base_dir = os.path.dirname(csv_file_path)

# Read the CSV with headers
df = pd.read_csv(csv_file_path)

# Ensure 'BugFound' is treated as boolean (in case it's read as string)
df["BugFound"] = df["BugFound"].astype(str).str.lower() == "true"

# Filter rows where BugFound is True
bug_rows = df[df["BugFound"] == True]

# Process each bugged row
for _, row in bug_rows.iterrows():
    seed = row["Seed"]
    env = row["Environment"]
    task = row["Task"]
    bin_type = row["Bin"]

    # Build path relative to the CSV directory
    pkl_path = os.path.join(base_dir, str(seed), env, task, "accurate_data.pkl")
    print("Looking for:", pkl_path)

    # Try to load the .pkl file
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
            print(data)
        print("✅ Pickle file loaded.")
    except FileNotFoundError:
        print("❌ Pickle file NOT found at:", pkl_path)
    except Exception as e:
        print("⚠️ Error loading pickle file:", e)