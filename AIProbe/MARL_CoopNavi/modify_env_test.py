import sys
import os
sys.path.append(os.path.abspath("/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/multiagent_particle_envs"))
from multiagent.environment import MultiAgentEnv
from make_env import make_env
import numpy as np
from gym import spaces

'''
- observation space:[self_vel, self_pos, landmark_rel_positions, other_agent_rel_positions, communication]
    self_vel = [vel_in_x, vel_in_y]
    self_pos = [agent_x, agent_y]
    landmark_rel_positions = [(landmark1_x, landmark1_y), ..., (landmarkN_x, landmarkN_y)] # N is the no. of landmarks (= to no. of agents)
    other_agent_rel_positions = [(agent1_x, agent1_y), ..., (agentN-1_x, agentN-1_y)]
    communication = [comm_dim_1, comm_dim_2]

- action space: [no_action, move_left, move_right, move_down, move_up]

- By default there are 3 agents. Each can take 5 discrete actions
'''



class InaccurateStateEnv(MultiAgentEnv):
    def __init__(self, world, reset_callback, reward_callback, observation_callback):
        """ Initialize the inaccurate state environment """
        super().__init__(world, reset_callback, reward_callback, observation_callback)

        # Update observation space to reflect the new observation dimension
        self.observation_space = []
        for agent in self.agents:
            obs_dim = len(self._get_obs(agent))
            self.observation_space.append(spaces.Box(low=-np.inf, high=+np.inf, shape=(obs_dim,), dtype=np.float32))

    def _get_obs(self, agent):
        """ Override observation function to remove `other_agent_rel_positions` """
        entity_pos = [entity.state.p_pos - agent.state.p_pos for entity in self.world.landmarks]
        comm = [other.state.c for other in self.world.agents if other is not agent]

        # Remove other agents' positions
        return np.concatenate([agent.state.p_vel, agent.state.p_pos] + entity_pos + comm)

def make_inaccurate_state_env(scenario_name):
    env = make_env(scenario_name)
    return InaccurateStateEnv(env.world, env.reset_callback, env.reward_callback, env.observation_callback)

class InaccurateRewardEnv(MultiAgentEnv):
    def __init__(self, world, reset_callback, reward_callback, observation_callback):
        """ Initialize the inaccurate reward environment """
        super().__init__(world, reset_callback, reward_callback, observation_callback)

    def _get_reward(self, agent):
        """ Override reward function to remove collision penalties """
        rew = 0
        for landmark in self.world.landmarks:
            dists = [np.linalg.norm(a.state.p_pos - landmark.state.p_pos) for a in self.world.agents]
            rew -= min(dists)  # Keep the landmark distance-based reward

        return rew  # No collision penalty

def make_inaccurate_reward_env(scenario_name):
    env = make_env(scenario_name)
    return InaccurateRewardEnv(env.world, env.reset_callback, env.reward_callback, env.observation_callback)

class InaccurateStateRewardEnv(MultiAgentEnv):
    def __init__(self, world, reset_callback, reward_callback, observation_callback):
        """ Initialize the inaccurate state and reward environment """
        super().__init__(world, reset_callback, reward_callback, observation_callback)

        # Update observation space to reflect the new observation dimension
        self.observation_space = []
        for agent in self.agents:
            obs_dim = len(self._get_obs(agent))
            self.observation_space.append(spaces.Box(low=-np.inf, high=+np.inf, shape=(obs_dim,), dtype=np.float32))

    def _get_obs(self, agent):
        """ Override observation function to remove `other_agent_rel_positions` """
        entity_pos = [entity.state.p_pos - agent.state.p_pos for entity in self.world.landmarks]
        comm = [other.state.c for other in self.world.agents if other is not agent]

        # Remove other agents' positions
        return np.concatenate([agent.state.p_vel, agent.state.p_pos] + entity_pos + comm)

    def _get_reward(self, agent):
        """ Override reward function to remove collision penalties """
        rew = 0
        for landmark in self.world.landmarks:
            dists = [np.linalg.norm(a.state.p_pos - landmark.state.p_pos) for a in self.world.agents]
            rew -= min(dists)  # Keep the landmark distance-based reward

        return rew  # No collision penalty

def make_inaccurate_state_reward_env(scenario_name):
    env = make_env(scenario_name)
    return InaccurateStateRewardEnv(env.world, env.reset_callback, env.reward_callback, env.observation_callback)

if __name__ == '__main__':
    scenario = 'simple_spread'
    env = make_env(scenario)

    # Inaccurate state representation (removes other_agent_rel_positions)
    env_inaccurate_state = make_inaccurate_state_env(scenario)
    print("Original observation space:", env.observation_space)
    print("Inaccurate state observation space:", env_inaccurate_state.observation_space)

    # Inaccurate reward model (removes collision penalty)
    env_inaccurate_reward = make_inaccurate_reward_env(scenario)

    # Inaccurate state and reward model (both inaccuracies combined)
    env_inaccurate_state_reward = make_inaccurate_state_reward_env(scenario)
    print("Inaccurate state & reward observation space:", env_inaccurate_state_reward.observation_space)
