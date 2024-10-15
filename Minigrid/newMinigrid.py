import os
import xml.etree.ElementTree as ET
import sys
import json

import pygame
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.grid import Grid
from minigrid.core.world_object import Wall, Lava, Goal, Ball
from minigrid.core.actions import Actions
from minigrid.core.mission import MissionSpace
from PIL import Image
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"


class Attribute:
    def __init__(self, name, data_type, value, min_val, max_val, step, mutable, description=None, value_list=None):
        self.name = name
        self.data_type = data_type
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.mutable = mutable
        self.description = description
        self.value_list = value_list


class Agent:
    def __init__(self, agent_id, name, agent_type, position, direction):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.position = position
        self.direction = direction


class Object:
    def __init__(self, object_id, name, obj_type, position, object_attributes):
        self.object_id = object_id
        self.name = name
        self.obj_type = obj_type
        self.position = position
        self.object_attributes = object_attributes


class Environment:
    def __init__(self, name, env_type, agents, objects, properties):
        self.name = name
        self.env_type = env_type
        self.agents = agents
        self.objects = objects
        self.properties = properties


# Parse attribute from XML
def parse_attribute(attribute_node):
    name = attribute_node.find('Name').get('value')
    data_type = attribute_node.find('DataType').get('value')
    value = attribute_node.find('Value').get('value')

    # Safely check if Min, Max, Step exist
    min_val = attribute_node.find('Min').get('value') if attribute_node.find('Min') is not None else None
    max_val = attribute_node.find('Max').get('value') if attribute_node.find('Max') is not None else None
    step = attribute_node.find('Step').get('value') if attribute_node.find('Step') is not None else None
    mutable = attribute_node.find('Mutable').get('value') if attribute_node.find('Mutable') is not None else None
    description = attribute_node.find('Description').get('value') if attribute_node.find('Description') is not None else None

    # Parse value list if available
    value_list = None
    if attribute_node.find('ValueList') is not None:
        value_list = {pair.get('key'): pair.get('value') for pair in attribute_node.find('ValueList').findall('Pair')}

    return Attribute(name, data_type, value, min_val, max_val, step, mutable, description, value_list)


# Parse agent from XML
def parse_agent(agent_node):
    agent_id = agent_node.get('id')
    name = agent_node.get('name')
    agent_type = agent_node.get('type')

    position = [parse_attribute(attr) for attr in agent_node.find('Position').findall('Attribute')]
    direction = [parse_attribute(attr) for attr in agent_node.find('Direction').findall('Attribute')]

    return Agent(agent_id, name, agent_type, position, direction)


# Parse object from XML
def parse_object(object_node):
    object_id = object_node.get('id')
    name = object_node.get('name')
    obj_type = object_node.get('type')

    position = [parse_attribute(attr) for attr in object_node.find('Position').findall('Attribute')]
    object_attributes = [parse_attribute(attr) for attr in object_node.find('ObjectAttributes').findall('Attribute')]

    return Object(object_id, name, obj_type, position, object_attributes)


# Parse environmental properties from XML
def parse_environment_property(property_node):
    name = property_node.get('name')
    attributes = [parse_attribute(attr) for attr in property_node.findall('Attribute')]

    return {'name': name, 'attributes': attributes}


