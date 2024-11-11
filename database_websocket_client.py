import json
import asyncio
from websockets.asyncio.client import connect

class DatabaseWebSocketClient:
    def __init__(self, server_url="ws://localhost:8765"):
        """Initialize the WebSocket client with the server URL."""
        self.server_url = server_url

    async def send_db_command(self, command, data=None):
        """Send a command to the WebSocket database server and return the response."""
        async with connect(self.server_url) as websocket:
            message = {
                "command": command,
                "data": data or {}  # Send data as an empty dictionary if none is provided
            }

            # Send the command as a JSON message
            await websocket.send(json.dumps(message))

            # Receive the response from the server
            response = await websocket.recv()
            return json.loads(response)

    async def update_db(self, current_direction=None, current_angle=None, angle_to_step_ratio=None, motor_state=None):
        """Update the motor state in the database using WebSocket."""
        data = {}

        # Build the data dictionary if any value is provided
        if current_direction is not None:
            data["current_direction"] = current_direction
        if current_angle is not None:
            data["current_angle"] = current_angle
        if angle_to_step_ratio is not None:
            data["angle_to_step_ratio"] = angle_to_step_ratio
        if motor_state is not None:
            data["current_state"] = motor_state

        # Send the update command to the WebSocket server
        response = await self.send_db_command("update_motor_state", data)
        return response  # Return the server's response (success or error)

    async def close(self):
        """Close the WebSocket connection."""
        # No explicit close needed with async with context manager

# Example usage:
if __name__ == "__main__":
    async def main():
        # Initialize the WebSocket client
        db_client = DatabaseWebSocketClient()

        # Example: Update the motor state
        response = await db_client.update_db(current_direction="forward", current_angle=90, motor_state="moving")
        print("Response from WebSocket server:", response)

    asyncio.run(main())