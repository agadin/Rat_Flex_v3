import sqlite3
import os

DATABASE_PATH = "stepper_motor.db"

def init_db():
    """Initialize the database if it hasn't been initialized yet."""
    # Check if the database file exists
    if os.path.exists(DATABASE_PATH):
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='motor_state';")
            table_exists = cursor.fetchone()

            # If the table exists, mark the database as initialized
            if table_exists:
                print("Database already initialized.")
                return

    print("Initializing database...")

    # Create the database and tables
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Create motor_state table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS motor_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_angle REAL DEFAULT 0,
            current_state TEXT DEFAULT 'idle',
            current_direction TEXT DEFAULT 'idle',
            stop_flag INTEGER DEFAULT 0,
            calibration_detected INTEGER DEFAULT 0,
            angle_to_step_ratio REAL DEFAULT 1.0
        );
        """)

        # Insert initial state if the table was newly created
        cursor.execute("INSERT INTO motor_state (id) VALUES (1);")

        # Mark the database as initialized
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY,
            initialized INTEGER DEFAULT 1
        );
        """)
        cursor.execute("INSERT INTO meta (id, initialized) VALUES (1, 1);")

        conn.commit()
        print("Database initialization complete.")

def check_if_initialized():
    """Check if the database has already been initialized."""
    if not os.path.exists(DATABASE_PATH):
        return False

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT initialized FROM meta WHERE id = 1;")
        result = cursor.fetchone()
        return result is not None and result[0] == 1