import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor

def load_flight_data(pickle_file):
    """
    Load flight trajectory data from the pickle file.
    """
    if not os.path.exists(pickle_file):
        print(f"❌ Error: Pickle file not found: {pickle_file}")
        return None

    with open(pickle_file, "rb") as f:
        flight_data = pickle.load(f)

    return flight_data


def plot_flight_trajectory(pickle_path):
    """
    Generate and save the trajectory plot in the same folder as the pickle file.
    """
    flight_data = load_flight_data(pickle_path)
    if not flight_data:
        return

    ownship_x = flight_data["ownship_x"]
    ownship_y = flight_data["ownship_y"]
    intruder_x = flight_data["intruder_x"]
    intruder_y = flight_data["intruder_y"]

    plt.figure(figsize=(8, 6))
    plt.plot(ownship_x, ownship_y, 'bo-', label="Ownship (ACAS-Xu)")
    plt.plot(intruder_x, intruder_y, 'ro-', label="Intruder")
    plt.scatter([ownship_x[0]], [ownship_y[0]], c="blue", marker="o", s=100, label="Ownship Start")
    plt.scatter([intruder_x[0]], [intruder_y[0]], c="red", marker="o", s=100, label="Intruder Start")

    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.title("Flight Trajectory")

    plt.legend()
    plt.grid()

    # Save the plot in the same folder as the pickle file
    output_path = os.path.join(os.path.dirname(pickle_path), "trajectory_plot.png")
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Saved trajectory: {output_path}")


def find_pickle_files(csv_file, base_folder):
    """
    Reads the CSV file and finds all corresponding .pkl file paths.
    """
    df = pd.read_csv(csv_file)
    pickle_files = []

    for _, row in df.iterrows():
        env_folder = row["Environment"]
        task_folder = row["Task"]
        pickle_file = os.path.join(base_folder, env_folder, task_folder, "flight_data.pkl")

        if os.path.exists(pickle_file):
            pickle_files.append(pickle_file)
        else:
            print(f"⚠️ No pickle file found for {env_folder}/{task_folder}")

    return pickle_files


def generate_flight_trajectories_parallel(csv_file, base_folder, num_workers=4):
    """
    Generates flight trajectory images in parallel using multiple processes.
    """
    # Find all .pkl files that need processing
    pickle_files = find_pickle_files(csv_file, base_folder)
    print(f"🔍 Found {len(pickle_files)} flight data files.")

    # Run parallel processing
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        executor.map(plot_flight_trajectory, pickle_files)

    print("\n✅ All trajectory plots have been generated!")


# Example Usage:
if __name__ == "__main__":
    csv_file = "/scratch/projects/AIProbe/Test_Enviroment/ACAS_XU/10_20/simulation_results_parallel.csv"
    base_directory = "/scratch/projects/AIProbe/Test_Enviroment/ACAS_XU/10_20"

    # Use all available CPU cores
    num_workers = os.cpu_count()

    # Generate trajectory images in parallel
    generate_flight_trajectories_parallel(csv_file, base_directory, num_workers=num_workers)