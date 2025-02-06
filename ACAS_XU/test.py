import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Define ACAS agent (ownship)
class ACASagent:
    def __init__(self, acas_speed):
        self.x = 0  # Starting position
        self.y = 0
        self.theta = np.pi / 2  # Facing upward initially
        self.speed = acas_speed
        self.interval = 0.1  # Time step

    def step(self, action):
        if action == 1:
            self.theta += (1.5 / 180) * np.pi * self.interval
        elif action == 2:
            self.theta -= (1.5 / 180) * np.pi * self.interval
        elif action == 3:
            self.theta += (3.0 / 180) * np.pi * self.interval
        elif action == 4:
            self.theta -= (3.0 / 180) * np.pi * self.interval

        # Normalize theta
        while self.theta > np.pi:
            self.theta -= np.pi * 2
        while self.theta < -np.pi:
            self.theta += np.pi * 2

        # Update position
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self):
        return np.random.randint(0, 5)  # Random action


# Define Intruder agent
class Autoagent:
    def __init__(self, x, y, auto_theta, speed=400):
        self.x = x
        self.y = y
        self.theta = auto_theta
        self.speed = speed
        self.interval = 0.1  # Time step

    def step(self, action):
        if action == 1:
            self.theta += (1.5 / 180) * np.pi * self.interval
        elif action == 2:
            self.theta -= (1.5 / 180) * np.pi * self.interval
        elif action == 3:
            self.theta += (3.0 / 180) * np.pi * self.interval
        elif action == 4:
            self.theta -= (3.0 / 180) * np.pi * self.interval

        # Normalize theta
        while self.theta > np.pi:
            self.theta -= np.pi * 2
        while self.theta < -np.pi:
            self.theta += np.pi * 2

        # Update position
        self.x += self.speed * np.cos(self.theta) * self.interval
        self.y += self.speed * np.sin(self.theta) * self.interval

    def act(self):
        return 0  # Move straight


# Environment class
class env:
    def __init__(self, acas_speed, x2, y2, auto_theta):
        self.ownship = ACASagent(acas_speed)
        self.inturder = Autoagent(x2, y2, auto_theta)

    def step(self):
        acas_act = self.ownship.act()
        auto_act = self.inturder.act()
        self.ownship.step(acas_act)
        self.inturder.step(auto_act)


# Initialize environment
acas_speed = 600  # Ownship speed
x2, y2, auto_theta = 500, 500, np.pi / 4  # Intruder closer to origin
air_env = env(acas_speed=acas_speed, x2=x2, y2=y2, auto_theta=auto_theta)

# Setup Matplotlib
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(-200, 600)
ax.set_ylim(-200, 600)
ax.set_title("ACAS Agent vs. Intruder")
ax.set_xlabel("X Position")
ax.set_ylabel("Y Position")

ownship_point, = ax.plot([], [], 'ro', markersize=10, label="Ownship (ACAS)")
intruder_point, = ax.plot([], [], 'bo', markersize=10, label="Intruder")
ownship_path, = ax.plot([], [], 'r-', linewidth=1, alpha=0.7)
intruder_path, = ax.plot([], [], 'b-', linewidth=1, alpha=0.7)
ax.legend()

# History
ownship_x_history = []
ownship_y_history = []
intruder_x_history = []
intruder_y_history = []

def update(frame):
    air_env.step()
    print(f"Ownship: ({air_env.ownship.x:.2f}, {air_env.ownship.y:.2f})")
    print(f"Intruder: ({air_env.inturder.x:.2f}, {air_env.inturder.y:.2f})")

    ownship_x_history.append(air_env.ownship.x)
    ownship_y_history.append(air_env.ownship.y)
    intruder_x_history.append(air_env.inturder.x)
    intruder_y_history.append(air_env.inturder.y)

    ownship_point.set_data([air_env.ownship.x], [air_env.ownship.y])
    intruder_point.set_data([air_env.inturder.x], [air_env.inturder.y])
    ownship_path.set_data(ownship_x_history, ownship_y_history)
    intruder_path.set_data(intruder_x_history, intruder_y_history)

    return ownship_point, intruder_point, ownship_path, intruder_path

# Run animation
ani = animation.FuncAnimation(fig, update, frames=500, interval=50, blit=True)

plt.show()