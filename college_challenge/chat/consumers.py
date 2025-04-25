# chat/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Load chat history
        messages = await self.get_chat_history()
        if messages:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'messages': messages
            }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Save the message to the database
        user = self.scope["user"]
        msg_obj = await self.save_message(user.id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': user.username,
                'timestamp': msg_obj['timestamp'].isoformat(),
                'message_id': msg_obj['id']
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
    
    @database_sync_to_async
    def get_chat_history(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            messages = Message.objects.filter(
                room=room
            ).order_by('timestamp')[:50]  # Last 50 messages
            
            return [
                {
                    'message': msg.content,
                    'username': msg.sender.username,
                    'timestamp': msg.timestamp.isoformat(),
                    'message_id': msg.id
                }
                for msg in messages
            ]
        except ChatRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, user_id, content):
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=self.room_id)
        
        msg = Message.objects.create(
            sender=user,
            room=room,
            content=content
        )
        
        return {
            'id': msg.id,
            'timestamp': msg.timestamp
        }