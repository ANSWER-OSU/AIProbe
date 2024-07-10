from collections import deque, defaultdict
from Fuzzer.LoadConfig import load_InitialState


# def compute_valid_actions(file_path):
#     initialEnvironment, GridSize = load_InitialState(file_path)
#
#     directions = {
#         "N": (0, -1),
#         "E": (1, 0),
#         "S": (0, 1),
#         "W": (-1, 0)
#     }
#
#     walls = {(wall.x, wall.y) for wall in initialEnvironment.walls}
#     for i in range(GridSize):
#         walls.add((i, 0))  # Top boundary
#         walls.add((i, GridSize - 1))  # Bottom boundary
#         walls.add((0, i))  # Left boundary
#         walls.add((GridSize - 1, i))  # Right boundary
#
#     lava = {(lava_tile.x, lava_tile.y) for lava_tile in initialEnvironment.lava_tiles if lava_tile.is_present}
#     keys = {(key.x_init, key.y_init): key.color for key in initialEnvironment.keys if key.is_present}
#
#     def is_valid(nx, ny, grid_size, walls, lava):
#         return 0 <= nx < grid_size and 0 <= ny < grid_size and (nx, ny) not in walls and (nx, ny) not in lava
#
#     def get_valid_actions(x, y, direction, grid_size, walls, lava, keys):
#         forward = directions[direction]
#         right = directions["NESW"[("NESW".index(direction) + 1) % 4]]
#         left = directions["NESW"[("NESW".index(direction) - 1) % 4]]
#
#         actions = {}
#
#         if is_valid(x + forward[0], y + forward[1], grid_size, walls, lava):
#             actions["forward"] = (x + forward[0], y + forward[1])
#         if is_valid(x + right[0], y + right[1], grid_size, walls, lava):
#             actions["right"] = (x + right[0], y + right[1])
#         if is_valid(x + left[0], y + left[1], grid_size, walls, lava):
#             actions["left"] = (x + left[0], y + left[1])
#         if (x+ forward[0], y+ forward[1]) in keys:
#             actions["pickup"] = keys[(x+ forward[0], y+ forward[1])]
#
#         return actions
#
#     action_map = defaultdict(dict)
#     start_x, start_y = initialEnvironment.agent.init_pos
#     queue = deque([(start_x, start_y)])
#     visited = set([(start_x, start_y)])
#
#     while queue:
#         x, y = queue.popleft()
#         for direction in directions:
#             action_map[(x, y)][direction] = get_valid_actions(x, y, direction, GridSize, walls, lava, keys)
#
#         for direction, (dx, dy) in directions.items():
#             nx, ny = x + dx, y + dy
#             if is_valid(nx, ny, GridSize, walls, lava) and (nx, ny) not in visited:
#                 queue.append((nx, ny))
#                 visited.add((nx, ny))
#
#     return action_map

def is_valid(nx, ny, grid_size, walls, lava):
    return 0 <= nx < grid_size and 0 <= ny < grid_size and (nx, ny) not in walls and (nx, ny) not in lava

def compute_valid_actionss(file_path):
    initialEnvironment, GridSize = load_InitialState(file_path)

    walls = {(wall.x, wall.y) for wall in initialEnvironment.walls}
    for i in range(GridSize):
        walls.add((i, 0))  # Top boundary
        walls.add((i, GridSize - 1))  # Bottom boundary
        walls.add((0, i))  # Left boundary
        walls.add((GridSize - 1, i))  # Right boundary

    lava = {(lava_tile.x, lava_tile.y) for lava_tile in initialEnvironment.lava_tiles if lava_tile.is_present}
    keys = {(key.x_init, key.y_init): key.color for key in initialEnvironment.keys if key.is_present}

    action_space = {
        0: ("left", "Turn left"),
        1: ("right", "Turn right"),
        2: ("forward", "Move forward"),
        3: ("pickup", "Pick up")
    }

    action_map = defaultdict(dict)

def is_valid_cell(x, y, grid_size, walls, lava):
    return 0 <= x < grid_size and 0 <= y < grid_size and (x, y) not in walls and (x, y) not in lava


def compute_valid_actions(file_path):
    # Load the initial environment and grid size from the given file
    initialEnvironment, GridSize = load_InitialState(file_path)

    # Create sets for walls and boundaries
    walls = {(wall.x, wall.y) for wall in initialEnvironment.walls}
    for i in range(GridSize):
        walls.add((i, 0))  # Top boundary
        walls.add((i, GridSize - 1))  # Bottom boundary
        walls.add((0, i))  # Left boundary
        walls.add((GridSize - 1, i))  # Right boundary

    # Create a set for lava tiles
    lava = {(lava_tile.x, lava_tile.y) for lava_tile in initialEnvironment.lava_tiles if lava_tile.is_present}

    # Create a dictionary for keys, mapping their positions to their colors
    keys = {(key.x_init, key.y_init): key.color for key in initialEnvironment.keys if key.is_present}

    # Define the action space with action IDs and descriptions
    action_space = {
        0: "left",
        1: "right",
        2: "forward",
        3: "pickup"
    }

    # Initialize a dictionary to store valid cells and their possible actions
    valid_cells = {}

    # Possible directions
    directions = ['n', 'e', 's', 'w']

    # Iterate over each cell in the grid
    for x in range(GridSize):
        for y in range(GridSize):
            for direction in directions:
                if is_valid_cell(x, y, GridSize, walls, lava):
                    actions = ["left", "right", "forward"]
                    if (x, y) in keys:
                        actions.append("pickup")
                    valid_cells[((x, y), direction)] = actions

    return valid_cells





def compute_unsafe_states(file_path):
    initialEnvironment, GridSize = load_InitialState(file_path)

    walls = {(wall.x, wall.y) for wall in initialEnvironment.walls}
    for i in range(GridSize):
        walls.add((i, 0))  # Top boundary
        walls.add((i, GridSize - 1))  # Bottom boundary
        walls.add((0, i))  # Left boundary
        walls.add((GridSize - 1, i))  # Right boundary

    lava = {(lava_tile.x, lava_tile.y) for lava_tile in initialEnvironment.lava_tiles if lava_tile.is_present}
    landmines = {(landmine.x, landmine.y) for landmine in initialEnvironment.landmines if landmine.is_present}
    keys = {(key.x_init, key.y_init): key.color for key in initialEnvironment.keys if key.is_present}

    unsafe_states = walls.union(lava).union(landmines)

    return unsafe_states
