#!/bin/bash
source /scratch/projects/miniconda3/bin/activate acas
python wrapper.py | tee -a output.txt
