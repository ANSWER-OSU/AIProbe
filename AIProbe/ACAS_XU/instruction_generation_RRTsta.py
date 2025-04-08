import json
import hashlib
import time
import os
import copy
import random
import math

from sympy import false

from environment_parser import parse_environment, ActionSpace
from environment_parser import Environment
from ACAS_XU.environment import env


import json
import hashlib
import time
import os
import copy
import random
import math

from environment_parser import parse_environment, ActionSpace
from environment_parser import Environment
from ACAS_XU.environment import env


class Node:
    """Represents a node in the RRT* tree."""
    def __init__(self, env, action_path=None, parent=None):
        self.env = env
        self.action_path = action_path if action_path else []
        self.parent = parent
        self.cost = 0  # Path cost from start
        self.survival_time = 0  # Track survival time


class InstructionChecker:
    def __init__(self):
        self.tree = []
        self.goal_timesteps = 13
        self.step_size = 10
        self.unsafe_actions = []
        self.safe_paths = []
        self.explored_states = set()
        self.neighbor_radius = 50  # For rewiring step

    def compute_environment_hash(self, environment):
        """Generate a unique hash for an environment state, ignoring Timestep_Count."""
        environment_dict = environment.to_dict()
        return hashlib.sha256(json.dumps(environment_dict, sort_keys=True).encode()).hexdigest()

    def rrt_star_survival(self, initial_env, action_space, time_limit, initial_hash, folder_name):
        """True RRT* implementation for survival."""
        start_time = time.time()
        instruction_exists = False
        output_file = os.path.join(folder_name, "instruction_results_rrt_survival.json")

        # Ensure the JSON file exists
        if not os.path.exists(output_file):
            with open(output_file, "w") as json_file:
                json.dump([], json_file, indent=4)

        root = Node(initial_env)
        root.survival_time = 0  # Starts with 0 timesteps
        root.action_path = []
        self.tree.append(root)
        best_survival_node = root

        while time.time() - start_time < time_limit:
            # 🌟 Sample a new state (random or goal-biased)
            random_node = random.choice(self.tree)  # Sample from already explored nodes
            sampled_env = self.sample_environment(random_node.env)  #
            #sampled_env = self.sample_environment(initial_env)

            # Find the nearest node in the tree
            nearest_node = self.get_nearest_node(sampled_env)

            # Get all possible new nodes from the nearest node
            new_nodes = self.steer(nearest_node, sampled_env, action_space)

            for new_node, safe, action_taken in new_nodes:
                env_hash = self.compute_environment_hash(new_node.env)

                if env_hash in self.explored_states:
                    continue  # Skip if already explored

                self.explored_states.add(env_hash)

                # 🌟 Find the best parent (rewiring step)
                best_parent = nearest_node
                best_cost = best_parent.cost + 1  # Default cost

                neighbors = self.get_nearby_nodes(new_node, self.neighbor_radius)
                for neighbor in neighbors:
                    potential_cost = neighbor.cost + 1  # Distance = 1 step
                    if potential_cost < best_cost:
                        best_parent = neighbor
                        best_cost = potential_cost

                new_node.parent = best_parent
                new_node.cost = best_cost
                new_node.action_path = best_parent.action_path + [action_taken]
                self.tree.append(new_node)

                # Print explored state
                survival_time = len(new_node.action_path)
                print(f"🛠️ Explored state with action: {action_taken}")
                print(f"📍 Coordinates: {self.get_coordinates(new_node.env)}")
                print(f"⏳ Survival Time: {survival_time} timesteps")
                print(f"🎯 Action sequence for survival time {survival_time}: {' -> '.join(map(str, new_node.action_path))}\n")

                # If survival goal is reached, stop
                if survival_time >= self.goal_timesteps:
                    instruction_exists = True
                    best_survival_node = new_node
                    break

                if not safe:
                    self.unsafe_actions.append(action_taken)

        # Save the best survival path
        if best_survival_node:
            action_path = self.extract_path(best_survival_node)
            new_result = {
                "instructions": " -> ".join(map(str, action_path)),
                "condition": f"Survived for {best_survival_node.survival_time} timesteps"
            }
            self.safe_paths.append(new_result)
            self.append_to_json(output_file, new_result)

        end_time = time.time()
        print(f"\nExecution completed in {end_time - start_time:.2f} seconds.")
        return instruction_exists

    def steer(self, nearest_node, sampled_env, action_space):
        """Move from nearest node towards a sampled node, prioritizing survival."""
        new_nodes = []

        for action in action_space.actions:
            temp_env = copy.deepcopy(nearest_node.env)
            updated_env, safe = self.call_python_wrapper_with_redis(temp_env, action)
            survival_time = self.get_timestep_count(updated_env)

            new_action_path = nearest_node.action_path + [action]
            new_node = Node(updated_env, new_action_path, nearest_node)
            new_node.survival_time = survival_time

            new_nodes.append((new_node, safe, action))

        return new_nodes

    def get_nearby_nodes(self, new_node, radius):
        """Find nodes within a certain radius for rewiring in RRT*."""
        neighbors = []
        for node in self.tree:
            if self.compute_distance(node.env, new_node.env) < radius:
                neighbors.append(node)
        return neighbors

    def compute_distance(self, env1, env2):
        """Compute Euclidean distance between two states based on X, Y."""
        x1, y1 = self.get_coordinates(env1)
        x2, y2 = self.get_coordinates(env2)
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def get_coordinates(self, env):
        """Extract (x, y) coordinates from environment."""
        x = float(next((attr.value.content for attr in env.attributes if attr.name.value == 'X'), 0))
        y = float(next((attr.value.content for attr in env.attributes if attr.name.value == 'Y'), 0))
        return x, y

    def get_timestep_count(self, env):
        """Extract timestep count from the environment."""
        for attr in env.attributes:
            if attr.name.value == 'Timestep_Count':
                return int(attr.value.content)
        return 0

    def extract_path(self, best_survival_node):
        """Trace back the path from the best survival node to root."""
        path = []
        node = best_survival_node
        while node:
            if node.parent:
                path.append(node.action_path[-1])
            node = node.parent
        return path[::-1]

    def sample_environment(self, reference_env):
        """Generate a random state (or goal-biased) for sampling."""
        sampled_env = copy.deepcopy(reference_env)
        if random.random() < 0.2:  # 20% chance to bias towards goal
            return sampled_env  # Goal-biased sampling
        for attr in sampled_env.attributes:
            if attr.name.value in ['X', 'Y']:
                attr.value.content = str(random.uniform(-10000, 10000))
            elif attr.name.value == 'Theta':
                attr.value.content = str(random.uniform(-3.14, 3.14))
        return sampled_env

    def get_nearest_node(self, sampled_env):
        """Find the nearest node in the RRT* tree based on Euclidean distance (X, Y)."""
        min_dist = float('inf')
        nearest_node = None

        for node in self.tree:
            dist = self.compute_distance(node.env, sampled_env)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node

        return nearest_node

    def get_remaining_actions(self, env_hash, action_space, action_dict):
        if env_hash not in action_dict:
            action_dict[env_hash] = action_space.actions.copy()
        return action_dict[env_hash]




    def call_python_wrapper_with_redis(self, environment, action):
        """Create the ACAS environment dynamically based on the Environment object."""

        # Extract agent (ownship) attributes
        ownship = environment.agents.agent_list[0] if environment.agents.agent_list else None
        ownship_x = float(next((attr.value.content for attr in ownship.attributes if attr.name.value == 'X'), 0))
        ownship_y = float(next((attr.value.content for attr in ownship.attributes if attr.name.value == 'Y'), 0))
        ownship_theta = float(next((attr.value.content for attr in ownship.attributes if attr.name.value == 'Theta'), 0))
        acas_speed = float(next((attr.value.content for attr in ownship.attributes if attr.name.value == 'Ownship_Speed'), 200))

        # Extract intruder attributes
        intruder = environment.objects.object_list[0] if environment.objects.object_list else None
        intruder_x = float(next((attr.value.content for attr in intruder.attributes if attr.name.value == 'X'), 0))
        intruder_y = float(next((attr.value.content for attr in intruder.attributes if attr.name.value == 'Y'), 0))
        intruder_theta = float(next((attr.value.content for attr in intruder.attributes if attr.name.value == 'Auto_Theta'), 0))
        intruder_speed = float(
            next((attr.value.content for attr in intruder.attributes if attr.name.value == 'Intruder_Speed'), 200))

        # Initialize the ACAS environment using the extracted parameters
        air_env = env(
            ownship_x=ownship_x,
            ownship_y=ownship_y,
            ownship_theta=ownship_theta,
            acas_speed=acas_speed,
            intruder_x=intruder_x,
            intruder_y=intruder_y,
            intruder_theta=intruder_theta,
            intruder_speed=intruder_speed,
            setting='accurate'
        )

        # Execute the step based on the action and get the updated environment
        air_env.step_proof(action)

        # Create an updated environment object based on the new state
        updated_environment = Environment(
            name=environment.name,
            type=environment.type,
            agents=environment.agents,
            objects=environment.objects,
            attributes=environment.attributes
        )
        for attr in ownship.attributes:
            if attr.name.value == 'X':
                attr.value.content = str(air_env.ownship.x)
            elif attr.name.value == 'Y':
                attr.value.content = str(air_env.ownship.y)
            elif attr.name.value == 'Theta':
                attr.value.content = str(air_env.ownship.theta)
            elif attr.name.value == 'Ownship_Speed':
                attr.value.content = str(air_env.ownship.speed)

            # Update intruder attributes based on the new state
        for attr in intruder.attributes:
            if attr.name.value == 'X':
                attr.value.content = str(air_env.intruder.x)
            elif attr.name.value == 'Y':
                attr.value.content = str(air_env.intruder.y)
            elif attr.name.value == 'Auto_Theta':
                attr.value.content = str(air_env.intruder.theta)
            elif attr.name.value == 'Intruder_Speed':
                attr.value.content = str(air_env.intruder.speed)


        for attr in updated_environment.attributes:
            if attr.name.value == 'Timestep_Count':
                temp = int(attr.value.content)
                attr.value.content =temp+1

            # Check for collision or boundary termination
        safe_condition = not air_env.terminated

        return updated_environment, safe_condition




def main(initial_xml_path):
    """Main function to execute RRT* for survival."""
    with open(initial_xml_path, "r") as file:
        initial_xml_data = file.read()

    initial_env = parse_environment(initial_xml_data)
    folder_path = os.path.dirname(initial_xml_path)

    action_space = ActionSpace(actions=[1,2,3,4])

    checker = InstructionChecker()
    initial_hash = checker.compute_environment_hash(initial_env)

    exists = checker.rrt_star_survival(initial_env, action_space, 1800, initial_hash, folder_path)

    if exists:
        print("✅ Survival strategy found using RRT*!")
    else:
        print("❌ No valid survival strategy found.")


if __name__ == '__main__':
    main("/Volumes/External_ssd/Data/Task_147/initialState.xml")