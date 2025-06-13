import os
import xml.etree.ElementTree as ET
import sys
from math import trunc

import numpy as np
import pygame
from PIL import Image

import MinigridEnv


# Wrapper Code


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
import xml.dom.minidom


# Save the updated environment to an XML file
import xml.dom.minidom
import re

# Save the updated environment to an XML file
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

    # Convert the tree to a string
    xml_str = ET.tostring(tree.getroot(), encoding="utf-8", method="xml").decode('utf-8')

    # Add space before self-closing tags "/>"
    xml_str = re.sub(r'(?<!\s)/>', r' />', xml_str)  # ensures space before self-closing tags

    # Use xml.dom.minidom for pretty printing the XML
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml_as_str = dom.toprettyxml(indent="  ")

    # Remove extra newlines introduced by toprettyxml()
    pretty_xml_as_str = re.sub(r'\n\s*\n', r'\n', pretty_xml_as_str)

    # Write the formatted XML to the output file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml_as_str)

# Run the environment using a single action
def run_minigrid_with_single_actions(xml_parsed_data, action):
    env = MinigridEnv.CustomMiniGridEnv(environment_data=xml_parsed_data)
    obs = env.reset()

    done = False

    
    env.render()

        # Map the single action from the argument
    mapped_action = MinigridEnv.map_user_input_to_action(action)
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


     
    for agent in xml_parsed_data['Agents']['AgentList']:
        if 'Attributes' in agent:
            # Update X position
            if len(agent['Attributes']) > 0:
                agent['Attributes'][0]['Value']['Content'] = str(env.agent_pos[0])  # X position
            # Update Y position
            if len(agent['Attributes']) > 1:
                agent['Attributes'][1]['Value']['Content'] = str(env.agent_pos[1])  # Y position
            # Update direction (angle)
            if len(agent['Attributes']) > 2:
                agent['Attributes'][2]['Value']['Content'] = str(env.agent_dir)  # Direction (angle)
    if isinstance(env.grid.get(*env.agent_pos), MinigridEnv.Lava):
       # print("Condition: unsafe (Agent starting on Lava tile)")
        env.close()  # Make sure to close the environment
        return xml_parsed_data, True

    env.close()

    # Return the updated environment data (you can modify this logic as needed)
    return xml_parsed_data , False



# Run the environment using a single action
#def run_minigrid_with_single_action(environment_data, action):
    # Create the custom MiniGrid environment
    # env = MinigridEnv.CustomMiniGridEnv(environment_data=environment_data)
    # env.reset()

    # if isinstance(env.grid.get(*env.agent_pos), MinigridEnv.Lava):
    #     #print("Condition: unsafe (Agent starting on Lava tile)")
    #     env.close()  # Make sure to close the environment
    #     return environment_data, False

    #     # Map action from the input to MiniGrid action
    # mapped_action = MinigridEnv.map_user_input_to_action(action)

    # # Step through the environment with the mapped action
    # obs, reward, terminated, info = env.step(mapped_action)

    # #new_enviroment_data = getEnvFromCustomMiniGridEnv(env,environment_data)
    # # Update the agent's position and direction in the environment_data
    # for agent in environment_data['Agents']['AgentList']:
    #     if 'Attributes' in agent:
    #         # Update X position
    #         if len(agent['Attributes']) > 0:
    #             agent['Attributes'][0]['Value']['Content'] = str(env.agent_pos[0])  # X position
    #         # Update Y position
    #         if len(agent['Attributes']) > 1:
    #             agent['Attributes'][1]['Value']['Content'] = str(env.agent_pos[1])  # Y position
    #         # Update direction (angle)
    #         if len(agent['Attributes']) > 2:
    #             agent['Attributes'][2]['Value']['Content'] = str(env.agent_dir)  # Direction (angle)

    # Save the environment image after performing the action
    #save_minigrid_image(env, "minigrid_after_action.png")

    # if isinstance(env.grid.get(*env.agent_pos), MinigridEnv.Lava):
    #    # print("Condition: unsafe (Agent starting on Lava tile)")
    #     env.close()  # Make sure to close the environment
    #     return environment_data, True

    # # Close environment after execution
    # env.close()

    # # Return the updated environment data (as an XML object)
    # return environment_data , terminated ,



def run_minigrid_with_single_action(env, environment_data, action):
    # Step through the existing environment with the mapped action
    mapped_action = MinigridEnv.map_user_input_to_action(action)
    obs, reward, terminated, info = env.step(mapped_action)

    # Update the agent's position and direction in the environment_data
    for agent in environment_data['Agents']['AgentList']:
        if 'Attributes' in agent:
            if len(agent['Attributes']) > 0:
                agent['Attributes'][0]['Value']['Content'] = str(env.agent_pos[0])  # X position
            if len(agent['Attributes']) > 1:
                agent['Attributes'][1]['Value']['Content'] = str(env.agent_pos[1])  # Y position
            if len(agent['Attributes']) > 2:
                agent['Attributes'][2]['Value']['Content'] = str(env.agent_dir)  # Direction

    return environment_data, terminated

