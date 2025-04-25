# challenges/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Challenge, CoinFlip, DiceRoll
from .serializers import ChallengeSerializer, CoinFlipSerializer, DiceRollSerializer
from users.models import Match, Transaction


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter challenges to only show relevant ones for the current user"""
        user = self.request.user
        return Challenge.objects.filter(participants=user)
    
    @action(detail=False, methods=['post'])
    def create_challenge(self, request):
        """Create a new challenge after matching"""
        match_id = request.data.get('match_id')
        game_type = request.data.get('game_type')
        tokens_bet = request.data.get('tokens_bet', 10)  # Default bet
        
        match = get_object_or_404(Match, id=match_id)
        
        # Verify the current user is part of this match
        if request.user not in [match.user1, match.user2]:
            return Response({"error": "Not authorized to create challenge for this match"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Check if users have enough tokens
        challenger = request.user
        opponent = match.user2 if match.user1 == challenger else match.user1
        
        if challenger.profile.tokens < tokens_bet or opponent.profile.tokens < tokens_bet:
            return Response({"error": "Insufficient tokens for this challenge"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Create challenge
        with transaction.atomic():
            challenge = Challenge.objects.create(
                created_by=challenger,
                tokens_bet=tokens_bet,
                match=match,
                status='pending'
            )
            challenge.participants.add(challenger, opponent)
            
            # Create specific game based on type
            if game_type == 'coinflip':
                game = CoinFlip.objects.create(
                    challenge=challenge,
                    user_heads=challenger  # Default assignment
                )
            elif game_type == 'diceroll':
                game = DiceRoll.objects.create(
                    challenge=challenge,
                    is_higher_wins=True  # Default game mode
                )
            else:
                challenge.delete()
                return Response({"error": "Invalid game type"}, 
                               status=status.HTTP_400_BAD_REQUEST)
                
        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept_challenge(self, request, pk=None):
        """Accept a pending challenge"""
        challenge = self.get_object()
        user = request.user
        
        # Verify user is part of this challenge
        if user not in challenge.participants.all():
            return Response({"error": "Not authorized to accept this challenge"}, 
                           status=status.HTTP_403_FORBIDDEN)
                           
        if challenge.created_by == user:
            return Response({"error": "Cannot accept your own challenge"}, 
                           status=status.HTTP_400_BAD_REQUEST)
                           
        if challenge.status != 'pending':
            return Response({"error": f"Challenge is already {challenge.status}"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Check if users still have enough tokens
        for participant in challenge.participants.all():
            if participant.profile.tokens < challenge.tokens_bet:
                return Response({"error": f"{participant.username} has insufficient tokens"}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        # Update challenge status
        challenge.status = 'accepted'
        challenge.save()
        
        # Reserve tokens
        for participant in challenge.participants.all():
            participant.profile.tokens -= challenge.tokens_bet
            participant.profile.save()
        
        return Response(ChallengeSerializer(challenge).data)
    
    @action(detail=True, methods=['post'])
    def execute_challenge(self, request, pk=None):
        """Execute the challenge to determine winner"""
        challenge = self.get_object()
        
        if challenge.status != 'accepted':
            return Response({"error": "Challenge must be accepted before execution"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Execute the game and determine winner
        if hasattr(challenge, 'coinflip'):
            game = challenge.coinflip
            winner = game.execute_game()
        elif hasattr(challenge, 'diceroll'):
            game = challenge.diceroll
            winner = game.execute_game()
        else:
            return Response({"error": "Unknown game type"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        if not winner:
            return Response({"error": "Failed to determine winner"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update challenge status
        challenge.status = 'completed'
        challenge.winner = winner
        challenge.save()
        
        # Transfer tokens to winner
        loser = [p for p in challenge.participants.all() if p != winner][0]
        tokens_won = challenge.tokens_bet * 2  # Winner gets both bets
        
        winner.profile.tokens += tokens_won
        winner.profile.win_streak += 1
        winner.profile.total_wins += 1
        winner.profile.save()
        
        loser.profile.win_streak = 0  # Reset streak
        loser.profile.total_losses += 1
        loser.profile.save()
        
        # Create transaction record
        Transaction.objects.create(
            from_user=loser,
            to_user=winner,
            amount=challenge.tokens_bet,
            challenge=challenge,
            transaction_type='challenge_reward'
        )
        
        return Response({
            "challenge": ChallengeSerializer(challenge).data,
            "winner": winner.username,
            "tokens_won": tokens_won
        })