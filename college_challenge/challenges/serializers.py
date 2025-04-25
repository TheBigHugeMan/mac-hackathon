# challenges/serializers.py

from rest_framework import serializers
from .models import Challenge, CoinFlipGame, DiceRollGame, Transaction
from users.serializers import UserProfileSerializer

class CoinFlipGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinFlipGame
        fields = ['challenger_choice', 'result']

class DiceRollGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiceRollGame
        fields = ['challenger_guess', 'opponent_guess', 'challenger_roll', 'opponent_roll']

class ChallengeSerializer(serializers.ModelSerializer):
    challenger = UserProfileSerializer(read_only=True)
    opponent = UserProfileSerializer(read_only=True)
    winner = UserProfileSerializer(read_only=True)
    coin_flip = CoinFlipGameSerializer(read_only=True)
    dice_roll = DiceRollGameSerializer(read_only=True)
    
    class Meta:
        model = Challenge
        fields = ['id', 'challenger', 'opponent', 'game_type', 'token_wager', 
                  'status', 'scheduled_time', 'created_at', 'winner', 
                  'coin_flip', 'dice_roll']

class CreateChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['opponent', 'game_type', 'token_wager', 'scheduled_time']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'challenge', 'amount', 'transaction_type', 'created_at']