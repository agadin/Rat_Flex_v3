import multiprocessing.shared_memory as sm
import struct
import time

# Define the shared memory name and format
shm_name = 'shared_data'
fmt = 'i d d d'  # Format for unpacking (stop_flag, step_count, current_angle, current_force)

# Attach to the existing shared memory
shm = sm.SharedMemory(name=shm_name)

# Read data from the shared memory
while True:
    # Read the data from shared memory
    data = bytes(shm.buf[:struct.calcsize(fmt)])
    stop_flag, step_count, current_angle, current_force = struct.unpack(fmt, data)

    # Print the read data
    print(f"Read data: Step {step_count}, Angle {current_angle}, Force {current_force}")

    # If the stop flag is set to 1, exit the loop
    if stop_flag == 1:
        print("Stop flag set. Exiting.")
        break

    # Sleep to simulate a delay in reading
    time.sleep(0.05)

# Close the shared memory after use
shm.close()
