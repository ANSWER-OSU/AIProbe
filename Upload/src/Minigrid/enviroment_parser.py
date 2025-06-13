
import xml.etree.ElementTree as ET


def parse_xml_to_dict(xml_file):
    """Parses an XML file and returns a structured dictionary."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    env_dict = {
        'Name': root.get('name'),
        'Type': root.get('type'),
        'Agents': {'AgentList': []},
        'Objects': {'ObjectList': []},
        'Attributes': []
    }

    def parse_attribute(attr_node):
        return {
            'Name': {'Value': attr_node.find('Name').get('value')},
            'DataType': {'Value': attr_node.find('DataType').get('value')},
            'Value': {'Content': attr_node.find('Value').get('value')},
            'Mutable': {'Value': attr_node.find('Mutable').get('value') == "true"} if attr_node.find(
                'Mutable') is not None else None,
            'Constraint': {
                'Min': attr_node.find('Constraint').get('Min') if attr_node.find('Constraint') is not None else None,
                'Max': attr_node.find('Constraint').get('Max') if attr_node.find('Constraint') is not None else None
            }
        }

    agents_node = root.find('Agents')
    if agents_node is not None:
        for agent in agents_node.findall('Agent'):
            agent_dict = {
                'Id': int(agent.get('id')),
                'Type': agent.get('type'),
                'Attributes': [parse_attribute(attr) for attr in agent.findall('Attribute')]
            }
            env_dict['Agents']['AgentList'].append(agent_dict)

    objects_node = root.find('Objects')
    if objects_node is not None:
        for obj in objects_node.findall('Object'):
            obj_dict = {
                'Id': int(obj.get('id')),
                'Type': obj.get('type'),
                'Attributes': [parse_attribute(attr) for attr in obj.findall('Attribute')]
            }
            env_dict['Objects']['ObjectList'].append(obj_dict)

    for attr in root.findall('Attribute'):
        env_dict['Attributes'].append(parse_attribute(attr))

    return env_dict


