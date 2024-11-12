import pymysql
import asyncio
import websockets
import json

# MySQL connection configuration
db_config = {
    "host": "localhost",
    "user": "ratflex",
    "password": "softtissue",
    "database": "motor_control"
}


async def handle_request(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        command = data.get("command")

        with pymysql.connect(**db_config) as connection:
            cursor = connection.cursor()

            if command == "get_motor_state":
                # Query the motor state from the database
                cursor.execute(
                    "SELECT current_angle, current_direction, current_state, angle_to_step_ratio FROM motor_state WHERE id = 1;")
                result = cursor.fetchone()

                if result:
                    # Send back the motor state data
                    await websocket.send(json.dumps({
                        "status": "success",
                        "data": result
                    }))
                else:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Motor state not found"
                    }))

            elif command == "update_motor_state":
                updates = data.get("data", {})
                if updates:
                    # Update the motor state in the database
                    for key, value in updates.items():
                        cursor.execute(f"UPDATE motor_state SET {key} = %s WHERE id = 1;", (value,))
                    connection.commit()
                    await websocket.send(json.dumps({
                        "status": "success",
                        "message": "Motor state updated successfully"
                    }))
                else:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "No data provided for update"
                    }))

            elif command == "stop_motor":
                cursor.execute("UPDATE motor_state SET stop_flag = 1 WHERE id = 1;")
                connection.commit()
                await websocket.send(json.dumps({
                    "status": "motor_stopped",
                    "message": "Motor has been stopped"
                }))

            elif command == "read_stop_motor":
                        cursor.execute("SELECT stop_flag FROM motor_state WHERE id = 1;")
                        result = cursor.fetchone()
                        if result:
                            await websocket.send(json.dumps({
                                "status": "success",
                                "stop_flag": result["stop_flag"]
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "status": "error",
                                "message": "Stop flag not found"
                            }))
            elif command == "get_current_force":
                # Query the motor state from the database
                cursor.execute(
                    "SELECT current_force FROM force_state WHERE id = 1;")
                result = cursor.fetchone()

                if result:
                    # Send back the motor state data
                    await websocket.send(json.dumps({
                        "status": "success",
                        "data": result
                    }))
                else:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Motor state not found"
                    }))
            elif command == "update_current_force":
                updates = data.get("data", {})
                if updates:
                    # Update the motor state in the database
                    for key, value in updates.items():
                        cursor.execute(f"UPDATE force_state SET {key} = %s WHERE id = 1;", (value,))
                    connection.commit()
                    await websocket.send(json.dumps({
                        "status": "success",
                        "message": "Force state updated successfully"
                    }))
                else:
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "No data provided for update"
                    }))
            else:
                # Handle unknown commands
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": f"Unknown command: {command}"
                }))

async def main():
    # Start the WebSocket server on localhost and port 8765
    async with websockets.serve(handle_request, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