def getEnvFromCustomMiniGridEnv(env, environment_data):

    # Update agents
    # Update agents
    for i, agent in enumerate(environment_data['Agents']['AgentList']):
        # Ensure the agent has a 'position' attribute with at least two entries
        if 'Attributes' in agent:
            # Update X and Y positions
            if len(agent['Attributes']) > 0:
                agent['Attributes'][0]['Value'] = str(env.agent_pos[0])  # X position
            if len(agent['Attributes']) > 1:
                agent['Attributes'][1]['Value'] = str(env.agent_pos[1])  # Y position

            # Update direction (assuming it exists and maps to agent direction)
            if len(agent['Attributes']) > 2:
                agent['Attributes'][2]['Value'] = str(env.agent_dir)


    # Update objects



    if hasattr(env, 'env_properties'):
        for i, prop in enumerate(environment_data.properties):
            if i < len(env.env_properties):
                prop.value = str(env.env_properties[i])

    # Return the updated environment data
    return environment_data


def main():
    # Get the file path to the XML file and the single action from command-line arguments
    xml_file = sys.argv[1]  # Input XML file path
    action = sys.argv[2]  # Single action to perform
    output_xml_file = sys.argv[3]  # Temporary output file path

    #xml_file = "/Users/rahil/Documents/GitHub/AIProbe/csharp/results/Result_LavaEnv6_8030/Task_22/initialState.xml" # Input XML file path
    #action = "forward"  # Single action to perform
    #output_xml_file = "/Users/rahil/Documents/GitHub/AIProbe/csharp/Xml FIles/outputTEMPLava.xml"  # Temporary output file path

    #if os.path.exists(output_xml_file): os.remove(output_xml_file)

    environment_data = parse_environment(xml_file)

    # Parse the environment from the XML file
    agent_updated_position, agent_direction = get_agent_position(environment_data)
    print(f"Agent's Updated Position: X={agent_updated_position['X']}, Y={agent_updated_position['Y']}, Z={agent_updated_position['Z']}, Direction={agent_direction} degrees")

    # Run the environment with the provided single action
    updated_environment_data, terminated = run_minigrid_with_single_action(environment_data, action)
    if(terminated):
        print("Condition: unsafe")
    else:
        print("Condition: safe")
    # Get the updated agent's position and direction after action
    agent_updated_position, agent_direction = get_agent_position(updated_environment_data)
    print(f"Agent's Updated Position: X={agent_updated_position['X']}, Y={agent_updated_position['Y']}, Z={agent_updated_position['Z']}, Direction={agent_direction} degrees")

    # Save the updated environment data to the output XML file
    save_environment_to_xml(updated_environment_data, output_xml_file)

    # Print the file path for C# to retrieve
    #print(output_xml_file)

def get_agent_position(environment_data):
    """Extracts and returns the agent's position and direction from the environment data."""
    agent = environment_data.agents[0]  # Access the first agent

    # Assuming `Position` is a list of `Attribute` objects
    position_attributes = agent.position  # Get the list of position attributes

    # Assuming `Direction` is a list of `Attribute` objects
    direction_attributes = agent.direction  # Get the list of direction attributes

    # Now extract X, Y, Z from the position attributes list
    position = {
        'X': int(position_attributes[0].value),  # Assuming first attribute corresponds to X
        'Y': int(position_attributes[1].value),  # Assuming second attribute corresponds to Y
        'Z': int(position_attributes[2].value)   # Assuming third attribute corresponds to Z
    }

    # Extract direction index and convert it to the corresponding cardinal direction (East, South, West, North)
    direction_index = int(direction_attributes[0].value)  # Get the direction index
    direction_str = direction_index_to_direction(direction_index)  # Convert index to direction name

    return position, direction_str

# Helper function to convert direction index to direction name
def direction_index_to_direction(direction_index):
    # Map MiniGrid's direction indices 0, 1, 2, 3 to cardinal directions
    index_map = {
        0: "south",  # 0 corresponds to East
        1: "West", # 1 corresponds to South
        2: "North",  # 2 corresponds to West
        3: "East"  # 3 corresponds to North
    }
    return index_map.get(direction_index, "Unknown")  # Default to "Unknown" if index is invalid


import redis
import json

def print_value_tags(environment):
    if isinstance(environment, dict):
        for key, value in environment.items():
            if key == 'Value':  # Check if the key is 'Value'
                print(f"Value: {value}")
            else:
                print_value_tags(value)  # Recursively check deeper structures
    elif isinstance(environment, list):
        for item in environment:
            print_value_tags(item)

def process_environment_with_action(environment, action):
    # Example: Apply the action to the environment
    # Modify environment state based on the action
    #print("Initial Environment State:")
    #print_value_tags(environment)
    safe_condition = True  # Set based on your logic

    environment_data, terminated =     run_minigrid_with_single_action(environment, action)

    #print("final Environment State:")
    #print_value_tags(environment)
    return environment, terminated

# def run_with_redis():
#     r = redis.Redis(host='localhost', port=6379, decode_responses=True)
#     while True:
#         if r.exists("environment:payload"):
#             payload = json.loads(r.get("environment:payload"))

#             if "Environment" not in payload or "Action" not in payload:
#                 raise KeyError("Payload is missing required keys: 'Environment' or 'Action'")

#             environment = payload["Environment"]
#             action = payload["Action"]

#             # Process environment and action
#             updated_environment, terminated = process_environment_with_action(environment, action)

#             if(terminated):
#                 safe_condition = False
#             else:
#                 safe_condition = True

#             result = {
#                 "UpdatedEnvironment": updated_environment,
#                 "SafeCondition": safe_condition
#             }
#             r.set("environment:result", json.dumps(result))
#             r.delete("environment:payload")


# if __name__ == "__main__":
#     run_with_redis()


##if __name__ == "__main__":
    ##main()
