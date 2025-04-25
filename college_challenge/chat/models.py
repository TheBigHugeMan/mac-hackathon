from django.db import models

# Create your models here.
# chat/models.py

from users.models import User, Match

class ChatRoom(models.Model):
    TYPE_CHOICES = [
        ('DIRECT', 'Direct Message'),
        ('LOBBY', 'Challenge Lobby'),
    ]
    
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='chat_room', null=True, blank=True)
    room_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.match:
            return f"Chat: {self.match.user1.username} and {self.match.user2.username}"
        return f"Chat Room {self.id}"

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_bot = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"