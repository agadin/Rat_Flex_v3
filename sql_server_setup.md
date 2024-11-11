
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
sudo systemctl start mysql

```

# Log into MySQL

```bash
mysql -u root -p
``` 

# Create a database and user
    
    ```sql
CREATE DATABASE motor_control;
CREATE USER 'your_username'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON motor_control.* TO 'your_username'@'localhost';
FLUSH PRIVILEGES;
    ```

# Create a table
    
```sql
USE motor_control;

CREATE TABLE motor_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    current_angle INT DEFAULT 0,
    current_direction VARCHAR(255) DEFAULT 'idle',
    motor_state VARCHAR(255) DEFAULT 'idle',
    angle_to_step_ratio FLOAT DEFAULT 1.0
);
```
USE motor_control;

CREATE TABLE force_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    force_state VARCHAR(255) DEFAULT 'idle',
    force_value FLOAT DEFAULT 0.0
);
```sql

```
## Example row change
```sql
ALTER TABLE motor_state CHANGE motor_state current_state VARCHAR(255) DEFAULT 'idle';
```

# Data verification

```sql
SELECT * FROM motor_state;
```

# Websocket server

```bash
pip install websockets asyncio mysql-connector-python
```
