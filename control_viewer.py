# This will be a streamlit page that allows the viewing of the current position of the arm, its current target and control the arm (stop, start, pause)
# Data will be stored as files on the device and read from the device. The data will be stored in a test specific manner (ie for each test conducted a corresponding folder will be created). Thus, the data will be stored in a folder that is named after the test located in the folder called tests. To find the current test a current_test.txt file stored in the main directory will direct to the current test. This file will contain the folder name, current state of the test (active, stopper, paused), and the current calibration file. current_test.txt will also have the current force and angle read out. The data inside the folder named after the test be stored in the following format:
# 1. A file called test_schedule.txt that contains the test schedule. The test schedule will be stored in the following format:
# test_schedule.txt
# test_name: test_name
# test_description: test_description
# 2. a file that contains the current positions and force values along with a timestamp. This file will be called test_data.txt and will be stored in the following format:
# test_data.txt
# timestamp, position, force
# 3. a file that contains the current target position. This file will be called target_position.txt and will be stored in the following format:
# target_position.txt
# target_position


# This page will have four main elements:
# 1. A current numerical position of the arm with current force readout (from the force sensor) and current target position using the st.metric() function
# 2. A updating picture of the arm that illustrates the current position of the arm (this will be done using pictures of the arm in different positions and updating the picture based on the current position). This will be done using the st.empty() function and updating the picture using the st.image() function. There will be different stiles of images (stored in subfolders inside the img folder) that have different appearenaces.
# 3. A control panel that allows the user to start, stop and pause the arm. This will be done using the st.button() function. These buttons will be horizontally aligned.
# 4. Test schedule viewer: this section will allow the user to view the current test schedule and the next test to be performed. This will be done using the st.table() function. This will read a file that contains the test schedule and display it in a table format. The table will have the following columns: . The table will be updated every 5 depending on if the current testing state is active or paused/stoped. The table will be updated using the st.empty() function and updating the table using the st.table() function.

# the upadting of the elements will occur if the testing is active. The user can also indicate the refresh interval along with an adjacent mannual refresh button. When the test is not active the page will not update automatically.

# The current force will be read from the class in force_sensor.py
# The current position will be read from the class in stepper_motor.py

# main while loop that will update the page when the test is active

import streamlit as st
import time

def get_current_test_info(file_path='current_test.txt'):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            test_info = {}
            for line in lines:
                key, value = line.strip().split(': ')
                test_info[key] = value
            return test_info
    except FileNotFoundError:
        st.error(f"File {file_path} not found.")
        return None
    except Exception as e:
        st.error(f"An error occurred while reading {file_path}: {e}")
        return None

def load_page_content():
    test_info = get_current_test_info()
    if test_info:
        current_test_folder = test_info.get('folder_name')
        test_state = test_info.get('state')
        calibration_file = test_info.get('calibration_file')
        current_force = test_info.get('current_force')
        current_angle = test_info.get('current_angle')

        st.metric(label="Current Force", value=current_force)
        st.metric(label="Current Angle", value=current_angle)
        st.metric(label="Current Test Folder", value=current_test_folder)
        st.metric(label="Test State", value=test_state)
        st.metric(label="Calibration File", value=calibration_file)

# Initial load
load_page_content()

# Main loop to check the state
while True:
    test_info = get_current_test_info()
    if test_info and test_info.get('state') == 'active':
        load_page_content() # 1st element
    time.sleep(5)  # Check every 5 seconds
# 1st element

# 2nd element

# 3rd element


# 4th element

