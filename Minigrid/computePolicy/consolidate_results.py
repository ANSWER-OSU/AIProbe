import os
import pandas as pd

# Define folder containing the CSV files
folder_path = "/home/projects/AIProbe/Minigrid/computePolicy/results_for_fuzzer_gen_configs"

# Define the mapping of filenames to agent types
agent_mapping = {
    "accurate_reward_accurate_state_rep": "Accurate_agent",
    "accurate_reward_inaccurate_state_rep": "Buggy_agent_1",
    "inaccurate_reward_accurate_state_rep": "Buggy_agent_2",
    "inaccurate_reward_inaccurate_state_rep": "Buggy_agent_3"
}

# Dictionary to store consolidated data
consolidated_data = {}

# Process each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        # Extract agent type key from the filename
        key = filename.split("Env_")[1].split(".csv")[0].split("_", 1)[1]  # Extract part after 'Env_X_'

        # Ensure the extracted key matches one in agent_mapping
        agent_type = agent_mapping.get(key)
        if agent_type is None:
            continue  # Skip if filename pattern doesn't match

        # Read the CSV file
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)

        print(file_path)
        # Iterate through rows and consolidate data
        for _, row in df.iterrows():
            env, seed, task = int(row[" Env#"]), int(row["Seed"]), int(row[" Task#"])
            agent_to_goal = row[" #AgentToGoal"]

            # Use (Env#, Seed, Task#) as a unique key
            unique_key = (int(env), int(seed), int(task))
            if unique_key not in consolidated_data:
                consolidated_data[unique_key] = {"Env#": env, "Seed": seed, "Task#": task,
                                                 "Buggy_agent_1": 0, "Buggy_agent_2": 0,
                                                 "Buggy_agent_3": 0, "Accurate_agent": 0}

            # Mark 1 if agent reached the goal, otherwise keep 0
            consolidated_data[unique_key][agent_type] = int(agent_to_goal)

# Convert dictionary to DataFrame
final_df = pd.DataFrame(consolidated_data.values())

# Save to CSV
final_df.to_csv("consolidated_data.csv", index=False)

print("Consolidation complete. File saved as 'consolidated_data.csv'.")
