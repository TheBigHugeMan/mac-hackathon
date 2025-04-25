# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    program = models.CharField(max_length=100, blank=True)
    major = models.CharField(max_length=100, blank=True)
    token_balance = models.IntegerField(default=100, validators=[MinValueValidator(0)])
    win_count = models.IntegerField(default=0)
    loss_count = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    rating = models.FloatField(default=1000.0)  # ELO-like rating
    
    def __str__(self):
        return self.username
    
    def update_streak(self, win):
        if win:
            self.win_count += 1
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
        else:
            self.loss_count += 1
            self.current_streak = 0
        self.save()
    
    def update_rating(self, opponent_rating, win, k_factor=32):
        # ELO rating system
        expected_result = 1 / (1 + 10 ** ((opponent_rating - self.rating) / 400))
        actual_result = 1 if win else 0
        self.rating += k_factor * (actual_result - expected_result)
        self.save()

class GamePreference(models.Model):
    GAME_TYPES = (
        ('COIN_FLIP', 'Coin Flip'),
        ('DICE_ROLL', 'Dice Roll'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_preferences')
    game_type = models.CharField(max_length=20, choices=GAME_TYPES)
    
    class Meta:
        unique_together = ('user', 'game_type')

class AvailableTime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='available_times')
    day_of_week = models.IntegerField(choices=[(i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])])
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        unique_together = ('user', 'day_of_week', 'start_time', 'end_time')

class Match(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )
    
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_matches')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_matches')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    class Meta:
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"{self.user1.username} ⟷ {self.user2.username} ({self.status})"