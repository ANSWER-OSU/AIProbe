from collections import deque, defaultdict
from Fuzzer.LoadConfig import load_InitialState


def compute_valid_actions(file_path):
    initialEnvironment, GridSize = load_InitialState(file_path)

    directions = {
        "N": (0, -1),
        "E": (1, 0),
        "S": (0, 1),
        "W": (-1, 0)
    }

    walls = {(wall.x, wall.y) for wall in initialEnvironment.walls}
    for i in range(GridSize):
        walls.add((i, 0))  # Top boundary
        walls.add((i, GridSize - 1))  # Bottom boundary
        walls.add((0, i))  # Left boundary
        walls.add((GridSize - 1, i))  # Right boundary

    lava = {(lava_tile.x, lava_tile.y) for lava_tile in initialEnvironment.lava_tiles if lava_tile.is_present}
    keys = {(key.x_init, key.y_init): key.color for key in initialEnvironment.keys if key.is_present}

    def is_valid(nx, ny, grid_size, walls, lava):
        return 0 <= nx < grid_size and 0 <= ny < grid_size and (nx, ny) not in walls and (nx, ny) not in lava

    def get_valid_actions(x, y, direction, grid_size, walls, lava, keys):
        forward = directions[direction]
        right = directions["NESW"[("NESW".index(direction) + 1) % 4]]
        left = directions["NESW"[("NESW".index(direction) - 1) % 4]]

        actions = {}

        if is_valid(x + forward[0], y + forward[1], grid_size, walls, lava):
            actions["forward"] = (x + forward[0], y + forward[1])
        if is_valid(x + right[0], y + right[1], grid_size, walls, lava):
            actions["right"] = (x + right[0], y + right[1])
        if is_valid(x + left[0], y + left[1], grid_size, walls, lava):
            actions["left"] = (x + left[0], y + left[1])
        if (x+ forward[0], y+ forward[1]) in keys:
            actions["pickup"] = keys[(x+ forward[0], y+ forward[1])]

        return actions

    action_map = defaultdict(dict)
    start_x, start_y = initialEnvironment.agent.init_pos
    queue = deque([(start_x, start_y)])
    visited = set([(start_x, start_y)])

    while queue:
        x, y = queue.popleft()
        for direction in directions:
            action_map[(x, y)][direction] = get_valid_actions(x, y, direction, GridSize, walls, lava, keys)

        for direction, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            if is_valid(nx, ny, GridSize, walls, lava) and (nx, ny) not in visited:
                queue.append((nx, ny))
                visited.add((nx, ny))

    return action_map


