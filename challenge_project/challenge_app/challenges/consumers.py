import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChallengeConsumer(AsyncWebsocketConsumer):
    #Accepts WebSocket connections and sends a welcome message.
    async def connect(self):
        # Accept the connection
        await self.accept()
        # Send a welcome message
        await self.send(text_data=json.dumps({
            'message': 'Welcome to the challenge lobby!'
        }))

    #Is set up for cleanup if needed.
    async def disconnect(self, close_code):
        # Perform any necessary cleanup here
        pass
    
    #Echoes back any message it receives in a simple JSON payload.
    async def receive(self, text_data):
        # Parse the incoming message
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        # Echo the message back to the client (or broadcast it)
        await self.send(text_data=json.dumps({
            'message': message,
        }))