import os

# Base directory
base_dir = "/scratch/projects/AIProbe-Main/Result/LavaRoom/Approch_1/100_Bin"

# Counter for initialState.xml files
initial_state_count = 0

# Walk through the Seed folders
for seed_folder in os.listdir(base_dir):
    seed_path = os.path.join(base_dir, seed_folder)
    if os.path.isdir(seed_path):
        for env_folder in os.listdir(seed_path):
            env_path = os.path.join(seed_path, env_folder)
            if os.path.isdir(env_path):
                for task_folder in os.listdir(env_path):
                    task_path = os.path.join(env_path, task_folder)
                    if os.path.isdir(task_path):
                        initial_state_file = os.path.join(task_path, "initialState.xml")
                        if os.path.exists(initial_state_file):
                            initial_state_count += 1

print(f"✅ Total initialState.xml files found: {initial_state_count}")