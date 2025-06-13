import argparse
import numpy as np
import tensorflow as tf
import time
import pickle
import sys
import os

sys.path.append(os.path.abspath("/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/"))
from modify_env_test import *
import maddpg.common.tf_util as U
from maddpg.trainer.maddpg import MADDPGAgentTrainer
import tensorflow.contrib.layers as layers

def parse_args():
    parser = argparse.ArgumentParser("Reinforcement Learning experiments for multiagent environments")
    parser.add_argument("--scenario", type=str, default="simple_spread", help="name of the scenario script")
    parser.add_argument("--max-episode-len", type=int, default=25, help="maximum episode length")
    parser.add_argument("--num-episodes", type=int, default=60000, help="number of episodes")
    parser.add_argument("--num-adversaries", type=int, default=0, help="number of adversaries")
    parser.add_argument("--good-policy", type=str, default="maddpg", help="policy for good agents")
    parser.add_argument("--adv-policy", type=str, default="maddpg", help="policy of adversaries")
    parser.add_argument("--lr", type=float, default=1e-2, help="learning rate for Adam optimizer")
    parser.add_argument("--gamma", type=float, default=0.95, help="discount factor")
    parser.add_argument("--batch-size", type=int, default=128, help="number of episodes to optimize at the same time")
    parser.add_argument("--num-units", type=int, default=64, help="number of units in the MLP")
    parser.add_argument("--exp-name", type=str, default="default_experiment", help="name of the experiment")
    parser.add_argument("--save-dir", type=str, default="/scratch/projects/AIProbe-Main/AIProbe/MARL_CoopNavi/InaccurateModels/", help="directory to save models")
    parser.add_argument("--save-rate", type=int, default=100, help="save model every N episodes")
    parser.add_argument("--load-dir", type=str, default="", help="directory to load models from")
    parser.add_argument("--restore", action="store_true", default=False)
    return parser.parse_args()

def mlp_model(input, num_outputs, scope, reuse=False, num_units=64):
    with tf.compat.v1.variable_scope(scope, reuse=tf.compat.v1.AUTO_REUSE):
        print(f"[DEBUG] Input shape to MLP model: {input.shape}")
        out = layers.fully_connected(input, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_units, activation_fn=tf.nn.relu)
        out = layers.fully_connected(out, num_outputs=num_outputs, activation_fn=None)
        return out

def make_env(scenario_name):
    from multiagent.environment import MultiAgentEnv
    import multiagent.scenarios as scenarios

    scenario = scenarios.load(scenario_name + ".py").Scenario()
    world = scenario.make_world()
    env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation)
    return env

def get_trainers(env, num_adversaries, obs_shape_n, arglist):
    trainers = []
    model = mlp_model
    trainer = MADDPGAgentTrainer
    for i in range(env.n):
        trainers.append(trainer(
            f"agent_{i}", model, obs_shape_n, env.action_space, i, arglist,
            local_q_func=(arglist.adv_policy == 'ddpg' if i < num_adversaries else arglist.good_policy == 'ddpg')
        ))
    return trainers

def train(arglist, env):
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    tf.compat.v1.reset_default_graph()
    with U.single_threaded_session():
        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        config.gpu_options.per_process_gpu_memory_fraction = 0.5
        sess = tf.compat.v1.Session(config=config)
        tf.compat.v1.keras.backend.set_session(sess)
        U.initialize()
        tf.compat.v1.disable_eager_execution()
        tf.compat.v1.debugging.set_log_device_placement(False)


        obs_shape_n = [env.observation_space[i].shape for i in range(env.n)]
        num_adversaries = min(env.n, arglist.num_adversaries)
        trainers = get_trainers(env, num_adversaries, obs_shape_n, arglist)

        print(f"Using good policy: {arglist.good_policy}, adversary policy: {arglist.adv_policy}")

        # Initialize TensorFlow session
        U.initialize()

        if arglist.restore:
            print("Loading previous model...")
            U.load_state(arglist.load_dir)

        episode_rewards = []
        agent_rewards = [[0.0] for _ in range(env.n)]
        final_ep_rewards = []
        saver = tf.train.Saver()

        obs_n = env.reset()
        episode_step, train_step = 0, 0
        t_start = time.time()

        print("Starting training...")
        for ep in range(arglist.num_episodes):
            obs_n = env.reset()
            ep_reward = 0
            for _ in range(arglist.max_episode_len):
                actions = [agent.action(obs) for agent, obs in zip(trainers, obs_n)]
                new_obs_n, rew_n, done_n, _ = env.step(actions)

                for i, agent in enumerate(trainers):
                    agent.experience(obs_n[i], actions[i], rew_n[i], new_obs_n[i], done_n[i], False)

                obs_n = new_obs_n
                ep_reward += sum(rew_n)

                if all(done_n):
                    break

            episode_rewards.append(ep_reward)
            for i, rew in enumerate(rew_n):
                agent_rewards[i].append(rew)

            train_step += 1

            # Train agents
            for agent in trainers:
                agent.preupdate()
            for agent in trainers:
                agent.update(trainers, train_step)

            # Save model every `save_rate` episodes
            if ep % arglist.save_rate == 0:
                save_dir = os.path.join(arglist.save_dir, arglist.exp_name)  # Create subdirectory for the experiment
                checkpoint_dir = os.path.join(save_dir, "checkpoints")  # Separate folder for model checkpoints
                os.makedirs(checkpoint_dir, exist_ok=True)  # Ensure directory exists

                U.save_state(checkpoint_dir, saver=saver)  # Save TensorFlow model in checkpoint_dir

                # Save rewards file inside the experiment's folder
                with open(os.path.join(save_dir, f"{arglist.exp_name}_rewards.pkl"), 'wb') as fp:
                    pickle.dump(final_ep_rewards, fp)
                print(f"Episode {ep}: Avg Reward: {np.mean(episode_rewards[-arglist.save_rate:]):.3f}")

            final_ep_rewards.append(np.mean(episode_rewards[-arglist.save_rate:]))

        # Save final results
        with open(os.path.join(save_dir, f"{arglist.exp_name}_rewards.pkl"), 'wb') as fp:
            pickle.dump(final_ep_rewards, fp)

        print("Training complete!")

if __name__ == '__main__':
    arglist = parse_args()

    # Inaccurate state representation environment
    print("\nTraining on inaccurate state environment...")
    inaccurate_state_env = make_inaccurate_state_env(arglist.scenario)
    arglist.exp_name = "inaccurate_state"
    train(arglist, inaccurate_state_env)

    # Inaccurate reward model environment
    print("\nTraining on inaccurate reward environment...")
    inaccurate_reward_env = make_inaccurate_reward_env(arglist.scenario)
    arglist.exp_name = "inaccurate_reward"
    train(arglist, inaccurate_reward_env)

    # Inaccurate state & reward model environment
    print("\nTraining on inaccurate state & reward environment...")
    inaccurate_state_reward_env = make_inaccurate_state_reward_env(arglist.scenario)
    arglist.exp_name = "inaccurate_state_reward"
    train(arglist, inaccurate_state_reward_env)
