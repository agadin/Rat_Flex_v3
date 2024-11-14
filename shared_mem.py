import multiprocessing.shared_memory as sm
import struct
import time
import threading

# Define the shared memory size (32 bytes for stop_flag, step_count, current_angle, current_force)
shm_name = 'shared_data'
shm_size = struct.calcsize('i d d d')  # 4 bytes for int, 3 doubles (8 bytes each)

# Packing format: (stop_flag, step_count, current_angle, current_force)
fmt = 'i d d d'
shm = sm.SharedMemory(create=True, name=shm_name, size=shm_size)


# Function to write data to shared memory (simulates the main script)
def write_to_shared_memory(shm):
    for i in range(100):
        # Prepare data to write into shared memory
        stop_flag = 0
        step_count = i
        current_angle = i * 0.1
        current_force = 5.0

        # Pack the data into bytes
        packed_data = struct.pack(fmt, stop_flag, step_count, current_angle, current_force)

        # Write packed data to shared memory
        shm.buf[:len(packed_data)] = packed_data
        print(f"Writing data: Step {step_count}, Angle {current_angle}, Force {current_force}")

        # Sleep to simulate work
        time.sleep(0.1)

    # Set the stop flag to 1 after writing
    stop_flag = 1
    packed_data = struct.pack(fmt, stop_flag, step_count, current_angle, current_force)
    shm.buf[:len(packed_data)] = packed_data
    print("Stop flag set. Writing complete.")


# Function to read data from shared memory (simulates the worker script)
def read_from_shared_memory(shm):
    while True:
        # Read the data from shared memory
        data = bytes(shm.buf[:struct.calcsize(fmt)])
        stop_flag, step_count, current_angle, current_force = struct.unpack(fmt, data)

        print(f"Read data: Step {step_count}, Angle {current_angle}, Force {current_force}")

        if stop_flag == 1:
            print("Stop flag set. Exiting.")
            break

        time.sleep(0.05)  # Simulate delay in reading


# Create shared memory block
shm = sm.SharedMemory(create=True, name=shm_name, size=shm_size)

# Start writing and reading in parallel using threads
write_thread = threading.Thread(target=write_to_shared_memory, args=(shm,))
read_thread = threading.Thread(target=read_from_shared_memory, args=(shm,))

write_thread.start()
read_thread.start()

# Wait for both threads to finish
write_thread.join()
read_thread.join()

# Clean up the shared memory after use
shm.close()
shm.unlink()  # Delete the shared memory block after use
