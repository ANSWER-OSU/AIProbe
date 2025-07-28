# AIProbe: Uncovering Systemic and Environment Errors in Autonomous Systems Using Differential Testing
**Full paper:** ["Uncovering Systemic and Environment Errors in Autonomous Systems Using Differential Testing"](https://www.arxiv.org/abs/2507.03870), Rahil P. Mehta<sup>\*</sup>, Yashwanthi Anand<sup>\*</sup>, Manish Motwani and Sandhya Saisubramanian.

AIProbe is a black-box testing framework for identifying and attributing execution anomalies in autonomous agents. It systematically generates diverse environment-task configurations and uses a search-based oracle planner to determine whether the anomaly stems from the agent's model or the environment itself.

AIProbe is designed to:

- Detect execution anomalies
- Attribute failures to agent errors or environment errors
- Work across discrete/continuous and single/multi-agent domains
- Operate in black-box settings with no access to the agent’s internal model or reward function

## Dependencies 

Dependencies include (but are not limited to):
```
gymnasium
numpy
scipy
matplotlib
tqdm
torch (for PPO models)
```
The domains we evaluate require additional installation. To install these requirements, `cd src/<DOMAIN_NAME>` and follow the environment installation instructions.

## Repository Contents

The source code for generating environment-task configurations and evaluating the planner and agent on these configurations are contained with `src/<DOMAIN_NAME>`. The domains includes [ACAS Xu](https://github.com/ANSWER-OSU/AIProbe/tree/main/src/ACAS_XU), [Coop Navi](https://github.com/ANSWER-OSU/AIProbe/tree/main/src/MARL_CoopNavi), [Bipedal Walker](https://github.com/ANSWER-OSU/AIProbe/tree/main/src/RL_BipedalWalker%20), [Flappy Bird](https://github.com/ANSWER-OSU/AIProbe/tree/main/src/Catcher_Flappy_Continuous), and [Lava](https://github.com/ANSWER-OSU/AIProbe/tree/main/src/Minigrid). 

Details of each environment and the instructions to run AIProbe on these domains are provided within the respective folders.

## License
This work is released under the Creative Commons Zero v1.0 Universal (CC0-1.0) license.




