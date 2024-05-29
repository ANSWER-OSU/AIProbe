class Door:
    def __init__(self, x, y, status,color,locked):
        self.x = x
        self.y = y
        self.door_status = status
        self.color = color
        self.door_locked = locked

class Key:
    def __init__(self, x_init, y_init, is_picked, is_present,color):
        self.x_init = x_init
        self.y_init = y_init
        self.is_picked = is_picked
        self.is_present = is_present
        self.color = color

class Object:
    def __init__(self, x, y, pick_status, v, w, drop_status, is_present,color):
        self.x = x
        self.y = y
        self.pick_status = pick_status
        self.v = v
        self.w = w
        self.drop_status = drop_status
        self.is_present = is_present
        self.color = color

class Lava:
    def __init__(self, x, y, is_present):
        self.x = x
        self.y = y
        self.is_present = is_present

class Agent:
    def __init__(self, init_pos, init_direction, dest_pos, dest_direction, path):
        self.init_pos = init_pos
        self.init_direction = init_direction
        self.dest_pos = dest_pos
        self.dest_direction = dest_direction
        self.path = path

class Wall:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class State:
    def __init__(self):
        self.agent = None
        self.doors = []
        self.keys = []
        self.objects = []
        self.lava_tiles = []
        self.walls = []