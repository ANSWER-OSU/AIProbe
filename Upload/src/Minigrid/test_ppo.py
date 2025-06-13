import gymnasium as gym
import numpy as np
import pygame
from stable_baselines3 import PPO
from MinigridEnv import CustomMiniGridEnv  # Replace with your actual file name
import xml.etree.ElementTree as ET
import time

# ---------- XML Parsing ----------
def parse_xml_to_dict(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    def parse_attr(attr):
        return {
            'Name': {'Value': attr.find('Name').get('value')},
            'DataType': {'Value': attr.find('DataType').get('value')},
            'Value': {'Content': attr.find('Value').get('value')},
            'Mutable': {'Value': attr.find('Mutable').get('value') == "true"} if attr.find('Mutable') is not None else None,
            'Constraint': {
                'Min': attr.find('Constraint').get('Min') if attr.find('Constraint') is not None else None,
                'Max': attr.find('Constraint').get('Max') if attr.find('Constraint') is not None else None
            }
        }

    data = {
        'Name': root.get('name'),
        'Type': root.get('type'),
        'Agents': {'AgentList': []},
        'Objects': {'ObjectList': []},
        'Attributes': [parse_attr(attr) for attr in root.findall('Attribute')]
    }

    for agent in root.findall('./Agents/Agent'):
        data['Agents']['AgentList'].append({
            'Id': int(agent.get('id')),
            'Type': agent.get('type'),
            'Attributes': [parse_attr(attr) for attr in agent.findall('Attribute')]
        })

    for obj in root.findall('./Objects/Object'):
        data['Objects']['ObjectList'].append({
            'Id': int(obj.get('id')),
            'Type': obj.get('type'),
            'Attributes': [parse_attr(attr) for attr in obj.findall('Attribute')]
        })

    return data

# ---------- Load Env ----------
initial_xml_path = "/scratch/projects/AIProbe-Main/test_lava/00000/Env_00/Task_000/initialState.xml"
final_xml_path   = "/scratch/projects/AIProbe-Main/test_lava/00000/Env_00/Task_000/finalState.xml"

env_data = parse_xml_to_dict(initial_xml_path)
goal_data = parse_xml_to_dict(final_xml_path)

goal_x = int(goal_data['Agents']['AgentList'][0]['Attributes'][0]['Value']['Content'])
goal_y = int(goal_data['Agents']['AgentList'][0]['Attributes'][1]['Value']['Content'])
goal_dir = int(goal_data['Agents']['AgentList'][0]['Attributes'][2]['Value']['Content'])
goal_pos = (goal_x, goal_y)

inaccuracy_type = 0
accurate_model = (inaccuracy_type == 0)

env = CustomMiniGridEnv(
    environment_data=env_data,
    accurate_model=accurate_model,
    task='escLava',
    inaccuracy_type=inaccuracy_type,
    goal_pos=goal_pos,
    goal_dir=goal_dir
)

# ---------- Load PPO Model ----------
model = PPO.load("/scratch/projects/AIProbe-Main/AIProbe/Minigrid/ppo_models/acc_model")

# ---------- Run Rollout ----------
obs, _ = env.reset()
done = False
terminated = False
truncated = False
total_reward = 0

for step in range(1000):
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    print(action)
    total_reward += reward

    # env.render()
    # time.sleep(0.1)

    if terminated or truncated:
        print(f"Episode finished after {step + 1} steps with total reward {total_reward}")
        break

env.close()
