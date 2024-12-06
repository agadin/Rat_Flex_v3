import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file into a DataFrame
file_path = 'data.csv'  # Update with the correct file path
columns = ['Time', 'Angle', 'Force', 'Motor_State', 'Direction', 'Protocol_Step']
data = pd.read_csv(file_path, names=columns)
data = data[data['Time'] >= 100]
data = data[data['Time'] <= 130]

# Ensure columns are the correct data types
data['Time'] = data['Time'].astype(float)
data['Angle'] = data['Angle'].astype(float)
data['Force'] = data['Force'].astype(float)

# Plot Force vs. Time
plt.figure(figsize=(8, 6))
plt.plot(data['Time'], data['Force'], label='Force vs. Time', color='blue')
plt.xlabel('Time (s)')
plt.ylabel('Force')
plt.title('Force vs. Time')
plt.grid(True)
plt.legend()
plt.show()
plt.savefig('img/force_vs_time.png')

# Plot Angle vs. Time
plt.figure(figsize=(8, 6))
plt.plot(data['Time'], data['Angle'], label='Angle vs. Time', color='green')
plt.xlabel('Time (s)')
plt.ylabel('Angle (degrees)')
plt.title('Angle vs. Time')
plt.grid(True)
plt.legend()
plt.show()
plt.savefig('img/angle_vs_time.png')

# Plot Force vs. Angle
plt.figure(figsize=(8, 6))
plt.plot(data["Angle"], data["Force"], marker='o', linestyle='-', color='b', label='Force vs. Angle')
# Add labels and title
plt.xlabel("Angle", fontsize=12)
plt.ylabel("Force", fontsize=12)
plt.title("Force vs. Angle", fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=10)

plt.savefig('img/force_vs_angle.png')
# Display the plot
plt.show()
