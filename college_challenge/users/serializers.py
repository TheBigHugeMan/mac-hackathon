# users/serializers.py
from rest_framework import serializers
from .models import User, GamePreference, AvailableTime, Match

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

class UserProfileSerializer(serializers.ModelSerializer):
    game_preferences = GamePreferenceSerializer(many=True, read_only=True)
    available_times = AvailableTimeSerializer(many=True, read_only=True)
    win_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'profile_picture', 'program', 'major',
            'token_balance', 'win_count', 'loss_count', 
            'current_streak', 'best_streak', 'rating',
            'game_preferences', 'available_times', 'win_rate'
        ]
    
    def get_win_rate(self, obj):
        total_games = obj.win_count + obj.loss_count
        if total_games == 0:
            return 0
        return round((obj.win_count / total_games) * 100, 1)

class UserCardSerializer(serializers.ModelSerializer):
    """Simplified user serializer for the swiping interface"""
    win_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'profile_picture', 'program', 'major',
            'current_streak', 'best_streak', 'token_balance', 'win_rate'
        ]
    
    def get_win_rate(self, obj):
        total_games = obj.win_count + obj.loss_count
        if total_games == 0:
            return 0
        return round((obj.win_count / total_games) * 100, 1)

class MatchSerializer(serializers.ModelSerializer):
    user1 = UserCardSerializer(read_only=True)
    user2 = UserCardSerializer(read_only=True)
    
    class Meta:
        model = Match
        fields = ['id', 'user1', 'user2', 'created_at', 'status']

class CreateMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['user2']
    
    def create(self, validated_data):
        user1 = self.context['request'].user
        user2 = validated_data.get('user2')
        
        # Check if match already exists
        existing_match = Match.objects.filter(
            (models.Q(user1=user1) & models.Q(user2=user2)) | 
            (models.Q(user1=user2) & models.Q(user2=user1))
        ).first()
        
        if existing_match:
            return existing_match
        
        return Match.objects.create(user1=user1, user2=user2)