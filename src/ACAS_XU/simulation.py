import matplotlib.pyplot as plt
import numpy as np
import pickle
from matplotlib.animation import FuncAnimation
from matplotlib.animation import FuncAnimation, FFMpegWriter
from custom_environment import CustomACASEnv

def run_simulation(ownship_speed, ownship_x, ownship_y, ownship_theta, intruder_speed, intruder_x, intruder_y, intruder_theta, timestep_count,gif_folder, setting):
    """Runs ACAS-Xu flight simulation and visualizes the paths."""

    air_env = CustomACASEnv(x2=ownship_x, y2=ownship_y, auto_theta=ownship_theta, acas_speed=ownship_speed,
        intruder_x=intruder_x, intruder_y=intruder_y, intruder_theta=intruder_theta, intruder_speed=intruder_speed, setting=setting)

    ownship_x_positions, ownship_y_positions = [], []
    intruder_x_positions, intruder_y_positions = [], []
    terminate = False
    # Run the simulation
    for step in range(timestep_count):
        air_env.sim_env.step()
        if air_env.sim_env.terminated:
            terminate = True
            break

        ownship_x_positions.append(air_env.sim_env.ownship.x)
        ownship_y_positions.append(air_env.sim_env.ownship.y)
        intruder_x_positions.append(air_env.sim_env.intruder.x)
        intruder_y_positions.append(air_env.sim_env.intruder.y)

    # Animate the flight paths
    # save_flight_paths_video(ownship_x_positions, ownship_y_positions, intruder_x_positions, intruder_y_positions,gif_folder)

    # Save the flight path data as a Pickle file
    save_simulation_data(f"{gif_folder}/{setting}_data.pkl", ownship_x_positions, ownship_y_positions, intruder_x_positions, intruder_y_positions)
    return terminate

def save_flight_paths_video(ownship_x, ownship_y, intruder_x, intruder_y, gif_folder,frame_skip=5):
    """Generates and saves an animated flight path visualization as an MP4 video with optimized performance."""

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(min(min(ownship_x), min(intruder_x)) - 10, max(max(ownship_x), max(intruder_x)) + 10)
    ax.set_ylim(min(min(ownship_y), min(intruder_y)) - 10, max(max(ownship_y), max(intruder_y)) + 10)
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Ownship vs Intruder Flight Paths")

    ownship_line, = ax.plot([], [], 'bo-', label="Ownship (ACAS-Xu)")
    intruder_line, = ax.plot([], [], 'ro-', label="Intruder")
    ownship_dot, = ax.plot([], [], 'bo', markersize=10)
    intruder_dot, = ax.plot([], [], 'ro', markersize=10)
    ax.legend()
    ax.grid()

    def update(frame):
        ownship_line.set_data(ownship_x[:frame+1], ownship_y[:frame+1])
        intruder_line.set_data(intruder_x[:frame+1], intruder_y[:frame+1])
        ownship_dot.set_data([ownship_x[frame]], [ownship_y[frame]])
        intruder_dot.set_data([intruder_x[frame]], [intruder_y[frame]])
        return ownship_line, intruder_line, ownship_dot, intruder_dot

    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=30, blit=False)
    video_path = f"{gif_folder}/simulation_video.mp4"
    writer = FFMpegWriter(fps=30, bitrate=1000)
    ani.save(video_path, writer=writer)
    print(f"Video saved as {video_path}")

def save_simulation_data(filename, ownship_x, ownship_y, intruder_x, intruder_y):
    data = {
        "ownship_x": ownship_x,
        "ownship_y": ownship_y,
        "intruder_x": intruder_x,
        "intruder_y": intruder_y,
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)
