# chat/serializers.py
from rest_framework import serializers
from .models import ChatRoom, Message
from users.serializers import UserCardSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserCardSerializer(read_only=True)
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'content', 'timestamp', 'is_bot']
    
    def get_sender_name(self, obj):
        if obj.is_bot:
            return "Chatbot"
        elif obj.sender:
            return obj.sender.username
        return "Unknown"

class CreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['chat_room', 'content']
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Message.objects.create(
            sender=user,
            **validated_data
        )

class ChatRoomSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'room_type', 'created_at', 'participant_names', 'latest_message']
    
    def get_latest_message(self, obj):
        message = obj.messages.order_by('-timestamp').first()
        if message:
            return MessageSerializer(message).data
        return None
    
    def get_participant_names(self, obj):
        return [obj.match.user1.username, obj.match.user2.username]