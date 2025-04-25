# challenges/serializers.py
from rest_framework import serializers
from .models import Challenge, CoinFlipGame, DiceRollGame, Transaction
from users.serializers import UserCardSerializer

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'timestamp']

class CoinFlipGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinFlipGame
        fields = ['challenger_choice', 'result']

class DiceRollGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiceRollGame
        fields = ['challenger_guess', 'opponent_guess', 'challenger_roll', 'opponent_roll']

class ChallengeSerializer(serializers.ModelSerializer):
    challenger = UserCardSerializer(read_only=True)
    opponent = UserCardSerializer(read_only=True)
    winner = UserCardSerializer(read_only=True)
    coin_flip = CoinFlipGameSerializer(read_only=True)
    dice_roll = DiceRollGameSerializer(read_only=True)
    
    class Meta:
        model = Challenge
        fields = [
            'id', 'challenger', 'opponent', 'game_type',
            'wager', 'status', 'created_at', 'scheduled_time',
            'completed_at', 'winner', 'coin_flip', 'dice_roll'
        ]
        read_only_fields = ['status', 'completed_at', 'winner']

class CreateChallengeSerializer(serializers.ModelSerializer):
    game_details = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = Challenge
        fields = ['match', 'game_type', 'wager', 'scheduled_time', 'game_details']
    
    def create(self, validated_data):
        user = self.context['request'].user
        match = validated_data.get('match')
        game_details = validated_data.pop('game_details', {})
        
        # Set challenger and opponent based on match
        if match.user1 == user:
            challenger = match.user1
            opponent = match.user2
        else:
            challenger = match.user2
            opponent = match.user1
        
        # Create challenge
        challenge = Challenge.objects.create(
            match=match,
            challenger=challenger,
            opponent=opponent,
            game_type=validated_data.get('game_type'),
            wager=validated_data.get('wager'),
            scheduled_time=validated_data.get('scheduled_time')
        )
        
        # Create game-specific details
        if challenge.game_type == 'COIN_FLIP':
            CoinFlipGame.objects.create(
                challenge=challenge,
                challenger_choice=game_details.get('challenger_choice', 'HEADS')
            )
        elif challenge.game_type == 'DICE_ROLL':
            DiceRollGame.objects.create(
                challenge=challenge,
                challenger_guess=game_details.get('challenger_guess'),
                opponent_guess=game_details.get('opponent_guess')
            )
        
        return challenge

class AcceptChallengeSerializer(serializers.ModelSerializer):
    game_details = serializers.JSONField(write_only=True, required=False)
    
    class Meta:
        model = Challenge
        fields = ['game_details']
    
    def update(self, instance, validated_data):
        game_details = validated_data.get('game_details', {})
        
        # Update game-specific details if needed
        if instance.game_type == 'DICE_ROLL':
            dice_game = instance.dice_roll
            dice_game.opponent_guess = game_details.get('opponent_guess', dice_game.opponent_guess)
            dice_game.save()
        
        # Accept the challenge
        instance.accept()
        return instance