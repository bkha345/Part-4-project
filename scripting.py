import numpy as np
import matplotlib.pyplot as plt


# Function to plot cosine graph between a and b
def plot_cosine(a, b):
    import copy
    # Ensure a and b are between 0 and 1
    if not (0 < a < 1 and 0 < b < 1):
        raise ValueError("Both a and b must be between 0 and 1")

    # Generate values between a and b
    seconds = 12.5
    total_numbers = int(seconds * 4)

    x_values = np.linspace(0, np.pi*6, total_numbers)  # 500 points between a and b for smooth curve
    amplitude = (b-a)/2
    offset = a + (b-a)/2
    y_values = amplitude * np.cos(x_values)+offset
    # since we can only deal with a depth of 4096, we need it to constantly change
    f = open("compendium.txt", "w")
    duration = 480
    for repeat in range(duration):
        for i in range(len(y_values)-1):
            f.write(str(y_values[i]) + "\n")
    f.write("0.85\n")
    f.close()
    # Plot the graph
    plt.plot(x_values, y_values, label=f'Cosine curve from {a} to {b}')
    plt.title('Cosine Graph')
    plt.xlabel('X values')
    plt.ylabel('Cosine(X)')
    plt.grid(True)
    plt.show()

# Example usage
lower = 0.6
upper = 0.85
plot_cosine(lower, upper)


import re
NUMBER=50
historyVoltage = np.array([0.0 for _ in range(NUMBER)])
historyCurrent = np.array([0.0 for _ in range(NUMBER)])
historyPower = np.array([0.0 for _ in range(NUMBER)])

# read the last line of the file
def get_last_line_large_file(filename):
    last_line = None
    with open(filename, 'r') as f:
        lines = f.readlines()
        last_line = lines[-1]
        print(last_line)
        # for line in f:
        #     last_line = line.strip()
    if last_line:
        return last_line
    else:
        print(f"Error reading: {filename}")
        return None

# # Initialize figure and plot
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
# Set up the first subplot (ax1)
voltageLine, = ax1.plot([], [], 'b-', lw=3)
ax1.set_xlim(0, 2 * np.pi)
ax1.set_ylim(0.5, 0.9)
ax1.set_xlabel('Time')
ax1.set_ylabel('Amplitude')
ax1.set_title('Real-Time Voltage')

# Set up the second subplot (ax2)
currentLine, = ax2.plot([], [], 'r-', lw=3)
ax2.set_xlim(0, 2 * np.pi)
ax2.set_ylim(12.5, 13.3)
ax2.set_xlabel('Time')
ax2.set_ylabel('Amplitude')
ax2.set_title('Real-Time Current')

# Set up the third subplot (ax3)
powerLine, = ax3.plot([], [], 'g-', lw=3)
ax3.set_xlim(0, 2 * np.pi)
ax3.set_ylim(7, 12)
ax3.set_xlabel('Time')
ax3.set_ylabel('Amplitude')
ax3.set_title('Real-Time Power')

while True:

    a = (get_last_line_large_file("log.txt"))
    pattern=r"Power: (\d*.\d*)V x (\d*.\d*)A = (\d*.\d*)W"

    match = re.match(pattern, a)
    if match:
        print(match.groups())
        historyVoltage = np.roll(historyVoltage, -1)
        historyCurrent = np.roll(historyCurrent, -1)
        historyPower = np.roll(historyPower, -1)
        historyVoltage[-1] = (match.group(1)) # we can change the group
        historyCurrent[-1] = (match.group(2))
        historyPower[-1] = (match.group(3))
    print(historyVoltage)

    # Update plot data
    voltageLine.set_data(np.linspace(0, 5, NUMBER), historyVoltage)
    currentLine.set_data(np.linspace(0, 5, NUMBER), historyCurrent)
    powerLine.set_data(np.linspace(0, 5, NUMBER), historyPower)
    # Redraw the plot
    plt.draw()
    plt.tight_layout()

    # Pause to simulate real-time data plotting
    plt.pause(0.1)  # Control the update rate
