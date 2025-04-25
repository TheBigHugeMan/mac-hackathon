from django.contrib.auth.models import AbstractUser
from django.db import models
# Create your models here.
# users/models.py

class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    program = models.CharField(max_length=100, blank=True)
    major = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    token_balance = models.IntegerField(default=100)
    games_won = models.IntegerField(default=0)
    games_lost = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    rating = models.FloatField(default=1000)  # ELO-like rating
    
    def __str__(self):
        return self.username
    
    @property
    def win_rate(self):
        total_games = self.games_won + self.games_lost
        if total_games == 0:
            return 0
        return (self.games_won / total_games) * 100

class GamePreference(models.Model):
    GAME_CHOICES = [
        ('COIN_FLIP', 'Coin Flip'),
        ('DICE_ROLL', 'Dice Roll'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferences')
    game_type = models.CharField(max_length=20, choices=GAME_CHOICES)
    
    class Meta:
        unique_together = ('user', 'game_type')

class AvailableTime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='available_times')
    day_of_week = models.IntegerField(choices=[(i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])])
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        ordering = ['day_of_week', 'start_time']

class Match(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    class Meta:
        unique_together = ('user1', 'user2')