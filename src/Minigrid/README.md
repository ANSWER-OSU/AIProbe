## **To use AIProbe:**
#### Run the below command in the parent folder, to install all the libraries:

```python
pip install -r requirements.txt
```

#### To see the output, run the below command in this directory:
```python
python mutate.py
```
#### Note - Now check the log.txt to see the output

## **About Files:**

#### 1) EnvironmentState.py
The provided file defines several classes representing different elements of a mini-grid environment, including Door, Key, Object, Lava, Agent, and State. Each class initializes with attributes related to its specific entity, such as coordinates, status, and presence indicators. These classes collectively model the state and elements of a mini-grid scenario.

#### 2) LoadConfig.py
The provided Python script implements a function `load_InitialState(file_path)` that parses an XML file describing the initial state of a game environment and constructs an instance of the `State` class, populated with elements such as an `Agent`, `Doors`, `Keys`, `Objects`, and `LavaTiles`. The function utilizes the ElementTree library to parse the XML structure and initializes the attributes of each entity based on the information provided in the XML file.

#### 3) Config.xml
The provided XML structure represents an initial state configuration for a game environment. It includes specifications for an agent's initial position and direction, destination position and direction, a list of keys with their coordinates and status, a list of doors with their coordinates and status, a list of objects with pick and drop coordinates and statuses, and lava tiles with their coordinates and presence indicator. This XML format facilitates the setup of initial game scenarios by defining the positions, statuses, and attributes of various elements within the environment.

#### 4) environment.py
The provided Python script defines classes and functions for customizing a MiniGrid environment, executing instructions within the environment, logging states, and assessing capabilities based on environment changes. It utilizes classes such as CustomMiniGridEnv, State, and Agent to manage the mini-grid environment, including elements like agents, doors, keys, objects, and lava tiles. Additionally, it includes functionality to execute instructions within the environment, update states, and log environment changes and capabilities.

#### 5) mutate.py
The provided Python script defines an InstructionMutator class responsible for generating mutated instructions based on a set of seed instructions and mutation rules. It utilizes randomization to create variations of instructions by inserting random actions, swapping directions, and duplicating directions. The mutations are checked for validity and capability using functions from the environment module, and valid instructions are stored or written to a file. Finally, it returns a list of generated instructions meeting the specified criteria. The script provides an example of usage, demonstrating how to instantiate the InstructionMutator class with seed instructions and generate mutated instructions.

#### 6) agentPosition.py
The provided Python function check_environment_changes compares the initial and final states of the game environment to determine if any significant changes have occurred. It specifically focuses on the agent's position and path, returning True if there are differences and False otherwise. Additional functionality for comparing door statuses is commented out.
