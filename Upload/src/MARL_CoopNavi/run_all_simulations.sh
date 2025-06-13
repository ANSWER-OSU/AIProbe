#!/bin/bash

# Path to your Python simulation script
PYTHON_SCRIPT="/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/maddpg/experiments/test_aiprobe_parallely_for_buggy_models.py"

# List of bin folders you want to use as base_folder values in the Python script
PARENT_DIRS=(
    "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/20_seed/5_Bin"
    "/scratch/projects/AIProbe-Main/Result/MARL_Coop_Navi/20_seed/10_Bin"
)

# Backup the original Python file (optional)
cp "$PYTHON_SCRIPT" "${PYTHON_SCRIPT}.bak"

for DIR in "${PARENT_DIRS[@]}"; do
    echo "🔁 Setting base_folder to: $DIR"

    # Write to a temporary file then move it back
    sed 's/^\([[:space:]]*\)base_folder = ".*"/\1base_folder = "'"$DIR"'"|' "$PYTHON_SCRIPT" > tmp.py
    mv tmp.py "$PYTHON_SCRIPT"

    # Verify that the line has been updated
    echo "🔍 New base_folder line in script:"
    grep 'base_folder =' "$PYTHON_SCRIPT"

    # Ensure that the base folder exists (create if missing)
    mkdir -p "$DIR"

    echo "🚀 Running simulations in: $DIR"
    python "$PYTHON_SCRIPT"

    echo "✅ Finished: $DIR"
    echo "---------------------------------------------"
done

echo "🏁 All simulation batches complete!"