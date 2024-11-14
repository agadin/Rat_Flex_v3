import multiprocessing.shared_memory as shared_memory
import numpy as np

def create_shared_memory():
    try:
        # Create shared memory
        shm = shared_memory.SharedMemory(name='psm_12345', create=True, size=256 * 8)
        shared_data = np.ndarray((256,), dtype=np.float64, buffer=shm.buf)
        return shm, shared_data
    except Exception as e:
        print(f"Error creating shared memory: {e}")
        return None, None

def write_to_shared_memory(shared_data):
    if shared_data is not None:
        # Write some test data to shared memory
        shared_data[0] = 42.0
        shared_data[1] = 3.14
        shared_data[2] = 2.718
    else:
        print("Shared data is None, cannot write to shared memory.")

def read_from_shared_memory():
    try:
        # Access the shared memory
        shm = shared_memory.SharedMemory(name='psm_12345')
        shared_data = np.ndarray((256,), dtype=np.float64, buffer=shm.buf)
        return shared_data[:3]
    except FileNotFoundError:
        print("Shared memory not found.")
        return None
    except Exception as e:
        print(f"Error accessing shared memory: {e}")
        return None

def main():
    # Create and write to shared memory
    shm, shared_data = create_shared_memory()
    if shm is not None and shared_data is not None:
        write_to_shared_memory(shared_data)

        # Read from shared memory
        read_data = read_from_shared_memory()
        if read_data is not None:
            print(f"Read data: {read_data}")

        # Cleanup
        shm.close()
        shm.unlink()
    else:
        print("Failed to create shared memory.")

if __name__ == "__main__":
    main()