# Parse the entire environment XML
def parse_environment(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Parse environment attributes
    env_name = root.get('name')
    env_type = root.get('type')

    # Parse agents
    agents = [parse_agent(agent_node) for agent_node in root.find('Agents').findall('Agent')]

    # Parse objects
    objects = [parse_object(object_node) for object_node in root.find('Objects').findall('Object')]

    # Parse environmental properties
    properties = [parse_environment_property(prop_node) for prop_node in root.find('EnvironmentalProperties').findall('Property')]

    return Environment(env_name, env_type, agents, objects, properties)


# Custom environment based on the parsed XML data
class CustomMiniGridEnv(MiniGridEnv):
    def __init__(self, environment_data, **kwargs):
        # Extract grid size from XML file's EnvironmentalProperties (Boundary width/height)
        boundary = next(prop for prop in environment_data.properties if prop['name'] == 'Boundary')
        grid_width = int(boundary['attributes'][0].value)  # Width
        grid_height = int(boundary['attributes'][1].value)  # Height

        # Make sure to pass only one value for grid_size (assuming the grid is square)
        assert grid_width == grid_height, "Grid width and height must be the same for MiniGridEnv"

        # Initialize the mission space and grid size based on the XML data
        mission_space = MissionSpace(mission_func=lambda: "Reach the goal while avoiding obstacles")
        super().__init__(grid_size=grid_width, mission_space=mission_space, **kwargs)

        # Save the environment data for later use
        self.environment_data = environment_data

    def _gen_grid(self, width, height):
        # Create an empty grid and set boundaries
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        # Place walls, landmines, and other objects based on the parsed XML data
        for obj in self.environment_data.objects:
            self.add_object_to_grid(obj)

        # Set agent's initial position
        agent = self.environment_data.agents[0]
        x_pos = int(agent.position[0].value)
        y_pos = int(agent.position[1].value)
        self.agent_pos = (x_pos, y_pos)

        # Set agent direction (convert angle to MiniGrid's direction)
        direction = int(agent.direction[0].value) //90
        self.agent_dir = direction  # Convert degrees to grid directions (0: East, 1: South, etc.)

    def add_object_to_grid(self, obj):
        # Extract the object's position
        x = int(obj.position[0].value)
        y = int(obj.position[1].value)

        # Add objects like walls and landmines based on the parsed XML data
        if obj.name == "Wall":
            self.grid.set(x, y, Wall())
        elif obj.name == "Lava":
            self.grid.set(x, y, Lava())  # You can customize the landmine object further if needed
        elif obj.name == "Goal":
            self.grid.set(x, y, Goal())  # Set goal object
        elif obj.name == "Ball":
            self.grid.set(x, y, Ball())

    def step(self, action):
        # Step through the environment and capture the results
        result = super().step(action)

        # Unpack the first four values (obs, reward, done, info) and ignore any extras
        obs, reward, done, info, *extra = result

        # Handle landmine (Lava) condition
        if isinstance(self.grid.get(*self.agent_pos), Lava):
            done = True
            reward = -1

        return obs, reward, done, info


# Map the action string to MiniGrid actions
def map_user_input_to_action(user_input):
    action_map = {
        'forward': Actions.forward,
        'left': Actions.left,
        'right': Actions.right,
        'pickup': Actions.pickup,
        'drop': Actions.drop,
        'toggle': Actions.toggle
    }
    return action_map.get(user_input, None)


# Run the environment using a list of predefined actions
def run_minigrid_with_action_list(xml_parsed_data, action_list):
    env = CustomMiniGridEnv(environment_data=xml_parsed_data)
    obs = env.reset()

    done = False
    for user_input in action_list:
        if done:
            print("The environment is finished (either goal reached or landmine hit).")
            break

        # Map the action from the list
        action = map_user_input_to_action(user_input)
        if action is None:
            print(f"Invalid action: {user_input}. Skipping...")
            continue

        # Perform the action in the environment
        obs, reward, done, info = env.step(action)

    return xml_parsed_data  # Return the updated environment data


# Convert Attribute object to XML element
def attribute_to_xml(attribute):
    attr_elem = ET.Element("Attribute")
    ET.SubElement(attr_elem, "Name").set("value", attribute.name)
    ET.SubElement(attr_elem, "DataType").set("value", attribute.data_type)
    ET.SubElement(attr_elem, "Value").set("value", attribute.value)
    if attribute.min_val:
        ET.SubElement(attr_elem, "Min").set("value", attribute.min_val)
    if attribute.max_val:
        ET.SubElement(attr_elem, "Max").set("value", attribute.max_val)
    if attribute.step:
        ET.SubElement(attr_elem, "Step").set("value", attribute.step)
    if attribute.mutable:
        ET.SubElement(attr_elem, "Mutable").set("value", attribute.mutable)
    if attribute.description:
        ET.SubElement(attr_elem, "Description").set("value", attribute.description)
    if attribute.value_list:
        value_list_elem = ET.SubElement(attr_elem, "ValueList")
        for key, value in attribute.value_list.items():
            pair_elem = ET.SubElement(value_list_elem, "Pair")
            pair_elem.set("key", key)
            pair_elem.set("value", value)
    return attr_elem


# Convert Agent object to XML element
def agent_to_xml(agent):
    agent_elem = ET.Element("Agent")
    agent_elem.set("id", agent.agent_id)
    agent_elem.set("name", agent.name)
    agent_elem.set("type", agent.agent_type)
    position_elem = ET.SubElement(agent_elem, "Position")
    for attr in agent.position:
        position_elem.append(attribute_to_xml(attr))
    direction_elem = ET.SubElement(agent_elem, "Direction")
    for attr in agent.direction:
        direction_elem.append(attribute_to_xml(attr))
    return agent_elem


# Convert Object object to XML element
def object_to_xml(obj):
    obj_elem = ET.Element("Object")
    obj_elem.set("id", obj.object_id)
    obj_elem.set("name", obj.name)
    obj_elem.set("type", obj.obj_type)
    position_elem = ET.SubElement(obj_elem, "Position")
    for attr in obj.position:
        position_elem.append(attribute_to_xml(attr))
    object_attributes_elem = ET.SubElement(obj_elem, "ObjectAttributes")
    for attr in obj.object_attributes:
        object_attributes_elem.append(attribute_to_xml(attr))
    return obj_elem


# Convert EnvironmentalProperties back to XML
def property_to_xml(prop):
    prop_elem = ET.Element("Property")
    prop_elem.set("name", prop['name'])
    for attr in prop['attributes']:
        prop_elem.append(attribute_to_xml(attr))
    return prop_elem


# Convert the entire Environment object to XML
def environment_to_xml(environment):
    root = ET.Element("Environment")
    root.set("name", environment.name)
    root.set("type", environment.env_type)

    # Add Agents
    agents_elem = ET.SubElement(root, "Agents")
    for agent in environment.agents:
        agents_elem.append(agent_to_xml(agent))

    # Add Objects
    objects_elem = ET.SubElement(root, "Objects")
    for obj in environment.objects:
        objects_elem.append(object_to_xml(obj))

    # Add EnvironmentalProperties
    properties_elem = ET.SubElement(root, "EnvironmentalProperties")
    for prop in environment.properties:
        properties_elem.append(property_to_xml(prop))

    tree = ET.ElementTree(root)
    return tree


# Save the updated environment to an XML file
def save_environment_to_xml(environment, file_path):
    tree = environment_to_xml(environment)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)


