import matplotlib.pyplot as plt
import numpy as np

from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter
from matplotlib.animation import FuncAnimation, FFMpegWriter
import pickle

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

import xml.etree.ElementTree as ET

def save_result_to_acas_xml(filename, ownship, intruder, state, timestep_count):
    """
    Save the final state to a proper ACAS-Xu format XML.
    """
    # Create root <Environment>
    root = ET.Element("Environment", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
        "name": "ACAS_Xu_Environment",
        "type": "simulation"
    })

    # Add <Agents>
    agents = ET.SubElement(root, "Agents")
    agent = ET.SubElement(agents, "Agent", {"id": "1", "type": "Aircraft"})
    for key, val in ownship.items():
        attr = ET.SubElement(agent, "Attribute")
        ET.SubElement(attr, "Name", value=key)
        ET.SubElement(attr, "DataType", value="float")
        ET.SubElement(attr, "Value", value=f"{val:.6f}")
        ET.SubElement(attr, "Mutable", value="true" if key != "X" else "false")
        constraint = ET.SubElement(attr, "Constraint", Min="-10000", Max="10000", Values="", Choice="")
        if key == "Theta":
            constraint.set("Min", "-3.14")
            constraint.set("Max", "3.14")
        elif "Speed" in key:
            constraint.set("Min", "10")
            constraint.set("Max", "1100")

    # Add <Objects>
    objects = ET.SubElement(root, "Objects")
    obj = ET.SubElement(objects, "Object", {"id": "1", "type": "Intruder"})
    for key, val in intruder.items():
        attr = ET.SubElement(obj, "Attribute")
        ET.SubElement(attr, "Name", value=key)
        ET.SubElement(attr, "DataType", value="float")
        ET.SubElement(attr, "Value", value=f"{val:.6f}")
        ET.SubElement(attr, "Mutable", value="true")
        constraint = ET.SubElement(attr, "Constraint", Min="-10000", Max="10000", Values="", Choice="")
        if key == "Auto_Theta":
            constraint.set("Min", "-3.14")
            constraint.set("Max", "3.14")
        elif "Speed" in key:
            constraint.set("Min", "10")
            constraint.set("Max", "1100")
            constraint.set("Choice", "4")

    # Add Global Attributes
    def add_global_attr(name, dtype, value, mutable, min_v, max_v):
        attr = ET.SubElement(root, "Attribute")
        ET.SubElement(attr, "Name", value=name)
        ET.SubElement(attr, "DataType", value=dtype)
        ET.SubElement(attr, "Value", value=str(value))
        ET.SubElement(attr, "Mutable", value=mutable)
        ET.SubElement(attr, "Constraint", Min=str(min_v), Max=str(max_v), Values="", Choice="")

    add_global_attr("Timestep_Count", "int", timestep_count, "true", 50, 10000)
    add_global_attr("Row_Distance", "float", "Unknown", "false", -1, 1)
    add_global_attr("Alpha", "float", "Unknown", "false", -1, 1)
    add_global_attr("Phi", "float", "Unknown", "false", -1, 1)

    # Write XML to file
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

def run_simulation(
    ownship_speed, ownship_x, ownship_y, ownship_theta, 
    intruder_speed, intruder_x, intruder_y, intruder_theta, 
    timestep_count,gif_folder,model
):
    from environment import env
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
        intruder_x=intruder_x, intruder_y=intruder_y, intruder_theta=intruder_theta, intruder_speed=intruder_speed)
    

    # Store positions for animation
    ownship_x_positions, ownship_y_positions = [], []
    intruder_x_positions, intruder_y_positions = [], []
    action = []
    state = None
    terminate = False
    is_invalide_state = False

    if air_env.terminated:
        print("🚨 Initial state: COLLISION detected! 🚨")
        return True ,  True


    # Run the simulation
    for step in range(timestep_count):  # Use timestep count from XML
        act = air_env.step()
        
        #print(states_seq)

        ownship_x_positions.append(air_env.ownship.x)
        ownship_y_positions.append(air_env.ownship.y)
        intruder_x_positions.append(air_env.intruder.x)
        intruder_y_positions.append(air_env.intruder.y)
        action.append(act)

        if air_env.terminated:
            print("Simulation Terminated collision detected.")
            reward, collide_flag, states_seq = air_env.reward_func()
            #state = [air_env.row, air_env.alpha, air_env.phi, air_env.ownship.speed, air_env.intruder.speed]
            state = states_seq[-1]
            print("Final State:", states_seq[-1])
            terminate = True
            break  # Stop if termination conditions are met
       

        # print(f"Step {step}:")
        # print(f"  Ownship Position: ({air_env.ownship.x}, {air_env.ownship.y})")
        # print(f"  Intruder Position: ({air_env.intruder.x}, {air_env.intruder.y})")
        ownship_dict = {
        "Ownship_Speed": air_env.ownship.speed,
        "X": air_env.ownship.x,
        "Y": air_env.ownship.y,
        "Theta": air_env.ownship.theta,
    }

    intruder_dict = {
        "Intruder_Speed": air_env.intruder.speed,
        "X": air_env.intruder.x,
        "Y": air_env.intruder.y,
        "Auto_Theta": air_env.intruder.theta,
    }

    if terminate:
        crash_xml = f"{gif_folder}/model{model}_crash_result.xml"
        save_result_to_acas_xml(crash_xml, ownship_dict, intruder_dict, state, timestep_count)
        print(f"Crash XML saved to: {crash_xml}")
    else:
        final_xml = f"{gif_folder}/model{model}_final.xml"
        save_result_to_acas_xml(final_xml, ownship_dict, intruder_dict, state, timestep_count)

    #print("saving")
    # Animate the flight paths
    #save_flight_paths_video(ownship_x_positions, ownship_y_positions, intruder_x_positions, intruder_y_positions,gif_folder)
    # Save the flight path data as a Pickle file
    save_simulation_data(f"{gif_folder}/model{model}_flight_data.pkl", ownship_x_positions, ownship_y_positions, intruder_x_positions, intruder_y_positions,state,action)
    return terminate,is_invalide_state



def save_simulation_data(filename, ownship_x, ownship_y, intruder_x, intruder_y, state, action):
    """Save simulation data to a Pickle file with structured labels."""
    data = {
        "States": {
            "ownship_x_positions": ownship_x,
            "ownship_y_positions": ownship_y,
            "intruder_x_positions": intruder_x,
            "intruder_y_positions": intruder_y,
        },
        "Observation": state,
        "Action": action
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)
    #print(f"Simulation data saved to {filename}")