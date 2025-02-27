import json
import hashlib
import time
from collections import deque
from environment_parser import parse_environment , ActionSpace
from environment_parser import Environment
from ACAS_XU.environment import env
import copy
import heapq
import time
import copy
import  os
from collections import defaultdict
class InstructionChecker:

    def compute_environment_hash(self, environment: Environment) -> str:
        """Generate a unique hash for an environment state."""
        environment_dict = environment.to_dict()  # Convert to serializable dictionary
        return hashlib.sha256(json.dumps(environment_dict, sort_keys=True).encode()).hexdigest()

    # def instruction_exists(self, initial_env, action_space, time_limit, initial_hash, final_hash):
    #     """Main logic for instruction generation."""
    #     start_time = time.time()
    #     instruction_exists = False
    #     results = []
    #
    #     instruction_dict = {}
    #     completed_actions = {}
    #     env_queue = deque([initial_env])
    #
    #     while time.time() - start_time < time_limit:
    #         if len(env_queue) == 0:
    #             print("queue empty")
    #             break
    #         current_env = env_queue.popleft()
    #         current_env_hash = self.compute_environment_hash(current_env)
    #
    #         if current_env_hash == final_hash:
    #             if final_hash in instruction_dict:
    #                 results.append((" -> ".join(instruction_dict[final_hash]), "Safe"))
    #                 instruction_exists = True
    #                 break
    #
    #         remaining_actions = self.get_remaining_actions(current_env_hash, action_space, completed_actions)
    #
    #
    #
    #         for action in remaining_actions:
    #             updated_env, safe = self.call_python_wrapper_with_redis(current_env, action)
    #             updated_env_hash = self.compute_environment_hash(updated_env)
    #
    #
    #             for attr in updated_env.attributes:
    #                 if attr.name.value == 'Timestep_Count' and attr.value.content == 3425 :
    #                     instruction_dict[updated_env_hash] = instruction_dict.get(current_env_hash, []) + [action]
    #                     results.append((" -> ".join(instruction_dict[updated_env_hash]), "Safe"))
    #
    #             if updated_env_hash == final_hash and safe:
    #                 instruction_exists = True
    #                 instruction_dict[updated_env_hash] = instruction_dict.get(current_env_hash, []) + [action]
    #                 results.append((" -> ".join(instruction_dict[updated_env_hash]), "Safe"))
    #                 break
    #
    #             if updated_env_hash not in instruction_dict:
    #                 instruction_dict[updated_env_hash] = instruction_dict.get(current_env_hash, []) + [action]
    #                 if safe:
    #                     results.append((" -> ".join(instruction_dict[updated_env_hash]), "Unreched_Safe"))
    #                     env_queue.append(updated_env)
    #                 else:
    #                     results.append((" -> ".join(instruction_dict[updated_env_hash]), "Unsafe"))
    #
    #     return results, instruction_exists
    #



    def instruction_exists(self, initial_env, action_space, time_limit, initial_hash, final_hash):
        """Improved BFS for balanced instruction generation."""
        start_time = time.time()
        instruction_exists = False
        results = []

        # Store multiple paths per state hash
        instruction_dict = {}
        completed_actions = {}
        env_queue = deque([(initial_env, [])])  # Queue stores (environment, action_path)

        while time.time() - start_time < time_limit:
            if not env_queue:
                print("Queue empty. No more environments to process.")
                break

            # Dequeue environment and action path
            current_env, action_path = env_queue.popleft()
            current_env_hash = self.compute_environment_hash(current_env)

            # Check if current environment matches final state
            if current_env_hash == final_hash:
                print(f"Final environment state reached with path: {' -> '.join(map(str, action_path))}")
                results.append((" -> ".join(map(str, action_path)), "Safe"))
                instruction_exists = True
                continue  # Do not break; collect all solutions

            # Get remaining actions for current state
            remaining_actions = self.get_remaining_actions(current_env_hash, action_space, completed_actions)

            for action in remaining_actions:
                # Execute action and compute updated state
                updated_environment = copy.deepcopy(current_env)
                updated_env, safe = self.call_python_wrapper_with_redis(updated_environment, action)
                updated_env_hash = self.compute_environment_hash(updated_env)
                new_action_path = action_path + [action]

                # Check for Timestep_Count condition
                for attr in updated_env.attributes:
                    if attr.name.value == 'Timestep_Count' and int(attr.value.content) == 3425:
                        print(f"Target timestep reached with path: {' -> '.join(map(str, new_action_path))}")
                        results.append((" -> ".join(map(str, new_action_path)), "Safe"))
                        instruction_exists = True

                # Track multiple paths for each state hash
                if updated_env_hash not in instruction_dict:
                    instruction_dict[updated_env_hash] = []
                instruction_dict[updated_env_hash].append(new_action_path)

                # Explore safe paths further
                if safe:
                    env_queue.append((updated_env, new_action_path))
                    results.append((" -> ".join(map(str, new_action_path)), "Unreached_Safe"))
                else:
                    results.append((" -> ".join(map(str, new_action_path)), "Unsafe"))

        end_time = time.time()
        print(f"\nExecution completed in {end_time - start_time:.2f} seconds.")
        return results, instruction_exists

    def instruction_exists_aStar(self, initial_env, action_space, time_limit, initial_hash, final_hash):
        """Improved A* for balanced instruction generation, exploring all solutions."""
        start_time = time.time()
        results = []

        # Priority queue for A*: (f(n), g(n), env, action_path)
        env_queue = []

        heapq.heappush(env_queue, (0, 0, initial_env, []))

        # Store best known cost to each state
        g_cost = {initial_hash: 0}
        completed_actions = {}

        while time.time() - start_time < time_limit:
            if not env_queue:
                print("Priority queue empty. No more environments to process.")
                break

            # Dequeue environment with lowest f(n)
            _, g_current, current_env, action_path = heapq.heappop(env_queue)
            current_env_hash = self.compute_environment_hash(current_env)

            # Check if current environment matches final state
            if current_env_hash == final_hash:
                print(f"Final environment state reached with path: {' -> '.join(map(str, action_path))}")
                results.append((" -> ".join(map(str, action_path)), "Safe"))
                # Do NOT break here; continue to explore other solutions

            # Check for Timestep_Count condition
            current_timestep = next(
                (int(attr.value.content) for attr in current_env.attributes if attr.name.value == 'Timestep_Count'),
                None)
            if current_timestep == 3425:
                print(f"Target timestep reached with path: {' -> '.join(map(str, action_path))}")
                results.append((" -> ".join(map(str, action_path)), "Safe"))
                # Continue exploring other solutions

            # Get remaining actions for current state
            remaining_actions = self.get_remaining_actions(current_env_hash, action_space, completed_actions)

            for action in remaining_actions:
                # Execute action and compute updated state
                updated_environment = copy.deepcopy(current_env)
                updated_env, safe = self.call_python_wrapper_with_redis(updated_environment, action)
                updated_env_hash = self.compute_environment_hash(updated_env)
                new_action_path = action_path + [action]

                # Calculate costs
                # Calculate costs
                g_new = g_current + 1  # Path cost (each step = 1)
                h_new = self.heuristic(updated_env, new_action_path)  # Pass action_path
                f_new = g_new + h_new

                # Update if new path is better or explore other paths
                if updated_env_hash not in g_cost or g_new < g_cost[updated_env_hash]:
                    g_cost[updated_env_hash] = g_new
                    heapq.heappush(env_queue, (f_new, g_new, updated_env, new_action_path))

                    if safe:
                        results.append((" -> ".join(map(str, new_action_path)), "Unreached_Safe"))
                    else:
                        results.append((" -> ".join(map(str, new_action_path)), "Unsafe"))

        end_time = time.time()
        print(f"\nExecution completed in {end_time - start_time:.2f} seconds.")
        return results, len(results) > 0

    # Example heuristic function
    def heuristic(self, env, action_path):
        """Estimate cost based on Timestep_Count and action diversity."""
        timestep = next((int(attr.value.content) for attr in env.attributes if attr.name.value == 'Timestep_Count'),
                        None)
        if timestep is None:
            return float('inf')

        # Encourage diversity: Penalize repeated '0' actions.
        repeated_action_penalty = action_path.count('0') * 10

        # Heuristic: Distance to target timestep + action diversity penalty
        return abs(3425 - timestep) + repeated_action_penalty

    def instruction_exists_dfs(self, initial_env, action_space, time_limit, initial_hash, final_hash):
        """Improved DFS for balanced instruction generation with action order control."""
        start_time = time.time()
        instruction_exists = False
        results = []

        # Store multiple paths per state hash
        instruction_dict = {}
        completed_actions = {}

        # Use a stack instead of a queue for DFS
        env_stack = [(initial_env, [])]  # Stack stores (environment, action_path)

        while time.time() - start_time < time_limit:
            if not env_stack:
                print("Stack empty. No more environments to process.")
                break

            # Pop environment and action path (DFS uses LIFO)
            current_env, action_path = env_stack.pop()
            current_env_hash = self.compute_environment_hash(current_env)

            # Check if current environment matches final state
            if current_env_hash == final_hash:
                print(f"Final environment state reached with path: {' -> '.join(map(str, action_path))}")
                results.append((" -> ".join(map(str, action_path)), "Safe"))
                instruction_exists = True
                continue  # Collect all solutions

            # Get remaining actions for current state
            remaining_actions = self.get_remaining_actions(current_env_hash, action_space, completed_actions)

            # Reverse action order to prioritize lower actions first (0, 1, 2, 3, 4)
            for action in reversed(remaining_actions):
                # Execute action and compute updated state
                updated_environment = copy.deepcopy(current_env)
                updated_env, safe = self.call_python_wrapper_with_redis(updated_environment, action)
                updated_env_hash = self.compute_environment_hash(updated_env)
                new_action_path = action_path + [action]

                # Check for Timestep_Count condition
                for attr in updated_env.attributes:
                    if attr.name.value == 'Timestep_Count' and int(attr.value.content) == 3425:
                        print(f"Target timestep reached with path: {' -> '.join(map(str, new_action_path))}")
                        results.append((" -> ".join(map(str, new_action_path)), "Safe"))
                        instruction_exists = True

                # Track multiple paths for each state hash
                if updated_env_hash not in instruction_dict:
                    instruction_dict[updated_env_hash] = []
                instruction_dict[updated_env_hash].append(new_action_path)

                # Explore safe paths further (LIFO for DFS)
                if safe:
                    env_stack.append((updated_env, new_action_path))
                    print(new_action_path)
                    results.append((" -> ".join(map(str, new_action_path)), "Unreached_Safe"))
                else:
                    results.append((" -> ".join(map(str, new_action_path)), "Unsafe"))

        end_time = time.time()
        print(f"\nExecution completed in {end_time - start_time:.2f} seconds.")
        return results, instruction_exists

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
            setting='inaccurate_state'
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



    def instruction_exists_with_json(self, initial_env, action_space, time_limit, initial_hash, final_hash, final_env,
                                     folder_name):
        """Improved BFS for balanced instruction generation."""
        start_time = time.time()
        instruction_exists = False
        output_file = os.path.join(folder_name, "instruction_results.json")
        timestep = 0
        for attr in final_env.attributes:
            if attr.name.value == 'Timestep_Count':
                timestep = int(attr.value.content)
                print(f"Timestep : {timestep} folder : {folder_name}")

        # Ensure the JSON file exists
        if not os.path.exists(output_file):
            with open(output_file, "w") as json_file:
                json.dump([], json_file, indent=4)

        # Store multiple paths per state hash
        instruction_dict = {}
        completed_actions = {}
        env_queue = deque([(initial_env, [])])  # Queue stores (environment, action_path)
        final_result = "Not Found"

        while time.time() - start_time < time_limit:
            if not env_queue:
                print("Queue empty. No more environments to process.")
                final_result = "Eplored all"
                break
            # Dequeue environment and action path
            current_env, action_path = env_queue.popleft()
            current_env_hash = self.compute_environment_hash(current_env)

            # Check if current environment matches final state
            if current_env_hash == final_hash:
                new_result = {"instructions": " -> ".join(map(str, action_path)), "condition": "Safe"}
                self.append_to_json(output_file, new_result)
                instruction_exists = True
                continue

            # Get remaining actions for current state
            remaining_actions = self.get_remaining_actions(current_env_hash, action_space, completed_actions)

            Found_unsafe = False
            for action in remaining_actions:
                # Execute action and compute updated state
                updated_environment = copy.deepcopy(current_env)
                updated_env, safe = self.call_python_wrapper_with_redis(updated_environment, action)
                updated_env_hash = self.compute_environment_hash(updated_env)
                new_action_path = action_path + [action]

                # Check for Timestep_Count condition
                for attr in updated_env.attributes:
                    if attr.name.value == 'Timestep_Count' and int(attr.value.content) == timestep:
                        new_result = {"instructions": " -> ".join(map(str, new_action_path)), "condition": "Safe"}
                        self.append_to_json(output_file, new_result)
                        final_result = "Safe"
                        instruction_exists = True
                        break

                # Track multiple paths for each state hash
                if updated_env_hash not in instruction_dict:
                    instruction_dict[updated_env_hash] = []
                instruction_dict[updated_env_hash].append(new_action_path)

                # Explore safe paths further
                condition = "Unreached_Safe" if safe else "Unsafe"
                new_result = {"instructions": " -> ".join(map(str, new_action_path)), "condition": condition}
                self.append_to_json(output_file, new_result)

                if safe:
                    env_queue.append((updated_env, new_action_path))
                    if(Found_unsafe):
                        final_result = "Safe will exist"
                        instruction_exists = True
                        break
                else:
                    Found_unsafe = True



        end_time = time.time()
        #self.log_result(folder_name, initial_env.name, final_env.name, "Completed", final_result,{end_time - start_time})
        print(f"\nExecution completed in {end_time - start_time:.2f} seconds.")
        return instruction_exists

    def append_to_json(self, filename, data):

        """Append a single result to the JSON file without loading the entire file into memory."""
        with open(filename, "r+") as json_file:
            try:
                # Move to the end of the JSON array and append
                json_file.seek(0, os.SEEK_END)
                pos = json_file.tell()
                if pos > 2:
                    json_file.seek(pos - 2)
                    json_file.write(",\n")
                else:
                    json_file.write("[\n")

                # Write the new result
                json.dump(data, json_file, indent=4)
                json_file.write("\n]")


            except json.JSONDecodeError:
                # If the file is empty or corrupted, start fresh
                with open(filename, "w") as fresh_file:
                    json.dump([data], fresh_file, indent=4)


