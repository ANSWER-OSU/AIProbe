import xml.etree.ElementTree as ET
import random

from Minigrid.EnvironmentState import Wall


def mutate_environment(xml_string):

    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Example mutations:
    # 1. Change agent's initial position
    agent = root.find("Agent")
    if agent is not None:
        initial_position = agent.find("InitialPosition")
        if initial_position is not None:
            initial_position.set("x", str(random.randint(1, 7)))
            initial_position.set("y", str(random.randint(1, 7)))

    # 2. Change positions of keys
    keys = root.find("Keys")
    if keys is not None:
        for key in keys.findall("Key"):
            key.set("x_init", str(random.randint(1, 7)))
            key.set("y_init", str(random.randint(1, 7)))
            key.set("is_picked", str(random.choice([0, 1])))
            key.set("is_present", str(random.choice([0, 1])))

    # 3. Add a new door with all required attributes
    doors = root.find("Doors")
    if doors is not None:
        new_door = ET.SubElement(doors, "Door",
                                 x=str(random.randint(1, 7)),
                                 y=str(random.randint(1, 7)),
                                 door_open=str(random.choice([0, 1])),
                                 color=random.choice(["red", "blue"]),
                                 door_locked=str(random.choice([0, 1])))

    # 4. Change positions and attributes of objects
    objects = root.find("Objects")
    if objects is not None:
        for obj in objects.findall("Object"):
            obj.set("pick_x", str(random.randint(1, 7)))
            obj.set("pick_y", str(random.randint(1, 7)))
            obj.set("pickStatus", str(random.choice([0, 1])))
            obj.set("drop_x", str(random.randint(1, 7)))
            obj.set("drop_y", str(random.randint(1, 7)))
            obj.set("dropStatus", str(random.choice([0, 1])))
            obj.set("is_present", str(random.choice([0, 1])))

    # 5. Change lava tile positions
    lava_tiles = root.find("LavaTiles")
    if lava_tiles is not None:
        for lava in lava_tiles.findall("Lava"):
            lava.set("x", str(random.randint(1, 7)))
            lava.set("y", str(random.randint(1, 7)))
            lava.set("is_present", str(random.choice([0, 1])))


    walls = root.find('Walls')



    # Convert the mutated tree back to a string
    mutated_xml_string = ET.tostring(root, encoding="unicode")
    return mutated_xml_string


# Given XML string
env_xml = """
<Environment>
    <Agent>
        <InitialPosition x="1" y="1" />
        <InitialDirection theta="e" />
        <DestinationPosition x="5" y="5" />
        <DestinationDirection theta="e" />
        <Path>
        </Path>
    </Agent>
    <Keys>
         <Key x_init="1" y_init="1" is_picked="0" is_present="0" color="red" />
    </Keys>
    <Doors>
    </Doors>
    <Objects>
        <Object pick_x="2" pick_y="2" pickStatus="0" drop_x="3" drop_y="3" dropStatus="0" is_present="1"/>
    </Objects>
    <LavaTiles>
        <Lava x="4" y="3" is_present="1" />
        <Lava x="1" y="4" is_present="1" />
        <Lava x="3" y="4" is_present="1" />
        <Lava x="2" y="1" is_present="1" />
        <Lava x="2" y="5" is_present="1" />
        <Lava x="1" y="2" is_present="1" />
        <Lava x="3" y="5" is_present="1" />
    </LavaTiles>
     <Grid>
        <Size grid_Size="7" />
    </Grid>
</Environment>
"""

# Mutate the environment
mutated_env_xml = mutate_environment(env_xml)
print(mutated_env_xml)
