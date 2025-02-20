import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse
import tensorflow as tf

# ✅ Ensure TensorFlow 1.x compatibility
tf.compat.v1.disable_eager_execution()

from make_env import make_env
from maddpg.trainer.maddpg import MADDPGAgentTester
import maddpg.common.tf_util as U  # ✅ Ensure proper TensorFlow session management


# ✅ Global session variable to persist TensorFlow session
SESSION = None

def load_trained_agents(env, checkpoint_path, args):
    """ Load trained MADDPG agents from a saved model file """
    global SESSION
    obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
    act_space_n = [env.action_space[i] for i in range(env.n)]
    trained_agents = []

    # ✅ Ensure a single persistent session
    if SESSION is None:
        SESSION = U.single_threaded_session()
        SESSION.__enter__()
        U.initialize()  # ✅ Ensure variables are initialized

    # ✅ Load the trained model
    saver = tf.compat.v1.train.import_meta_graph(checkpoint_path + ".meta")
    saver.restore(SESSION, checkpoint_path)
    print("✅ Checkpoint loaded successfully!")

    if args is None:
        class DefaultArgs:
            num_units = 64  # Default number of units
        args = DefaultArgs()

    def mlp_model(input, num_outputs, scope, reuse=False, num_units=64):
        with tf.compat.v1.variable_scope(scope, reuse=reuse):
            out = input
            out = tf.compat.v1.layers.dense(out, num_units, activation=tf.nn.relu)
            out = tf.compat.v1.layers.dense(out, num_units, activation=tf.nn.relu)
            out = tf.compat.v1.layers.dense(out, num_outputs, activation=None)
            return out

    for i in range(env.n):
        agent = MADDPGAgentTester(
            name=f"agent_{i}",
            model=mlp_model,
            obs_shape_n=obs_shape_n,
            act_space_n=act_space_n,
            agent_index=i,
            args=args
        )
        trained_agents.append(agent)

    return trained_agents


def create_env(scenario_name, config_path=None, checkpoint_path=None, args=None):
    """ Initialize the environment and load trained MADDPG agents """
    env = make_env(scenario_name)  # ✅ Use make_env.py to create the environment
    trained_agents = load_trained_agents(env, checkpoint_path, args) if checkpoint_path else []
    print(f"✅ Environment created with {len(env.world.agents)} agents and {len(env.world.landmarks)} landmarks.")
    return env, trained_agents


def visualize_env(env, trained_agents, num_steps=50):
    """ Visualize agents and landmarks in real-time """
    global SESSION
    fig, ax = plt.subplots()

    agent_positions = [[] for _ in range(len(env.world.agents))]
    landmark_positions = [landmark.state.p_pos for landmark in env.world.landmarks]

    agent_scatter = ax.scatter([], [], c='blue', label="Agents")
    landmark_scatter = ax.scatter(*zip(*landmark_positions), c='red', marker='s', label="Landmarks")

    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_title("Multi-Agent Environment Visualization")
    ax.legend()

    def update(frame):
        """ Update function for animation using trained MADDPG model """
        global SESSION
        actions = []
        obs_n = env.reset()

        with SESSION.as_default():  # ✅ Ensure session is active
            for i, agent in enumerate(trained_agents):
                #obs_tensor = np.expand_dims(obs_n[i], axis=0)  # Ensure correct shape
                obs_tensor = np.array(obs_n[i], dtype=np.float32).reshape(1, -1)
                # ✅ Ensure action is computed within an active session
                sampled_action = agent.action(obs_tensor)[0]
                actions.append(sampled_action)

            obs_n, rewards, done, _ = env.step(actions)

        # Get agent and landmark positions
        agent_positions = [agent.state.p_pos for agent in env.world.agents]
        landmark_positions = [landmark.state.p_pos for landmark in env.world.landmarks]

        print(f"\n🔹 Step {frame + 1}/{num_steps}")
        reached_agents = set()

        for i, agent_pos in enumerate(agent_positions):
            for j, landmark_pos in enumerate(landmark_positions):
                distance = np.linalg.norm(agent_pos - landmark_pos)
                if distance < 0.05:
                    print(f"✅ Agent {i} has reached Landmark {j}!")
                    reached_agents.add(i)

        if len(reached_agents) == len(env.world.agents):
            print("🎉 All agents have reached landmarks! Stopping simulation.")
            plt.close()
            return

        agent_scatter.set_offsets(agent_positions)
        return agent_scatter,

    ani = animation.FuncAnimation(fig, update, frames=num_steps, repeat=False)
    plt.ion()
    plt.show(block=True)


def run_test(env, trained_agents, num_steps=50):
    """ Run the environment and visualize agent movement """
    visualize_env(env, trained_agents, num_steps)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MultiAgentEnv with Fixed Positions and Visualization")
    parser.add_argument("--scenario", type=str, default="simple_spread", help="Scenario name (default: simple_spread)")
    parser.add_argument("--steps", type=int, default=50, help="Number of steps to run (default: 50)")
    parser.add_argument("--config", type=str, help="Path to JSON config file with fixed positions")
    parser.add_argument("--load-dir", type=str, help="Path to trained model checkpoint")
    parser.add_argument("--num-units", type=int, default=64, help="Number of units in MLP network")

    args = parser.parse_args()

    env, trained_agents = create_env(args.scenario, args.config, args.load_dir, args)
    run_test(env, trained_agents, args.steps)
