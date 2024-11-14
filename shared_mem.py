import multiprocessing.shared_memory as shared_memory
import numpy as np


def create_shared_memory():
    # Create shared memory
    shm = shared_memory.SharedMemory(name='psm_12345', create=True, size=256 * 8)
    shared_data = np.ndarray((256,), dtype=np.float64, buffer=shm.buf)
    return shm, shared_data


def write_to_shared_memory(shared_data):
    # Write some test data to shared memory
    shared_data[0] = 42.0
    shared_data[1] = 3.14
    shared_data[2] = 2.718


def read_from_shared_memory():
    # Access the shared memory
    shm = shared_memory.SharedMemory(name='psm_12345')
    shared_data = np.ndarray((256,), dtype=np.float64, buffer=shm.buf)
    return shared_data[:3]


def main():
    # Create and write to shared memory
    shm, shared_data = create_shared_memory()
    write_to_shared_memory(shared_data)

    # Read from shared memory
    read_data = read_from_shared_memory()
    print(f"Read data: {read_data}")

    # Cleanup
    shm.close()
    shm.unlink()


if __name__ == "__main__":
    main()