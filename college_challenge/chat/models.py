# chat/models.py
from django.db import models
from users.models import User, Match

class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('DIRECT', 'Direct Chat'),
        ('LOBBY', 'Challenge Lobby'),
    )
    
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='chat_room')
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='DIRECT')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chat: {self.match.user1.username} & {self.match.user2.username}"

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_bot = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        sender_name = "Chatbot" if self.is_bot else self.sender.username
        return f"{sender_name}: {self.content[:50]}"

    @classmethod
    def create_bot_message(cls, chat_room, content):
        return cls.objects.create(
            chat_room=chat_room,
            content=content,
            is_bot=True
        )