def main(initial_xml_path,final_xml_path):

    # Parse initial and final environment states
    with open(initial_xml_path, "r") as file:
        initial_xml_data = file.read()

    with open(final_xml_path, "r") as file:
        final_xml_data = file.read()

    initial_env = parse_environment(initial_xml_data)
    final_env = parse_environment(final_xml_data)
    folder_path = os.path.dirname(initial_xml_path)
    # Define action space
    # "Action 0: Maintain current heading",
    # "Action 1: Turn left by 1.5° per time interval",
    # "Action 2: Turn right by 1.5° per time interval",
    # "Action 3: Turn left by 3° per time interval",
    # "Action 4: Turn right by 3° per time interval"
    action_space = ActionSpace(actions=[1, 2,3,4])

    # Initialize and run InstructionChecker
    checker = InstructionChecker()
    initial_hash = checker.compute_environment_hash(initial_env)
    final_hash = checker.compute_environment_hash(final_env)

    #results, exists = checker.instruction_exists(initial_env, action_space, 7200, initial_hash, final_hash)
    exists = checker.instruction_exists_with_json(initial_env, action_space, 1800, initial_hash, final_hash, final_env,folder_path)
    #exists = checker.instruction_exists_with_json(initial_env, action_space, 7200, initial_hash, final_hash)
    #results, exists = checker.instruction_exists_aStar(initial_env, action_space, 600, initial_hash, final_hash)
    #results, exists = checker.instruction_exists_dfs(initial_env, action_space, 600, initial_hash, final_hash)

    # Save results to JSON
    # output_data = {
    #     "exists": exists,
    #     "results": [{"instructions": result[0], "condition": result[1]} for result in results]
    # }
    #
    # # Write to JSON file
    # output_file = "instruction_results.json"
    # with open(output_file, "w") as json_file:
    #     json.dump(output_data, json_file, indent=4)

    # Display results
    if exists:
        print("Instruction set found:")
    else:
        print("No valid instruction set found.")


if __name__ == '__main__':

    # Example XML input path
    main("/Volumes/External_ssd/Data/Task_147/initialState.xml", "/Volumes/External_ssd/Data/Task_147/finalState.xml")

