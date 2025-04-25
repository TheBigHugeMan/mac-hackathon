from django.db import models
from users.models import User, Match

# Create your models here.

class Challenge(models.Model):
    GAME_CHOICES = [
        ('COIN_FLIP', 'Coin Flip'),
        ('DICE_ROLL', 'Dice Roll'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='challenges')
    challenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges_created')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges_received')
    game_type = models.CharField(max_length=20, choices=GAME_CHOICES)
    token_wager = models.IntegerField(default=10)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    scheduled_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='challenges_won')
    
    def __str__(self):
        return f"{self.challenger.username} vs {self.opponent.username} - {self.game_type}"

class CoinFlipGame(models.Model):
    SIDE_CHOICES = [
        ('HEADS', 'Heads'),
        ('TAILS', 'Tails'),
    ]
    
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, related_name='coin_flip')
    challenger_choice = models.CharField(max_length=5, choices=SIDE_CHOICES)
    result = models.CharField(max_length=5, choices=SIDE_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return f"Coin Flip: {self.challenge}"

class DiceRollGame(models.Model):
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, related_name='dice_roll')
    challenger_guess = models.IntegerField(null=True, blank=True)
    opponent_guess = models.IntegerField(null=True, blank=True)
    challenger_roll = models.IntegerField(null=True, blank=True)
    opponent_roll = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"Dice Roll: {self.challenge}"

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('WAGER', 'Wager'),
        ('WINNINGS', 'Winnings'),
        ('BONUS', 'Bonus'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"