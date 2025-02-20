import os
import numpy as np
import tensorflow as tf
import maddpg.common.tf_util as U
from maddpg.trainer.maddpg import MADDPGAgentTester
import argparse
from multiagent.environment import MultiAgentEnv
import multiagent.scenarios as scenarios


def parse_args():
    """Parse arguments for running a trained RL agent."""
    parser = argparse.ArgumentParser("Run trained RL agent in simple environment")
    parser.add_argument("--scenario", type=str, default="simple", help="Scenario script name")
    parser.add_argument("--model-dir", type=str, default="../checkpoints/", help="Directory of the trained model")
    parser.add_argument("--max-episode-len", type=int, default=100, help="Maximum episode length")
    parser.add_argument("--num-units", type=int, default=64, help="Number of units in MLP")
    return parser.parse_args()


def make_env(scenario_name):
    """Load the scenario and create MultiAgentEnv, handling missing attributes."""
    scenario = scenarios.load(scenario_name + ".py").Scenario()
    world = scenario.make_world()

    # Ensure dim_c is positive before creating the environment
    if hasattr(world, "dim_c") and world.dim_c <= 0:
        world.dim_c = 1  # Ensure world.dim_c is always at least 1

    env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation)
    return env


def mlp_model(input, num_outputs, scope, reuse=False, num_units=64):
    """Defines a simple MLP model with names matching the checkpoint."""
    with tf.compat.v1.variable_scope(scope, reuse=reuse):
        out = tf.compat.v1.layers.dense(input, num_units, activation=tf.nn.relu, name="fully_connected")
        out = tf.compat.v1.layers.dense(out, num_units, activation=tf.nn.relu, name="fully_connected_1")
        out = tf.compat.v1.layers.dense(out, num_outputs, activation=None, name="fully_connected_2")
    return out



import os
import tensorflow as tf

def get_trained_agents(env, obs_shape_n, model_dir, args):
    """Load trained agents from the latest checkpoint."""
    trainers = []
    trainer = MADDPGAgentTester
    for i in range(env.n):
        trainers.append(trainer(
            "agent_%d" % i, mlp_model, obs_shape_n, env.action_space, i, args,
            local_q_func=False))

    U.initialize()


    # 🔹 Ensure model_dir is correct and exists
    model_dir = os.path.abspath(model_dir)  # Convert to absolute path

    # 🔹 Check if the checkpoint directory exists
    if not os.path.exists(model_dir):
        raise FileNotFoundError(f"❌ Model directory not found: {model_dir}. Ensure it exists.")

    # 🔹 Ensure the checkpoint file exists
    checkpoint = tf.train.latest_checkpoint(model_dir)
    if checkpoint is None:
        raise FileNotFoundError(f"❌ No checkpoint found in {model_dir}. Ensure you have trained and saved a model.")


    print(f"✅ Loading model from {checkpoint}")
    U.load_state(checkpoint, ignore_missing_vars=True)
    # Load the trained model
    return trainers



def run_episode(env, trainers, max_episode_len):
    """Run a single episode using the trained agents in the simple environment."""
    obs_n = env.reset()
    episode_reward = 0
    for step in range(max_episode_len):
        action_n = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]
        obs_n, rew_n, done_n, _ = env.step(action_n)
        episode_reward += sum(rew_n)
        if all(done_n):  # Stop if all agents are done
            break
    print(f"🎯 Episode finished with total reward: {episode_reward}")


if __name__ == '__main__':
    args = parse_args()  # Parse arguments
    env = make_env(args.scenario)  # Load the environment
    obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]  # Get observation shapes

    with U.single_threaded_session():
        trainers = get_trained_agents(env, obs_shape_n, args.model_dir, args)  # Load trained agents
        run_episode(env, trainers, args.max_episode_len)  # Run a single episode
