from __future__ import annotations

from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Door, Goal, Key, Wall
from minigrid.manual_control import ManualControl
from minigrid.core.actions import Actions  # Import Actions from minigrid.minigrid
from minigrid.minigrid_env import MiniGridEnv


class DoorKeyEnv(MiniGridEnv):
    def __init__(
            self,
            size=16,
            agent_start_pos=(1, 1),
            agent_start_dir=0,
            max_steps: int | None = None,
            **kwargs,
    ):
        self.agent_start_pos = agent_start_pos
        self.agent_start_dir = agent_start_dir

        mission_space = MissionSpace(mission_func=self._gen_mission)

        if max_steps is None:
            max_steps = 4 * size ** 2

        super().__init__(
            mission_space=mission_space,
            grid_size=size,
            # Set this to True for maximum speed
            see_through_walls=True,
            max_steps=max_steps,
            **kwargs,
        )

    @staticmethod
    def _gen_mission():
        return "use the key to open the door and then get to the goal"

    def _gen_grid(self, width, height):
        # Create an empty grid
        self.grid = Grid(width, height)

        # Generate the surrounding walls
        self.grid.wall_rect(0, 0, width, height)

        # Place the door and key
        self.grid.set(width // 2, height // 2, Door("red", is_locked=True))
        self.grid.set(width // 2 - 2, height // 2, Key("green"))

        # Place a goal square in the bottom-right corner
        self.put_obj(Goal(), width - 2, height - 2)

        # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "use the key to open the door and then get to the goal"


def main():
    env = DoorKeyEnv(render_mode="human")

    # Enable manual control for testing
    manual_control = ManualControl(env, seed=42)

    # Create a dictionary to map keyboard keys to actions
    action_keys = {
        ord('p'): Actions.pickup,
        ord('t'): Actions.toggle
    }
    # Set the manual control keys
    manual_control.action_keys = action_keys

    manual_control.start()


if __name__ == "__main__":
    main()
