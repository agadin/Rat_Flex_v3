import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Step 1: Load the CSV data
file_path = '/Users/alexandergadin/Downloads/20250127_1234_01/20250127_None_1234_01.csv'  # Replace with your actual file path
headers = ['Time', 'Angle', 'Force', 'raw_Force', 'Motor_State', 'Direction', 'Protocol_Step']

# Read the CSV and add headers
df = pd.read_csv(file_path, header=None, names=headers)

# Step 2: Define protocol step groups for 11, 25, 39, etc.; 7, 21, 35, etc.; 3, 17, 31, etc.; and 1, 15, 29, etc.
group_11 = list(range(11, df['Protocol_Step'].max() + 1, 14))
group_7 = list(range(7, df['Protocol_Step'].max() + 1, 14))
group_3 = list(range(3, df['Protocol_Step'].max() + 1, 14))
group_1 = list(range(1, df['Protocol_Step'].max() + 1, 14))

# Step 3: Define x values for forces
x_values = [0.35 + i * 0.05 for i in range(len(group_11))]

# Step 4: Calculate absolute angle differences for each group
def calculate_differences(group):
    differences = []
    for step in group:
        step_data = df[df['Protocol_Step'] == step]
        if not step_data.empty:
            first_angle = step_data['Angle'].iloc[0]
            last_angle = step_data['Angle'].iloc[-1]
            differences.append(abs(last_angle - first_angle))
    return differences

def calculate_final_angles(group):
    final_angles = []
    for step in group:
        step_data = df[df['Protocol_Step'] == step]
        if not step_data.empty:
            final_angle = step_data['Angle'].iloc[-1]
            final_angles.append(final_angle)
    return final_angles

def calculate_initial_angles(group):
    initial_angles = []
    for step in group:
        step_data = df[df['Protocol_Step'] == step]
        if not step_data.empty:
            initial_angle = step_data['Angle'].iloc[0]
            initial_angles.append(initial_angle)
    return initial_angles

initial_curve_11 = calculate_initial_angles(group_11)
initial_curve_7 = calculate_initial_angles(group_7)
initial_curve_3 = calculate_initial_angles(group_3)
initial_curve_1 = calculate_initial_angles(group_1)

curve_11 = calculate_differences(group_11)
curve_7 = calculate_differences(group_7)
curve_3 = calculate_differences(group_3)
curve_1 = calculate_differences(group_1)

final_curve_11 = calculate_final_angles(group_11)
final_curve_7 = calculate_final_angles(group_7)
final_curve_3 = calculate_final_angles(group_3)
final_curve_1 = calculate_final_angles(group_1)


# Step 5: Plot the curves for differences
plt.figure(figsize=(8, 5))
plt.plot(x_values, [val + 60 for val in curve_1], marker='d', linestyle=':', label='Initial Cycle (adjusted)', color='red')
plt.plot(x_values, curve_3, marker='^', linestyle='-.', label='Cycle 1', color='orange')
plt.plot(x_values, curve_7, marker='s', linestyle='--', label='Cycle 2', color='green')
plt.plot(x_values, curve_11, marker='o', linestyle='-', label='Cycle 3', color='blue')



# Format the first plot
plt.xlabel('Force Threshold (N)')
plt.ylabel('Range of Motion (degrees)')
plt.title('Range of Motion at different Force Thresholds on Uninjured Arm')
plt.grid()
plt.legend()
plt.tight_layout()
plt.savefig('/Users/alexandergadin/Downloads/20250127_1234_01/range_of_motion.png', dpi=300)

# Step 6: Plot the curves for final angles
plt.figure(figsize=(8, 5))
plt.plot([], [], ' ', label='Initial Cycle (omitted)')
plt.plot(x_values, final_curve_3, marker='^', linestyle='-.', label='Cycle 1', color='orange')
plt.plot(x_values, final_curve_7, marker='s', linestyle='--', label='Cycle 2', color='green')
plt.plot(x_values, final_curve_11, marker='o', linestyle='-', label='Cycle 3', color='blue')


