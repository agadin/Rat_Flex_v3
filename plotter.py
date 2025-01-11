import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define headers for the CSV
headers = ['Time', 'Angle', 'Force', 'raw_Force', 'Motor_State', 'Direction', 'Protocol_Step']

# Read the CSV file
data = pd.read_csv('data.csv', header=None, names=headers, na_filter=False)

# if there are any 6 column rows, we will need to adjust the raw_Force values

if data['Protocol_Step'].str.len().eq(0).any():
    # Identify rows with 6 or 7 columns
    data['Row_Type'] = data['Protocol_Step'].apply(lambda x: '6_column' if x == '' else '7_column')

    # Convert 'Force' and 'raw_Force' to numeric
    data['Force'] = pd.to_numeric(data['Force'], errors='coerce')
    data['raw_Force'] = pd.to_numeric(data['raw_Force'], errors='coerce')

    # Function to adjust the 6-column rows
    def fix_data_rows(data):
        fixed_data = []
        last_diff = 0  # Difference between Force and raw_Force for the last 7-column row

        for _, row in data.iterrows():
            if row['Row_Type'] == '7_column':
                # Update the difference for 7-column rows
                last_diff = row['raw_Force'] - row['Force']
                fixed_data.append(row)
            elif row['Row_Type'] == '6_column':
                # Adjust the 6-column row
                new_row = row.copy()
                # Insert the adjusted raw_Force value
                new_row['raw_Force'] = new_row['Force'] + last_diff
                fixed_data.append(new_row)

        return pd.DataFrame(fixed_data)

    # Function to fix rows with missing columns
    def fix_rows(data):
        fixed_data = []
        for _, row in data.iterrows():
            if row['Row_Type'] == '6_column':
                new_row = row.copy()
                new_row['Protocol_Step'] = new_row['Direction']
                new_row['Direction'] = new_row['Motor_State']
                fixed_data.append(new_row)
            else:
                fixed_data.append(row)
        return pd.DataFrame(fixed_data)

    # Fix the data
    fixed_data = fix_data_rows(data)
    fixed_data = fix_rows(fixed_data)

    # Save the fixed data to a new CSV file
    fixed_data.to_csv('fixed_data.csv', index=False)
else:
    fixed_data = data

# Extract relevant columns
angle = fixed_data['Angle']
force = fixed_data['Force']
raw_force = fixed_data['raw_Force']

# Plot Angle vs. Force and raw_Force
plt.figure(figsize=(10, 8))
plt.plot(angle, force, label='Force', marker='o', linestyle='-', color='b')
plt.title('Angle vs. Force', fontsize=16)
plt.xlabel('Angle (degrees)', fontsize=14)
plt.ylabel('Force (N)', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True)
plt.show()

# Plot Angle vs. Force and raw_Force
plt.figure(figsize=(10, 8))
plt.plot(angle, force, label='Force', marker='o', linestyle='-', color='b')
plt.plot(angle, raw_force, label='raw_Force', marker='x', linestyle='--', color='r')
plt.title('Angle vs. Force and raw_Force', fontsize=16)
plt.xlabel('Angle (degrees)', fontsize=14)
plt.ylabel('Force (N)', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True)
plt.show()

# Extract relevant columns
protocol_step = pd.to_numeric(fixed_data['Protocol_Step'], errors='coerce')

# Plot Angle vs. Force with Protocol_Step 1 in red
plt.figure(figsize=(10, 8))
plt.plot(angle[protocol_step == 1], force[protocol_step == 1], color='red', marker='o',label='Protocol_Step 1', zorder=2)
plt.plot(angle[protocol_step != 1], force[protocol_step != 1], color='blue', marker='o', label='Other Protocol_Steps', zorder=1)
plt.title('Angle vs. Force', fontsize=16)
plt.xlabel('Angle (degrees)', fontsize=14)
plt.ylabel('Force (N)', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True)
plt.show()

protocol_step = pd.to_numeric(fixed_data['Protocol_Step'], errors='coerce')
# Count rows for each Protocol_Step (excluding Protocol_Step 1)
# Count rows for each Protocol_Step (excluding Protocol_Step 1 and even steps)
filtered_data = fixed_data[(protocol_step != 1) & (protocol_step % 2 != 0)]
protocol_counts = filtered_data['Protocol_Step'].value_counts().sort_index()

# Calculate standard deviation for the final bar values
std_dev = protocol_counts.std()
print(f"Standard Deviation of Protocol_Step counts: {std_dev}")

