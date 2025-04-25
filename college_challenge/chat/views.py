# chat/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from users.models import Match
from challenges.models import Challenge

class ChatRoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get match IDs where the user is a participant
        match_ids = Match.objects.filter(
            (models.Q(user1=user) | models.Q(user2=user)) & 
            models.Q(status='ACCEPTED')
        ).values_list('id', flat=True)
        
        # Get chat rooms for those matches
        return ChatRoom.objects.filter(match_id__in=match_ids)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        chat_room = self.get_object()
        user = request.user
        
        # Check if the user is a participant in this chat room
        match = chat_room.match
        if not match or (user != match.user1 and user != match.user2):
            return Response({'error': 'You are not a participant in this chat room'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        content = request.data.get('content')
        if not content:
            return Response({'error': 'Message content is required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Create the message
        message = Message.objects.create(
            chat_room=chat_room,
            sender=user,
            content=content
        )
        
        # Check for chatbot trigger words and respond if needed
        self.check_chatbot_response(chat_room, content)
        
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
    
    def check_chatbot_response(self, chat_room, content):
        # Check if the message contains keywords that should trigger a chatbot response
        content_lower = content.lower()
        
        # Help with using the app
        if 'help' in content_lower or 'how to' in content_lower:
            self.send_chatbot_message(
                chat_room, 
                "Need help? Here are some commands:\n"
                "- 'challenge': Get info about creating challenges\n"
                "- 'rules': Learn about game rules\n"
                "- 'tokens': Understanding the token system"
            )
        
        # Challenge info
        elif 'challenge' in content_lower:
            self.send_chatbot_message(
                chat_room,
                "To create a challenge:\n"
                "1. Match with another student\n"
                "2. Select a game (Coin Flip or Dice Roll)\n"
                "3. Set the number of tokens to wager\n"
                "4. Decide if you want to play now or schedule for later\n"
                "The other student will need to accept your challenge before it begins!"
            )
        
        # Game rules
        elif 'rules' in content_lower or 'how to play' in content_lower:
            if 'coin' in content_lower:
                self.send_chatbot_message(
                    chat_room,
                    "Coin Flip Rules:\n"
                    "- The challenger selects either Heads or Tails\n"
                    "- The coin is flipped\n"
                    "- Winner takes all tokens wagered"
                )
            elif 'dice' in content_lower:
                self.send_chatbot_message(
                    chat_room,
                    "Dice Roll Rules:\n"
                    "- Both players roll a six-sided die\n"
                    "- The higher number wins\n"
                    "- In case of a tie, we'll automatically reroll until there's a winner"
                )
            else:
                self.send_chatbot_message(
                    chat_room,
                    "We currently offer two games:\n"
                    "- Coin Flip: Choose heads or tails\n"
                    "- Dice Roll: Highest roll wins\n"
                    "Ask about specific games for more details!"
                )
        
        # Token info
        elif 'token' in content_lower:
            self.send_chatbot_message(
                chat_room,
                "About Tokens:\n"
                "- You start with 100 virtual tokens\n"
                "- Wager tokens on challenges against other students\n"
                "- Win challenges to increase your token balance\n"
                "- Your token balance is displayed on your profile\n"
                "Remember, these are just virtual tokens for fun and have no monetary value!"
            )
        
        # Friendly reminder about responsible gameplay
        elif 'streak' in content_lower or 'losing' in content_lower:
            self.send_chatbot_message(
                chat_room,
                "Remember that games should be fun! If you're on a losing streak, maybe take a break. The app will still be here when you get back! 😊"
            )
    
    def send_chatbot_message(self, chat_room, content):
        # Create a system user for chatbot messages if it doesn't exist
        system_user, created = User.objects.get_or_create(
            username='ChallengeBotHelper',
            defaults={
                'is_active': False,  # Can't log in
                'profile_picture': None,
                'bio': "I'm the Challenge Bot, here to help you with game rules and app features!"
            }
        )
        
        # Create the chatbot message
        Message.objects.create(
            chat_room=chat_room,
            sender=system_user,
            content=content,
            is_bot=True
        )

@login_required
def chat_room_view(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)
    
    # Ensure the user is a participant in this chat room
    match = chat_room.match
    if not match or (request.user != match.user1 and request.user != match.user2):
        return redirect('home')
    
    # Get the other user in this chat room
    other_user = match.user2 if request.user == match.user1 else match.user1
    
    # Get all messages in this chat room
    messages = Message.objects.filter(chat_room=chat_room).order_by('timestamp')
    
    # Find any challenges related to this match
    challenges = Challenge.objects.filter(match=match).order_by('-created_at')
    
    context = {
        'chat_room': chat_room,
        'other_user': other_user,
        'messages': messages,
        'challenges': challenges
    }
    
    return render(request, 'chat/chat_room.html', context)