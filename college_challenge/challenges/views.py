# challenges/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required

from .models import Challenge, CoinFlipGame, DiceRollGame, Transaction
from .serializers import ChallengeSerializer, CreateChallengeSerializer, AcceptChallengeSerializer
from users.models import Match

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter challenges to only show relevant ones for the current user"""
        user = self.request.user
        return Challenge.objects.filter(
            models.Q(challenger=user) | models.Q(opponent=user)
        )
    
    def get_serializer_class(self):
        if self.action == 'create_challenge':
            return CreateChallengeSerializer
        elif self.action == 'accept_challenge':
            return AcceptChallengeSerializer
        return ChallengeSerializer
    
    @action(detail=False, methods=['post'])
    def create_challenge(self, request):
        """Create a new challenge after matching"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        match_id = serializer.validated_data.get('match').id
        match = get_object_or_404(Match, id=match_id)
        
        # Verify the current user is part of this match
        if request.user not in [match.user1, match.user2]:
            return Response({"error": "Not authorized to create challenge for this match"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Set context for serializer to access request
        serializer.context['request'] = request
        challenge = serializer.save()
        
        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept_challenge(self, request, pk=None):
        """Accept a pending challenge"""
        challenge = self.get_object()
        user = request.user
        
        # Verify user is the opponent in this challenge
        if user != challenge.opponent:
            return Response({"error": "Only the opponent can accept this challenge"}, 
                          status=status.HTTP_403_FORBIDDEN)
                           
        if challenge.status != 'PENDING':
            return Response({"error": f"Challenge is already {challenge.get_status_display()}"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Use serializer to handle game details if provided
        serializer = self.get_serializer(challenge, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Try to accept the challenge
        success = challenge.accept()
        if not success:
            return Response({"error": "Insufficient tokens to accept challenge"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        return Response(ChallengeSerializer(challenge).data)
    
    @action(detail=True, methods=['post'])
    def execute_challenge(self, request, pk=None):
        """Execute the challenge to determine winner"""
        challenge = self.get_object()
        
        if challenge.status != 'ACCEPTED':
            return Response({"error": "Challenge must be accepted before execution"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Execute the game and determine winner
        if hasattr(challenge, 'coin_flip'):
            game = challenge.coin_flip
            success = game.execute()
            if success:
                result = game.result
            else:
                return Response({"error": "Failed to execute coin flip"}, 
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif hasattr(challenge, 'dice_roll'):
            game = challenge.dice_roll
            success = game.execute()
            if success:
                result = f"{game.challenger_roll} vs {game.opponent_roll}"
            else:
                return Response({"error": "Failed to execute dice roll"}, 
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Unknown game type"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Return updated challenge data
        return Response({
            "challenge": ChallengeSerializer(challenge).data,
            "winner": challenge.winner.username,
            "tokens_won": challenge.wager * 2,
            "result": result
        })

@login_required
def challenge_list(request):
    """View to display all challenges for the current user"""
    user = request.user
    
    # Get all challenges involving the user
    challenges = Challenge.objects.filter(
        models.Q(challenger=user) | models.Q(opponent=user)
    ).order_by('-created_at')
    
    # Separate challenges by status for easier display
    pending_challenges = challenges.filter(status='PENDING')
    active_challenges = challenges.filter(status='ACCEPTED')
    completed_challenges = challenges.filter(status__in=['COMPLETED', 'CANCELED', 'REJECTED'])
    
    context = {
        'pending_challenges': pending_challenges,
        'active_challenges': active_challenges,
        'completed_challenges': completed_challenges
    }
    
    return render(request, 'challenges/my_challenges.html', context)

@login_required
def create_challenge(request, match_id):
    """View to create a new challenge"""
    match = get_object_or_404(Match, id=match_id)
    
    # Verify the user is part of this match
    if request.user not in [match.user1, match.user2]:
        return redirect('home')
    
    if request.method == 'POST':
        # Create challenge using form data
        game_type = request.POST.get('game_type')
        wager = int(request.POST.get('wager', 10))
        
        # Set challenger and opponent
        if match.user1 == request.user:
            challenger = match.user1
            opponent = match.user2
        else:
            challenger = match.user2
            opponent = match.user1
        
        # Create the challenge
        challenge = Challenge.objects.create(
            match=match,
            challenger=challenger,
            opponent=opponent,
            game_type=game_type,
            wager=wager
        )
        
        # Create game-specific details
        if game_type == 'COIN_FLIP':
            choice = request.POST.get('choice', 'HEADS')
            CoinFlipGame.objects.create(
                challenge=challenge,
                challenger_choice=choice
            )
        elif game_type == 'DICE_ROLL':
            challenger_guess = request.POST.get('challenger_guess')
            if challenger_guess:
                challenger_guess = int(challenger_guess)
            
            DiceRollGame.objects.create(
                challenge=challenge,
                challenger_guess=challenger_guess
            )
            
        # Redirect to chat room with the challenge
        chat_room = match.chat_room
        return redirect('chatroom', room_id=chat_room.id)
    
    # Display form for creating challenge
    context = {
        'match': match,
        'other_user': match.user2 if request.user == match.user1 else match.user1
    }
    
    return render(request, 'challenges/create_challenge.html', context)

@login_required
def challenge_detail(request, pk):
    """View to display details of a specific challenge"""
    challenge = get_object_or_404(Challenge, id=pk)
    
    # Verify the user is a participant in this challenge
    if request.user not in [challenge.challenger, challenge.opponent]:
        return redirect('home')
    
    context = {
        'challenge': challenge,
        'is_challenger': request.user == challenge.challenger
    }
    
    return render(request, 'challenges/challenge_detail.html', context)