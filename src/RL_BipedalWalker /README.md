## 1. Environment installation
```
conda env create -f RLWalkEnv.yml
conda activate RLWalkEnv
```

## 2. Task generator
Use the provided run.sh script to generate environment and task files.
```
cd ..
cd Enviroment_Generation/publish
./run.sh <DomainName> <Master_XML_path> <TimeStepPresent>
cd ../..
cd BipedalWalker
```

Example:

```
./run.sh BipedalWalker ./data/BipedalWalker.xml true
```

This will:
    - Generate XML files (initial and final state)
    - Create output under AIprobe/Result/BipedalWalker/

## 3. Run model on generated task
This script simulation and runs the model on all generated tasks

```

```

## 4. Crash analysis
This script analyzes simulation results to identify no of tasks the model failed due to crashes and the unique states.
```
python crash_summary.py --csv_path /path/to/simulation/results --base_dir /path/to/genrated/task
```
