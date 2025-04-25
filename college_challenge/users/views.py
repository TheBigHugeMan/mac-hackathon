# Create your views here.
# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Match, GamePreference, AvailableTime
from .serializers import UserSerializer, UserProfileSerializer, MatchSerializer
from .forms import RegistrationForm, UserProfileForm
import random

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserProfileSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def potential_matches(self, request):
        user = request.user
        
        # Get users who have not matched with the current user
        already_matched = Match.objects.filter(user1=user).values_list('user2', flat=True)
        already_matched_reverse = Match.objects.filter(user2=user).values_list('user1', flat=True)
        
        potential_matches = User.objects.exclude(id=user.id) \
                                      .exclude(id__in=already_matched) \
                                      .exclude(id__in=already_matched_reverse)
        
        # Filter by game preferences if provided
        game_type = request.query_params.get('game_type')
        if game_type:
            potential_matches = potential_matches.filter(preferences__game_type=game_type)
        
        # Filter by rating range if desired
        rating_range = 200  # Match with users within +/- 200 rating points
        potential_matches = potential_matches.filter(
            rating__gte=user.rating - rating_range,
            rating__lte=user.rating + rating_range
        )
        
        serializer = UserProfileSerializer(potential_matches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def swipe_right(self, request, pk=None):
        target_user = self.get_object()
        user = request.user
        
        # Check if there's already a match (the other user swiped right on this user)
        existing_match = Match.objects.filter(user1=target_user, user2=user, status='PENDING').first()
        
        if existing_match:
            # It's a match!
            existing_match.status = 'ACCEPTED'
            existing_match.save()
            
            # Create a chat room for the matched users
            from chat.models import ChatRoom
            ChatRoom.objects.create(
                match=existing_match,
                room_type='DIRECT'
            )
            
            return Response({'status': 'matched', 'match_id': existing_match.id}, status=status.HTTP_200_OK)
        else:
            # Create a new pending match
            match = Match.objects.create(
                user1=user,
                user2=target_user,
                status='PENDING'
            )
            
            return Response({'status': 'pending', 'match_id': match.id}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def swipe_left(self, request, pk=None):
        target_user = self.get_object()
        user = request.user
        
        # Check if there's a pending match from the other user
        existing_match = Match.objects.filter(user1=target_user, user2=user, status='PENDING').first()
        
        if existing_match:
            # Reject the match
            existing_match.status = 'REJECTED'
            existing_match.save()
        
        # No need to create anything for a left swipe
        return Response({'status': 'rejected'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def matches(self, request):
        user = request.user
        
        # Get all accepted matches where the user is either user1 or user2
        matches = Match.objects.filter(
            (models.Q(user1=user) | models.Q(user2=user)) & 
            models.Q(status='ACCEPTED')
        )
        
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'users/profile.html', context)

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set initial token balance
            user.token_balance = 100
            user.save()
            
            # Log the user in
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})