#!/bin/bash

# The purpose of this script is to launch AIProbe on multiple 
# environment configurations using multiple seeds in parallel
# input: none
# output: results and logs produced by AIProbe at locations set
# in the AIProbeConfig.xml file
# how to run: bash launchAIProbe.sh
#


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
	echo "timeout 1h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log &" 
	timeout 3h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log & 
    else
        echo "Launching AIProbe on the first env"
	echo "timeout 1h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log &" 
	timeout 3h dotnet AIprobe.dll > output_lava"$envnum"_"$seed".log & 
    fi
    sleep 5

}


seeds=(9957 1092)
#seeds=(8030 9957 1092 6470 734 329 2503 1041 9264 6161)

export -f launchAIProbe

parallel --joblog parallel.log -j 20 'launchAIProbe {1} {2}' ::: "${seeds[@]}" ::: $(seq 1 13)

exit 


# Iterate over the seeds
for seed in "${seeds[@]}"; do
    echo "Seed: $seed"
    for envnum in $(seq 1 13); do
	echo "Env#: $envnum"
	launchAIProbe $seed $envnum
    done
done

