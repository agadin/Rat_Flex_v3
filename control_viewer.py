# This will be a streamlit page that allows the viewing of the current position of the arm, its current target and control the arm (stop, start, pause)
# Data will be stored as files on the device and read from the device. The data will be stored in a test specific manner (ie for each test conducted a corresponding folder will be created). Thus, the data will be stored in a folder that is named after the test located in the folder called tests. To find the current test a current_test.txt file stored in the main directory will direct the user. This file will contain the folder name and current state of the test (active, stopper, paused). The data inside the folder named after the test be stored in the following format:
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

# the upadting of the elements will occur if the testing is active. The user can also indicate the refresh interval