# Ensure protocol_counts is sorted numerically by Protocol_Step
protocol_counts = protocol_counts.sort_index()

# Explicitly convert the index to integer for proper sorting (if needed)
protocol_counts.index = protocol_counts.index.astype(int)
protocol_counts = protocol_counts.sort_index()

# Plot bar graph of Protocol_Step counts in ascending order
plt.figure(figsize=(10, 6))
protocol_counts.plot(kind='bar', color='green', edgecolor='black')
plt.title('Count of Rows for Odd Protocol_Steps', fontsize=16)
plt.xlabel('Protocol_Step', fontsize=14)
plt.ylabel('Count', fontsize=14)
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Create a heatmap of Force and Angle
plt.figure(figsize=(10, 8))
heatmap_data = fixed_data.pivot_table(values='Force', index='Angle', aggfunc='mean')
sns.heatmap(heatmap_data, cmap='coolwarm', cbar_kws={'label': 'Force (N)'})
plt.title('Heatmap of Force vs. Angle', fontsize=16)
plt.xlabel('Angle (degrees)', fontsize=14)
plt.ylabel('Force (N)', fontsize=14)
plt.show()

# Create a histogram of Angles
plt.figure(figsize=(10, 6))
plt.hist(angle, bins=30, color='skyblue', edgecolor='black')
plt.title('Histogram of Angles', fontsize=16)
plt.xlabel('Angle (degrees)', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Create a correlation matrix
correlation_matrix = fixed_data[['Angle', 'Force', 'raw_Force']].corr()
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', cbar_kws={'label': 'Correlation Coefficient'})
plt.title('Correlation Matrix', fontsize=16)
plt.show()



# Force vs. raw_Force Scatter Plot
plt.figure(figsize=(10, 8))
plt.scatter(force, raw_force, alpha=0.7, color='purple', edgecolor='black')
plt.title('Force vs. raw_Force', fontsize=16)
plt.xlabel('Force (N)', fontsize=14)
plt.ylabel('raw_Force (N)', fontsize=14)
plt.grid(True)
plt.tight_layout()
plt.show()

# Force Distribution by Protocol_Step
plt.figure(figsize=(10, 8))
sns.boxplot(x='Protocol_Step', y='Force', data=fixed_data)
plt.title('Force Distribution by Protocol_Step', fontsize=16)
plt.xlabel('Protocol_Step', fontsize=14)
plt.ylabel('Force (N)', fontsize=14)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()


# Calculate elapsed time for each Direction block
fixed_data['Time'] = pd.to_numeric(fixed_data['Time'], errors='coerce')
fixed_data['Direction'] = fixed_data['Direction'].astype('category')
time_differences = fixed_data.groupby((fixed_data['Direction'] != fixed_data['Direction'].shift()).cumsum())
block_durations = time_differences.agg({'Time': lambda x: x.iloc[-1] - x.iloc[0], 'Direction': 'first'}).reset_index(drop=True)

# Filter out idle blocks and durations less than 4 seconds
block_durations = block_durations[block_durations['Time'] >= 4]

# Add a relative order column for each direction
block_durations['Relative_Order'] = block_durations.groupby('Direction').cumcount() + 1

# Plot durations with better formatting
plt.figure(figsize=(10, 8))
sns.scatterplot(x='Direction', y='Time', hue='Relative_Order', size='Relative_Order', data=block_durations, palette='viridis', sizes=(50, 200), alpha=0.65)
plt.title('Time Spent in Each Direction', fontsize=16)
plt.xlabel('Direction', fontsize=14)
plt.ylabel('Time Elapsed (s)', fontsize=14)
plt.legend(title='Relative Order', fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Force and Direction Over Time
plt.figure(figsize=(14, 8))
force = fixed_data['Force']
direction = fixed_data['Direction']
time = fixed_data['Time']

# Normalize Direction to distinct numeric values for visualization
direction_mapping = {'idle': 0, 'forward': 1, 'backward': -1}
fixed_data['Direction_numeric'] = fixed_data['Direction'].map(direction_mapping)

# Plot Force
plt.plot(time, force, label='Force (N)', color='blue', alpha=0.7)

# Plot Direction
plt.fill_between(time, fixed_data['Direction_numeric'], step='mid', alpha=0.3, label='Direction', color='orange')

plt.title('Force and Direction Over Time', fontsize=16)
plt.xlabel('Time', fontsize=14)
plt.ylabel('Force (N) / Direction', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True)
plt.tight_layout()
plt.show()



