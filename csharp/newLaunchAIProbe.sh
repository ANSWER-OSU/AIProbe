/home/mehtara/miniconda3/bin/condai#!/bin/bash

# The purpose of this script is to launch AIProbe on multiple 
# environment configurations using multiple seeds sequentially.
# input: none
# output: results and logs produced by AIProbe at locations set
# in the AIProbeConfig.xml file
# how to run: bash launchAIProbe.sh

export AIPROBE_HOME=/home/projects/AIProbe/csharp
export PYTHON_HOME=/home/projects/miniconda3/envs/aiprobe/bin/python
cp AIprobeConfig.xml ./bin/Debug/net8.0/
cd ./bin/Debug/net8.0/

launchAIProbe() {
    seed=$1
    envnum=$2
    prevenvnum=$((envnum - 1))

    echo "Seed: $seed"
    echo "EnvNum: $envnum"
    echo "PrevEnvNum: $prevenvnum"

    echo "sed -i 's/8030/'$seed'/g' AIprobeConfig.xml"
    sed -i 's/8030/'$seed'/g' AIprobeConfig.xml
    sleep 5
    if [ "$prevenvnum" -ne 0 ]; then
        echo "Running sed to replace AiConfig.xml file"
        echo "sed -i 's/LavaEnv'$prevenvnum'/LavaEnv'$envnum'/g' AIprobeConfig.xml" 
        sed -i 's/LavaEnv'$prevenvnum'/LavaEnv'$envnum'/g' AIprobeConfig.xml
        echo "timeout 6h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log &" 
        timeout 6h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log &
    else
        echo "Launching AIProbe on the first env"
        echo "timeout 6h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log &" 
        timeout 6h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log &
    fi
    sleep 5
}

# Define your seeds (only 6470 is being used in this example)
seeds=(6161)

# Iterate over the seeds and environments sequentially
for seed in "${seeds[@]}"; do
    echo "Seed: $seed"
    for envnum in $(seq 1 13); do
        echo "Env#: $envnum"
        launchAIProbe $seed $envnum
    done
done

exit
~    
