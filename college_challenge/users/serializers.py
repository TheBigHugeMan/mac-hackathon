# users/serializers.py

from rest_framework import serializers
from .models import User, Match, GamePreference, AvailableTime

class GamePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GamePreference
        fields = ['game_type']

class AvailableTimeSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AvailableTime
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time']
    
    def get_day_name(self, obj):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[obj.day_of_week]

class UserSerializer(serializers.ModelSerializer):
    preferences = GamePreferenceSerializer(many=True, read_only=True)
    available_times = AvailableTimeSerializer(many=True, read_only=True)
    win_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture', 'program', 'major', 
                  'bio', 'token_balance', 'games_won', 'games_lost', 'current_streak', 
                  'best_streak', 'rating', 'preferences', 'available_times', 'win_rate']
        read_only_fields = ['token_balance', 'games_won', 'games_lost', 'current_streak', 
                           'best_streak', 'rating', 'win_rate']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture', 'program', 'major', 
                  'bio', 'current_streak', 'best_streak', 'token_balance', 'rating']

class MatchSerializer(serializers.ModelSerializer):
    user1 = UserProfileSerializer(read_only=True)
    user2 = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Match
        fields = ['id', 'user1', 'user2', 'created_at', 'status']