# challenges/models.py
from django.db import models
from django.utils import timezone
import random
from users.models import User, Match
from django.core.validators import MinValueValidator, MaxValueValidator



class Challenge(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled'),
    )
    
    GAME_CHOICES = (
        ('COIN_FLIP', 'Coin Flip'),
        ('DICE_ROLL', 'Dice Roll'),
    )
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='challenges')
    challenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_challenges')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_challenges')
    game_type = models.CharField(max_length=20, choices=GAME_CHOICES)
    wager = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_time = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_challenges')
    
    def __str__(self):
        return f"{self.challenger.username} vs {self.opponent.username} - {self.get_game_type_display()}"
    
    def accept(self):
        if self.status == 'PENDING':
            # Check if both users have enough tokens
            if self.challenger.token_balance >= self.wager and self.opponent.token_balance >= self.wager:
                # Reserve the tokens
                self.challenger.token_balance -= self.wager
                self.opponent.token_balance -= self.wager
                self.challenger.save()
                self.opponent.save()
                
                # Create transactions
                Transaction.objects.create(
                    user=self.challenger,
                    challenge=self,
                    amount=-self.wager,
                    transaction_type='WAGER'
                )
                Transaction.objects.create(
                    user=self.opponent,
                    challenge=self,
                    amount=-self.wager,
                    transaction_type='WAGER'
                )
                
                self.status = 'ACCEPTED'
                self.save()
                return True
            return False
        return False
    
    def reject(self):
        if self.status == 'PENDING':
            self.status = 'REJECTED'
            self.save()
            return True
        return False
    
    def complete(self, winner):
        if self.status == 'ACCEPTED':
            self.winner = winner
            self.status = 'COMPLETED'
            self.completed_at = timezone.now()
            self.save()
            
            # Award tokens to winner
            total_wager = self.wager * 2
            winner.token_balance += total_wager
            winner.save()
            
            # Create transaction
            Transaction.objects.create(
                user=winner,
                challenge=self,
                amount=total_wager,
                transaction_type='WINNINGS'
            )
            
            # Update stats
            winner.update_streak(True)
            loser = self.challenger if self.winner == self.opponent else self.opponent
            loser.update_streak(False)
            
            # Update ratings
            winner.update_rating(loser.rating, True)
            loser.update_rating(winner.rating, False)
            
            return True
        return False

class CoinFlipGame(models.Model):
    CHOICES = (
        ('HEADS', 'Heads'),
        ('TAILS', 'Tails'),
    )
    
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, related_name='coin_flip')
    challenger_choice = models.CharField(max_length=5, choices=CHOICES)
    result = models.CharField(max_length=5, choices=CHOICES, null=True, blank=True)
    
    def execute(self):
        if self.challenge.status == 'ACCEPTED':
            # Perform random coin flip
            self.result = random.choice(['HEADS', 'TAILS'])
            self.save()
            
            # Determine winner
            winner = self.challenge.challenger if self.challenger_choice == self.result else self.challenge.opponent
            self.challenge.complete(winner)
            return True
        return False

class DiceRollGame(models.Model):
    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE, related_name='dice_roll')
    challenger_guess = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        null=True,
        blank=True
    )
    opponent_guess = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        null=True,
        blank=True
    )
    challenger_roll = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        null=True,
        blank=True
    )
    opponent_roll = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        null=True,
        blank=True
    )
    
    def execute(self):
        if self.challenge.status == 'ACCEPTED':
            # Perform random dice rolls
            self.challenger_roll = random.randint(1, 6)
            self.opponent_roll = random.randint(1, 6)
            self.save()
            
            # Determine winner based on guesses or higher roll
            if self.challenger_guess is not None and self.opponent_guess is not None:
                # If both made guesses, the closest guess wins
                challenger_diff = abs(self.challenger_roll - self.challenger_guess)
                opponent_diff = abs(self.opponent_roll - self.opponent_guess)
                
                if challenger_diff < opponent_diff:
                    winner = self.challenge.challenger
                elif opponent_diff < challenger_diff:
                    winner = self.challenge.opponent
                else:
                    # In case of a tie, higher roll wins
                    winner = self.challenge.challenger if self.challenger_roll > self.opponent_roll else self.challenge.opponent
            else:
                # If no guesses, higher roll wins
                winner = self.challenge.challenger if self.challenger_roll > self.opponent_roll else self.challenge.opponent
                
                # Handle ties by re-rolling (recursive call)
                if self.challenger_roll == self.opponent_roll:
                    return self.execute()
            
            self.challenge.complete(winner)
            return True
        return False

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('WAGER', 'Wager'),
        ('WINNINGS', 'Winnings'),
        ('REFUND', 'Refund'),
        ('BONUS', 'Bonus'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    challenge = models.ForeignKey(Challenge, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.IntegerField()  # Can be negative for wagers
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}: {self.amount} ({self.transaction_type})"