# Run the environment using a single action
def run_minigrid_with_single_actions(xml_parsed_data, action):
    env = CustomMiniGridEnv(environment_data=xml_parsed_data)
    obs = env.reset()

    done = False

    if done:
        print("The environment is finished (either goal reached or landmine hit).")
    else:
        env.render()

        # Map the single action from the argument
        mapped_action = map_user_input_to_action(action)
        if mapped_action is None:
            print(f"Invalid action: {action}. Skipping...")
        else:
            # Perform the action in the environment
            result = env.step(mapped_action)

            # Unpack the required values (obs, reward, done, info) and ignore any extras
            if len(result) == 4:
                obs, reward, done, info = result
            else:
                obs, reward, done, info, *extra = result  # Capturing extra values (if any)

            print(f"Action: {action}, Reward: {reward}, Done: {done}")

    env.close()

    # Return the updated environment data (you can modify this logic as needed)
    return xml_parsed_data



# Run the environment using a single action
def run_minigrid_with_single_action(environment_data, action):
    # Create the custom MiniGrid environment
    env = CustomMiniGridEnv(environment_data=environment_data)
    env.reset()

    # Map action from the input to MiniGrid action
    mapped_action = map_user_input_to_action(action)

    # Step through the environment with the mapped action
    obs, reward, done, info = env.step(mapped_action)

    agent = environment_data.agents[0]  # Assuming there's only one agent
    agent.position[0].value = str(env.agent_pos[0])  # Update X position
    agent.position[1].value = str(env.agent_pos[1])  # Update Y position
    agent.direction[0].value = str(env.agent_dir * 90)  # Update direction (0: East, 90: South, 180: West, 270: North)

    # Close environment after execution
    env.close()

    # Return the updated environment data (as an XML object)
    return environment_data



def main():
    # Get the file path to the XML file and the single action from command-line arguments
    xml_file = sys.argv[1]  # Input XML file path
    action = sys.argv[2]  # Single action to perform
    output_xml_file = sys.argv[3]  # Temporary output file path

    #xml_file = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/LavaEnv.xml" # Input XML file path
    #action = "forward"  # Single action to perform
    #output_xml_file = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/TempLavaEnv.xml"  # Temporary output file path

    # Parse the environment from the XML file
    environment_data = parse_environment(xml_file)

    # Run the environment with the provided single action
    updated_environment_data = run_minigrid_with_single_action(environment_data, action)

    # Save the updated environment data to the output XML file
    save_environment_to_xml(updated_environment_data, output_xml_file)


    # Print the file path for C# to retrieve
    print(output_xml_file)







if __name__ == "__main__":
    main()
