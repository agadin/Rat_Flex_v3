import struct
import time
import multiprocessing.shared_memory as sm

def read_shared_memory():
    shm_name = 'shared_data'
    fmt = 'i d d d'
    shm_size = struct.calcsize(fmt)
    log_file = 'shared_memory_debug.log'

    try:
        shm = sm.SharedMemory(name=shm_name, create=False)
    except FileNotFoundError:
        print(f"Shared memory {shm_name} not found.")
        return

    with open(log_file, 'a') as f:
        while True:
            print("Reading shared memory...")
            try:
                data = bytes(shm.buf[:shm_size])
                stop_flag, step_count, current_angle, current_force = struct.unpack(fmt, data)
                log_entry = f"Stop Flag: {stop_flag}, Step Count: {step_count}, Current Angle: {current_angle}, Current Force: {current_force}\n"
                f.write(log_entry)
                f.flush()
                time.sleep(0.5)  # Adjust the sleep time as needed
            except Exception as e:
                f.write(f"Error reading shared memory: {e}\n")
                f.flush()
                time.sleep(1)  # Wait before retrying

if __name__ == "__main__":
    read_shared_memory()