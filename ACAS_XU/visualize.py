import pickle
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.animation import FuncAnimation, FFMpegWriter

def load_and_visualize_pickle(pickle_file, save_gif_path=None):
    """Load simulation data from a Pickle file and visualize it as an animation."""
    
    # Load the data
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)

    ownship_x = data["ownship_x"]
    ownship_y = data["ownship_y"]
    intruder_x = data["intruder_x"]
    intruder_y = data["intruder_y"]

    # Create the plot
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
        """Update function for animation."""
        ownship_line.set_data(ownship_x[:frame+1], ownship_y[:frame+1])
        intruder_line.set_data(intruder_x[:frame+1], intruder_y[:frame+1])
        ownship_dot.set_data([ownship_x[frame]], [ownship_y[frame]])
        intruder_dot.set_data([intruder_x[frame]], [intruder_y[frame]])
        return ownship_line, intruder_line, ownship_dot, intruder_dot

    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=50, blit=True)

    # Save animation as GIF if path is provided
    if save_gif_path:
        ani.save(save_gif_path, writer="pillow", fps=20)
        print(f"Animation saved to {save_gif_path}")

    plt.show()



def load_last_frame(pickle_file):
    """Load simulation data from a Pickle file and visualize only the last frame."""
    
    # Load the data
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)

    ownship_x = data["ownship_x"]
    ownship_y = data["ownship_y"]
    intruder_x = data["intruder_x"]
    intruder_y = data["intruder_y"]

    # Get the last frame index
    last_frame = len(ownship_x) - 1

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(min(min(ownship_x), min(intruder_x)) - 10, max(max(ownship_x), max(intruder_x)) + 10)
    ax.set_ylim(min(min(ownship_y), min(intruder_y)) - 10, max(max(ownship_y), max(intruder_y)) + 10)
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Final Position of Ownship and Intruder")

    # Plot full paths (optional, for reference)
    ax.plot(ownship_x, ownship_y, 'bo-', alpha=0.5, label="Ownship (ACAS-Xu)")
    ax.plot(intruder_x, intruder_y, 'ro-', alpha=0.5, label="Intruder")

    # Plot last positions
    ax.plot(ownship_x[last_frame], ownship_y[last_frame], 'bo', markersize=12, label="Final Ownship Position")
    ax.plot(intruder_x[last_frame], intruder_y[last_frame], 'ro', markersize=12, label="Final Intruder Position")

    ax.legend()
    ax.grid()
    plt.show()

# Example Usage:
#load_last_frame("/Users/rahil/Documents/GitHub/AIProbe/csharp/results/Result_ACAS_Xu_9472/Env_1/Task_1/flight_data.pkl")



def save_animation_to_video(pickle_file, save_video_path="flight_animation.mp4"):
    """Load simulation data from a Pickle file and save it as an MP4 video."""
    
    # Load the data
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)

    ownship_x = data["ownship_x"]
    ownship_y = data["ownship_y"]
    intruder_x = data["intruder_x"]
    intruder_y = data["intruder_y"]

    # Create the plot
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
        """Update function for animation."""
        ownship_line.set_data(ownship_x[:frame+1], ownship_y[:frame+1])
        intruder_line.set_data(intruder_x[:frame+1], intruder_y[:frame+1])
        ownship_dot.set_data([ownship_x[frame]], [ownship_y[frame]])
        intruder_dot.set_data([intruder_x[frame]], [intruder_y[frame]])
        return ownship_line, intruder_line, ownship_dot, intruder_dot

    ani = FuncAnimation(fig, update, frames=len(ownship_x), interval=50, blit=True)

    # Save animation as MP4 video
    writer = FFMpegWriter(fps=20, metadata={"title": "Flight Path Animation"})
    ani.save(save_video_path, writer=writer)

    print(f"Animation saved to {save_video_path}")

# Example Usage:
#save_animation_to_video("/Users/rahil/Documents/GitHub/AIProbe/csharp/results/Result_ACAS_Xu_9472/Env_1/Task_1/flight_data.pkl")



# Example Usage:
#load_and_visualize_pickle("/Users/rahil/Documents/GitHub/AIProbe/csharp/results/Result_ACAS_Xu_9472/Env_1/Task_1/flight_data.pkl")




import pickle
import matplotlib.pyplot as plt

def plot_flight_paths(pickle_file, save_image_path=None):
    """Load simulation data from a Pickle file and visualize the full flight paths as a static plot."""
    
    # Load the data
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)

    ownship_x = data["ownship_x"]
    ownship_y = data["ownship_y"]
    intruder_x = data["intruder_x"]
    intruder_y = data["intruder_y"]

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(min(min(ownship_x), min(intruder_x)) - 10, max(max(ownship_x), max(intruder_x)) + 10)
    ax.set_ylim(min(min(ownship_y), min(intruder_y)) - 10, max(max(ownship_y), max(intruder_y)) + 10)
    
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Ownship vs Intruder Flight Paths")

    # Plot full paths
    ax.plot(ownship_x, ownship_y, 'bo-', label="Ownship (ACAS-Xu)")
    ax.plot(intruder_x, intruder_y, 'ro-', label="Intruder")

    # Mark starting positions
    ax.plot(ownship_x[0], ownship_y[0], 'gs', markersize=10, label="Start Ownship")
    ax.plot(intruder_x[0], intruder_y[0], 'ys', markersize=10, label="Start Intruder")

    # Mark final positions
    ax.plot(ownship_x[-1], ownship_y[-1], 'bo', markersize=12, label="Final Ownship Position")
    ax.plot(intruder_x[-1], intruder_y[-1], 'ro', markersize=12, label="Final Intruder Position")

    ax.legend()
    ax.grid()

    # Save the image if path is provided
    if save_image_path:
        plt.savefig(save_image_path, dpi=300)
        print(f"Plot saved to {save_image_path}")

    plt.show()

# Example Usage:
plot_flight_paths("/Users/rahil/Downloads/Task_492/flight_data.pkl",
                  save_image_path="flight_paths.png")