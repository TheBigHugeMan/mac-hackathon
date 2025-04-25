# Create your views here.
# challenges/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Challenge, CoinFlipGame, DiceRollGame, Transaction
from .serializers import ChallengeSerializer, CreateChallengeSerializer, TransactionSerializer
from users.models import Match, User
import random

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateChallengeSerializer
        return ChallengeSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        opponent_id = serializer.validated_data['opponent'].id
        game_type = serializer.validated_data['game_type']
        token_wager = serializer.validated_data['token_wager']
        scheduled_time = serializer.validated_data.get('scheduled_time')
        
        # Get the match between the users
        match = get_object_or_404(
            Match, 
            (models.Q(user1=request.user, user2_id=opponent_id) | 
             models.Q(user2=request.user, user1_id=opponent_id)),
            status='ACCEPTED'
        )
        
        # Check if user has enough tokens
        if request.user.token_balance < token_wager:
            return Response({'error': 'Not enough tokens'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the challenge
        challenge = Challenge.objects.create(
            match=match,
            challenger=request.user,
            opponent_id=opponent_id,
            game_type=game_type,
            token_wager=token_wager,
            scheduled_time=scheduled_time
        )
        
        # Create the specific game instance
        if game_type == 'COIN_FLIP':
            CoinFlipGame.objects.create(
                challenge=challenge,
                challenger_choice='HEADS'  # Default choice, can be updated later
            )
        elif game_type == 'DICE_ROLL':
            DiceRollGame.objects.create(
                challenge=challenge
            )
        
        # Reserve the tokens
        Transaction.objects.create(
            user=request.user,
            challenge=challenge,
            amount=-token_wager,
            transaction_type='WAGER'
        )
        request.user.token_balance -= token_wager
        request.user.save()
        
        # Create a lobby chat room
        from chat.models import ChatRoom
        lobby = ChatRoom.objects.create(
            room_type='LOBBY'
        )
        
        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)
    
    # challenges/views.py (continued)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        challenge = self.get_object()
        
        # Check if the user is the opponent
        if request.user != challenge.opponent:
            return Response({'error': 'You are not the opponent of this challenge'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Check if the challenge is still pending
        if challenge.status != 'PENDING':
            return Response({'error': 'Challenge is not pending'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has enough tokens
        if request.user.token_balance < challenge.token_wager:
            return Response({'error': 'Not enough tokens'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update the challenge status
            challenge.status = 'ACCEPTED'
            challenge.save()
            
            # Reserve the tokens
            Transaction.objects.create(
                user=request.user,
                challenge=challenge,
                amount=-challenge.token_wager,
                transaction_type='WAGER'
            )
            request.user.token_balance -= challenge.token_wager
            request.user.save()
            
            # If the challenge is scheduled for now, execute it immediately
            if not challenge.scheduled_time or challenge.scheduled_time <= timezone.now():
                self.execute_challenge(challenge)
        
        return Response(ChallengeSerializer(challenge).data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        challenge = self.get_object()
        
        # Check if the user is the opponent
        if request.user != challenge.opponent:
            return Response({'error': 'You are not the opponent of this challenge'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Check if the challenge is still pending
        if challenge.status != 'PENDING':
            return Response({'error': 'Challenge is not pending'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update the challenge status
            challenge.status = 'DECLINED'
            challenge.save()
            
            # Return tokens to the challenger
            Transaction.objects.create(
                user=challenge.challenger,
                challenge=challenge,
                amount=challenge.token_wager,
                transaction_type='WINNINGS'
            )
            challenge.challenger.token_balance += challenge.token_wager
            challenge.challenger.save()
        
        return Response(ChallengeSerializer(challenge).data)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        challenge = self.get_object()
        
        # Check if the user is a participant
        if request.user != challenge.challenger and request.user != challenge.opponent:
            return Response({'error': 'You are not a participant in this challenge'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Check if the challenge is accepted
        if challenge.status != 'ACCEPTED':
            return Response({'error': 'Challenge is not accepted'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Execute the challenge
        result = self.execute_challenge(challenge)
        
        return Response(result)
    
    def execute_challenge(self, challenge):
        if challenge.game_type == 'COIN_FLIP':
            return self.execute_coin_flip(challenge)
        elif challenge.game_type == 'DICE_ROLL':
            return self.execute_dice_roll(challenge)
        return {'error': 'Unknown game type'}
    
    def execute_coin_flip(self, challenge):
        coin_flip = challenge.coin_flip
        
        # Determine the result
        result = random.choice(['HEADS', 'TAILS'])
        coin_flip.result = result
        coin_flip.save()
        
        # Determine the winner
        winner = challenge.challenger if coin_flip.challenger_choice == result else challenge.opponent
        
        # Update challenge and process rewards
        return self.process_challenge_result(challenge, winner)
    
    def execute_dice_roll(self, challenge):
        dice_roll = challenge.dice_roll
        
        # Roll the dice for both players
        challenger_roll = random.randint(1, 6)
        opponent_roll = random.randint(1, 6)
        
        dice_roll.challenger_roll = challenger_roll
        dice_roll.opponent_roll = opponent_roll
        dice_roll.save()
        
        # Determine the winner (higher roll wins)
        if challenger_roll > opponent_roll:
            winner = challenge.challenger
        elif opponent_roll > challenger_roll:
            winner = challenge.opponent
        else:
            # It's a tie, reroll
            return self.execute_dice_roll(challenge)
        
        # Update challenge and process rewards
        return self.process_challenge_result(challenge, winner)
    
    def process_challenge_result(self, challenge, winner):
        with transaction.atomic():
            # Update challenge
            challenge.status = 'COMPLETED'
            challenge.winner = winner
            challenge.save()
            
            # Calculate total winnings (both wagers)
            total_winnings = challenge.token_wager * 2
            
            # Award tokens to winner
            Transaction.objects.create(
                user=winner,
                challenge=challenge,
                amount=total_winnings,
                transaction_type='WINNINGS'
            )
            winner.token_balance += total_winnings
            
            # Update win/loss records and streaks
            loser = challenge.opponent if winner == challenge.challenger else challenge.challenger
            
            # Update winner stats
            winner.games_won += 1
            winner.current_streak += 1
            winner.best_streak = max(winner.best_streak, winner.current_streak)
            
            # Update loser stats
            loser.games_lost += 1
            loser.current_streak = 0
            
            # Update ELO ratings
            self.update_elo_ratings(winner, loser)
            
            # Save both users
            winner.save()
            loser.save()
        
        return ChallengeSerializer(challenge).data
    
    def update_elo_ratings(self, winner, loser):
        # Simple ELO rating update
        k_factor = 32  # How much ratings change (higher = more volatile)
        
        # Calculate expected win probabilities
        winner_expected = 1 / (1 + 10 ** ((loser.rating - winner.rating) / 400))
        loser_expected = 1 / (1 + 10 ** ((winner.rating - loser.rating) / 400))
        
        # Update ratings
        winner.rating += k_factor * (1 - winner_expected)
        loser.rating += k_factor * (0 - loser_expected)
    
    @action(detail=False, methods=['get'])
    def my_challenges(self, request):
        user = request.user
        
        # Get all challenges where the user is either challenger or opponent
        challenges = Challenge.objects.filter(
            models.Q(challenger=user) | models.Q(opponent=user)
        ).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            challenges = challenges.filter(status=status_filter)
        
        serializer = ChallengeSerializer(challenges, many=True)
        return Response(serializer.data)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')

@login_required
def leaderboard_view(request):
    # Get top users by rating
    top_users = User.objects.all().order_by('-rating')[:20]
    
    # Get users with highest win streaks
    streak_users = User.objects.all().order_by('-current_streak')[:10]
    
    # Get users with highest token balances
    rich_users = User.objects.all().order_by('-token_balance')[:10]
    
    context = {
        'top_users': top_users,
        'streak_users': streak_users,
        'rich_users': rich_users,
    }
    
    return render(request, 'challenges/leaderboard.html', context)