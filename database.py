import mysql.connector

# MySQL connection configuration
db_config = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "stepper_motor_db"
}

def init_db():
    """Initialize the database if it hasn't been initialized yet."""
    connection = mysql.connector.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
    )
    cursor = connection.cursor()

    # Create the database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS stepper_motor_db;")
    cursor.execute("USE stepper_motor_db;")

    # Create motor_state table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS motor_state (
        id INT PRIMARY KEY AUTO_INCREMENT,
        current_angle FLOAT DEFAULT 0,
        current_state VARCHAR(50) DEFAULT 'idle',
        current_direction VARCHAR(50) DEFAULT 'idle',
        stop_flag BOOLEAN DEFAULT 0,
        calibration_detected BOOLEAN DEFAULT 0,
        angle_to_step_ratio FLOAT DEFAULT 1.0
    );
    """)

    # Check if the table already has an entry
    cursor.execute("SELECT COUNT(*) FROM motor_state;")
    record_count = cursor.fetchone()[0]

    # If no records exist, insert initial values
    if record_count == 0:
        cursor.execute("""
        INSERT INTO motor_state (
            current_angle,
            current_state,
            current_direction,
            stop_flag,
            calibration_detected,
            angle_to_step_ratio
        ) VALUES (%s, %s, %s, %s, %s, %s);
        """, (0.0, 'idle', 'idle', 0, 0, 1.0))

        print("Inserted initial values into motor_state table.")

    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
    init_db()
    print("Database initialization complete.")