# Format the second plot
plt.xlabel('Force Threshold (N)')
plt.ylabel('Max Device Angle (degrees)')
plt.title('Max device angle at different Force Thresholds on Uninjured Arm')
plt.grid()
plt.legend()
plt.tight_layout()
plt.savefig('/Users/alexandergadin/Downloads/20250127_1234_01/final_angles.png', dpi=300)

# Step 6: Plot the curves for final angle
plt.figure(figsize=(8, 5))
plt.plot(x_values, final_curve_1, marker='d', linestyle=':', label='Cycle 1', color='red')
plt.plot(x_values, initial_curve_3, marker='^', linestyle='-.', label='Cycle 1', color='orange')
plt.plot(x_values, initial_curve_7, marker='s', linestyle='--', label='Cycle 2', color='green')
plt.plot(x_values, initial_curve_11, marker='o', linestyle='-', label='Cycle 3', color='blue')


# Format the second plot
plt.xlabel('Force Threshold (N)')
plt.ylabel('Min Device Angle (degrees)')
plt.title('Minimum device angle at different Force Thresholds on Uninjured Arm')
plt.grid()
plt.legend()
plt.tight_layout()
plt.savefig('/Users/alexandergadin/Downloads/20250127_1234_01/initial_angles.png', dpi=300)
plt.show()

# Function to calculate the average slope of a curve
def calculate_average_slope(x_values, y_values):
    slopes = []
    for i in range(1, len(x_values)):
        slope = (y_values[i] - y_values[i-1]) / (x_values[i] - x_values[i-1])
        slopes.append(slope)
    return np.mean(slopes)

# Calculate average slopes for each curve
average_slope_final_curve_1 = calculate_average_slope(x_values, final_curve_1)
average_slope_initial_curve_3 = calculate_average_slope(x_values, initial_curve_3)
average_slope_initial_curve_7 = calculate_average_slope(x_values, initial_curve_7)
average_slope_initial_curve_11 = calculate_average_slope(x_values, initial_curve_11)

# Calculate the overall average slope
all_slopes = [
    average_slope_final_curve_1,
    average_slope_initial_curve_3,
    average_slope_initial_curve_7,
    average_slope_initial_curve_11
]
overall_average_slope = np.mean(all_slopes)

print(f"Average slope for final_curve_1: {average_slope_final_curve_1}")
print(f"Average slope for initial_curve_3: {average_slope_initial_curve_3}")
print(f"Average slope for initial_curve_7: {average_slope_initial_curve_7}")
print(f"Average slope for initial_curve_11: {average_slope_initial_curve_11}")
print(f"Overall average slope: {overall_average_slope}")


# Function to calculate the average slope of a curve, excluding the first point
def calculate_average_slope(x_values, y_values):
    slopes = []
    for i in range(2, len(x_values)):
        slope = (y_values[i] - y_values[i-1]) / (x_values[i] - x_values[i-1])
        slopes.append(slope)
    return np.mean(slopes)

# Calculate average slopes for each curve, excluding the first point
average_slope_final_curve_3 = calculate_average_slope(x_values, final_curve_3)
average_slope_final_curve_7 = calculate_average_slope(x_values, final_curve_7)
average_slope_final_curve_11 = calculate_average_slope(x_values, final_curve_11)

# Calculate the overall average slope
all_slopes = [
    average_slope_final_curve_3,
    average_slope_final_curve_7,
    average_slope_final_curve_11
]
overall_average_slope = np.mean(all_slopes)

print(f"Average slope for final_curve_3: {average_slope_final_curve_3}")
print(f"Average slope for final_curve_7: {average_slope_final_curve_7}")
print(f"Average slope for final_curve_11: {average_slope_final_curve_11}")
print(f"Overall average slope: {overall_average_slope}")
# Step 6: Plot the curves for final angles
