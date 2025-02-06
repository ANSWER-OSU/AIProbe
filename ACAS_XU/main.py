import matplotlib.pyplot as plt
import numpy as np
from environment import env
from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter
from matplotlib.animation import FuncAnimation, FFMpegWriter 

def animate_flight_paths(ownship_x, ownship_y, intruder_x, intruder_y):
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
    
    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=50, blit=True)
    plt.show()

# Initialize environment
# #air_env = env(acas_speed=300, x2=500, y2=500, auto_theta=np.pi/4)
# #air_env = env(acas_speed=300, x2=0, y2=600, auto_theta=-np.pi/2)
# air_env = env(acas_speed=300, x2=300, y2=300, auto_theta=np.pi + np.pi/4)
# #air_env = env(acas_speed=300, x2=0, y2=1000, auto_theta=-np.pi/2, speed=300)
# ownship_x, ownship_y = [], []
# intruder_x, intruder_y = [], []

# for step in range(50000000):  # Simulate 500 steps
#     air_env.step()
#     if air_env.terminated:
#             break 
#     ownship_x.append(air_env.ownship.x)
#     ownship_y.append(air_env.ownship.y)
#     intruder_x.append(air_env.intruder.x)
#     intruder_y.append(air_env.intruder.y)
#     print(f"Ownship Position: ({air_env.ownship.x}, {air_env.ownship.y})")
#     print(f"Intruder Position: ({air_env.intruder.x}, {air_env.intruder.y})")

# # Animate flight paths
# animate_flight_paths(ownship_x, ownship_y, intruder_x, intruder_y)



import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

def run_simulation(
    ownship_speed, ownship_x, ownship_y, ownship_theta, 
    intruder_speed, intruder_x, intruder_y, intruder_theta, 
    timestep_count,gif_folder,
):
    """Runs ACAS-Xu flight simulation and visualizes the paths."""
    
    # Initialize the environment
    # air_env = env(
    #     acas_speed=ownship_speed, 
    #     x2=intruder_x, 
    #     y2=intruder_y, 
    #     auto_theta=intruder_theta
    # )

    air_env = env(
        ownship_x=ownship_x, ownship_y=ownship_y, ownship_theta=ownship_theta, acas_speed=ownship_speed,
        intruder_x=intruder_x, intruder_y=intruder_y, intruder_theta=intruder_theta, intruder_speed=intruder_speed
    )

    # Store positions for animation
    ownship_x_positions, ownship_y_positions = [], []
    intruder_x_positions, intruder_y_positions = [], []

    terminate = False 

    # Run the simulation
    for step in range(timestep_count):  # Use timestep count from XML
        air_env.step()
        if air_env.terminated:
            print("Simulation Terminated")
            terminate = True
            break  # Stop if termination conditions are met

        ownship_x_positions.append(air_env.ownship.x)
        ownship_y_positions.append(air_env.ownship.y)
        intruder_x_positions.append(air_env.intruder.x)
        intruder_y_positions.append(air_env.intruder.y)

        # print(f"Step {step}:")
        # print(f"  Ownship Position: ({air_env.ownship.x}, {air_env.ownship.y})")
        # print(f"  Intruder Position: ({air_env.intruder.x}, {air_env.intruder.y})")

    #print("saving")
    # Animate the flight paths
    #save_flight_paths_video(ownship_x_positions, ownship_y_positions, intruder_x_positions, intruder_y_positions,gif_folder)
# Save the flight path data as a Pickle file
    save_simulation_data(f"{gif_folder}/flight_data.pkl", ownship_x_positions, ownship_y_positions, intruder_x_positions, intruder_y_positions)
    return terminate


def animate_flight_paths(ownship_x, ownship_y, intruder_x, intruder_y):

    """Generates an animated flight path visualization."""
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
    
    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=50, blit=True)
    plt.show()


def save_flight_paths(ownship_x, ownship_y, intruder_x, intruder_y,gif_folder):
    """Generates and saves an animated flight path visualization as a GIF."""
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

    print("updating")

    def update(frame):
        ownship_line.set_data(ownship_x[:frame+1], ownship_y[:frame+1])
        intruder_line.set_data(intruder_x[:frame+1], intruder_y[:frame+1])
        ownship_dot.set_data([ownship_x[frame]], [ownship_y[frame]])
        intruder_dot.set_data([intruder_x[frame]], [intruder_y[frame]])
        return ownship_line, intruder_line, ownship_dot, intruder_dot
    
    print("animating")

     # ⏩ Speed Optimization: Skip frames to make rendering faster
    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=30, blit=False)

    #print("saving")
    # Save animation as a GIF
    gif_path = f"{gif_folder}/simulation.gif"
    ani.save(gif_path, writer=PillowWriter(fps=20))
    print(f"Animation saved as {gif_path}")



def save_flight_paths_video(ownship_x, ownship_y, intruder_x, intruder_y, gif_folder,frame_skip=5):
    """Generates and saves an animated flight path visualization as an MP4 video with optimized performance."""
    
    # Reduce data points for efficiency (skip frames)
    ownship_x = ownship_x[::frame_skip]
    ownship_y = ownship_y[::frame_skip]
    intruder_x = intruder_x[::frame_skip]
    intruder_y = intruder_y[::frame_skip]

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

    # ⏩ Speed Optimization: Skip frames to make rendering faster
    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=30, blit=False)

    # ✅ Save animation as an MP4 video
    video_path = f"{gif_folder}/simulation_video.mp4"
    writer = FFMpegWriter(fps=30, bitrate=1000)  # Adjust FPS & Bitrate for performance
    ani.save(video_path, writer=writer)
    
    print(f"✅ Video saved as {video_path}")



import pickle

def save_simulation_data(filename, ownship_x, ownship_y, intruder_x, intruder_y):
    """Save simulation data to a Pickle file."""
    data = {
        "ownship_x": ownship_x,
        "ownship_y": ownship_y,
        "intruder_x": intruder_x,
        "intruder_y": intruder_y,
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)
    #print(f"Simulation data saved to {filename}")