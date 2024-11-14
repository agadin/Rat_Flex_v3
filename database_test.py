import multiprocessing.shared_memory as sm
import struct
import time

# Define shared memory block size and format
shm_name = 'shared_data'
shm_size = struct.calcsize('i d d d')  # 4 bytes for int, 3 doubles (8 bytes each)
fmt = 'i d d d'  # Format for packing (stop_flag, step_count, current_angle, current_force)

# Create shared memory block
shm = sm.SharedMemory(create=True, name=shm_name, size=shm_size)

# Write data to shared memory
for i in range(100):
    stop_flag = 0
    step_count = i
    current_angle = i * 0.1
    current_force = 5.0

    # Pack the data into bytes
    packed_data = struct.pack(fmt, stop_flag, step_count, current_angle, current_force)

    # Write packed data to the shared memory block
    shm.buf[:len(packed_data)] = packed_data
    print(f"Writing data: Step {step_count}, Angle {current_angle}, Force {current_force}")

    # Sleep to simulate some delay between writes
    time.sleep(0.1)

# After writing, set the stop flag
stop_flag = 1
packed_data = struct.pack(fmt, stop_flag, step_count, current_angle, current_force)
shm.buf[:len(packed_data)] = packed_data
print("Stop flag set. Writing complete.")

# Close the shared memory after use
shm.close()
