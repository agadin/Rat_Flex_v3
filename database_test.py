import sqlite3
import os
import time
from database import init_db, DATABASE_PATH


def test_init_db():
    """Test the init_db function."""
    # Run init_db to initialize the database
    init_db()

    # Verify that the database file exists
    if os.path.exists(DATABASE_PATH):
        print(f"Database file '{DATABASE_PATH}' exists.")
    else:
        print(f"Database file '{DATABASE_PATH}' does not exist.")

    # Connect to the database and check the motor_state table
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Check if motor_state table exists and has data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='motor_state';")
            if cursor.fetchone():
                print("motor_state table exists.")
                cursor.execute("SELECT * FROM motor_state;")
                rows = cursor.fetchall()
                if rows:
                    print("motor_state table contains data:", rows)
                else:
                    print("motor_state table is empty.")
            else:
                print("motor_state table does not exist.")

            # Check if the meta table exists and is initialized
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta';")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM meta;")
                rows = cursor.fetchall()
                if rows:
                    print("meta table contains data:", rows)
                else:
                    print("meta table is empty.")
            else:
                print("meta table does not exist.")
    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")

# Run the test
test_init_db()
