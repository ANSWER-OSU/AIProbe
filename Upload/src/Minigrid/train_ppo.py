import gymnasium as gym
from stable_baselines3 import PPO
from MinigridEnv import CustomMiniGridEnv  # Replace 'Minigrid' with your actual file/module name
import xml.etree.ElementTree as ET
from stable_baselines3.common.env_util import make_vec_env

# ---------- Parse XML ----------
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

inaccuracy_type = 0  # or 1/2/3 depending on what you want to test
accurate_model = (inaccuracy_type == 0)

import copy

def make_env():
    # ---------- Paths ----------

    initial_xml_path = "/scratch/projects/AIProbe-Main/test_lava/98765/Env_91/Task_000/initialState.xml"
    final_xml_path   = "/scratch/projects/AIProbe-Main/test_lava/98765/Env_91/Task_000/finalState.xml"

    # ---------- Define environment ----------
    env_data = parse_xml_to_dict(initial_xml_path)
    goal_data = parse_xml_to_dict(final_xml_path)
    env_data_copy = copy.deepcopy(env_data)
    goal_data_copy = copy.deepcopy(goal_data)
    goal_x = int(goal_data_copy['Agents']['AgentList'][0]['Attributes'][0]['Value']['Content'])
    goal_y = int(goal_data_copy['Agents']['AgentList'][0]['Attributes'][1]['Value']['Content'])
    goal_dir = int(goal_data_copy['Agents']['AgentList'][0]['Attributes'][2]['Value']['Content'])
    goal_pos = (goal_x, goal_y)

    return CustomMiniGridEnv(
        environment_data=env_data_copy,
        accurate_model=accurate_model,
        task='escLava',
        inaccuracy_type=inaccuracy_type,
        goal_pos=goal_pos,
        goal_dir=goal_dir
    )



# ---------- Vectorized env ----------
vec_env = make_vec_env(lambda: make_env(), n_envs=4)

# ---------- Train ----------
model = PPO("MlpPolicy", vec_env, verbose=1, ent_coef=0.5, gamma=0.95, n_steps=2048, batch_size=64, learning_rate=0.0003, n_epochs=10)
model.learn(total_timesteps=1000000)

# ---------- Save ----------
model.save("ppo_models/acc_model")
print("✅ Model trained and saved.")
