from dataclasses import dataclass, field, asdict
from typing import List, Optional
import xml.etree.ElementTree as ET

@dataclass
class Name:
    value: str

@dataclass
class Description:
    value: str

@dataclass
class DataType:
    value: str

@dataclass
class Value:
    content: str

@dataclass
class Mutable:
    value: bool

@dataclass
class Constraint:
    min: Optional[str] = None
    max: Optional[str] = None
    one_of: Optional[str] = None
    round_off: Optional[str] = None

@dataclass
class Attribute:
    name: Optional[Name] = None
    description: Optional[Description] = None
    data_type: Optional[DataType] = None
    value: Optional[Value] = None
    mutable: Optional[Mutable] = None
    constraint: Optional[Constraint] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Agent:
    id: int
    type: str
    attributes: List[Attribute] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "attributes": [attr.to_dict() for attr in self.attributes]
        }

@dataclass
class Agents:
    agent_list: List[Agent] = field(default_factory=list)

    def to_dict(self):
        return {"agent_list": [agent.to_dict() for agent in self.agent_list]}

@dataclass
class Object:
    id: int
    type: str
    attributes: List[Attribute] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "attributes": [attr.to_dict() for attr in self.attributes]
        }

@dataclass
class Objects:
    object_list: List[Object] = field(default_factory=list)

    def to_dict(self):
        return {"object_list": [obj.to_dict() for obj in self.object_list]}

@dataclass
class Environment:
    name: str
    type: str
    agents: Agents
    objects: Objects
    attributes: List[Attribute] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "agents": self.agents.to_dict(),
            "objects": self.objects.to_dict(),
            "attributes": [attr.to_dict() for attr in self.attributes]
        }
@dataclass
class ActionSpace:
    actions: List[str] = field(default_factory=list)

# Example of parsing an XML into the environment structure
def parse_environment(xml_string: str) -> Environment:
    root = ET.fromstring(xml_string)

    def parse_attributes(element):
        attributes = []
        for attr in element.findall("Attribute"):
            attributes.append(
                Attribute(
                    name=Name(attr.find("Name").get("value")) if attr.find("Name") is not None else None,
                    description=Description(attr.find("Description").get("value")) if attr.find("Description") is not None else None,
                    data_type=DataType(attr.find("DataType").get("value")) if attr.find("DataType") is not None else None,
                    value=Value(attr.find("Value").get("value")) if attr.find("Value") is not None else None,
                    mutable=Mutable(attr.find("Mutable").get("value") == 'true') if attr.find("Mutable") is not None else None,
                    constraint=Constraint(
                        min=attr.find("Constraint").get("Min") if attr.find("Constraint") is not None else None,
                        max=attr.find("Constraint").get("Max") if attr.find("Constraint") is not None else None,
                        one_of=attr.find("Constraint").get("oneOf") if attr.find("Constraint") is not None else None,
                        round_off=attr.find("Constraint").get("roundOff") if attr.find("Constraint") is not None else None,
                    )
                )
            )
        return attributes

    agents = [
        Agent(
            id=int(agent.get("id")),
            type=agent.get("type"),
            attributes=parse_attributes(agent)
        ) for agent in root.find("Agents").findall("Agent")
    ]

    objects = [
        Object(
            id=int(obj.get("id")),
            type=obj.get("type"),
            attributes=parse_attributes(obj)
        ) for obj in root.find("Objects").findall("Object")
    ]

    env = Environment(
        name=root.get("name"),
        type=root.get("type"),
        agents=Agents(agent_list=agents),
        objects=Objects(object_list=objects),
        attributes=parse_attributes(root)
    )

    return env
