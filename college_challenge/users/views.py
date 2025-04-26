# users/views.py
from django.db.models import Q
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User, Match
from .serializers import (
    UserProfileSerializer, UserCardSerializer, 
    MatchSerializer, CreateMatchSerializer
)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from .forms import UserRegisterForm, UserProfileForm
from chat.models import ChatRoom

def home_view(request):
    """Home page view"""
    if request.user.is_authenticated:
        # Get user stats
        user = request.user
        total_games = user.win_count + user.loss_count
        win_rate = 0 if total_games == 0 else round((user.win_count / total_games) * 100, 1)
        
        # Get recent matches
        recent_matches = Match.objects.filter(
            (Q(user1=user) | Q(user2=user)) & 
            Q(status='ACCEPTED')
        ).order_by('-created_at')[:5]
        
        # Get recent challenges
        from challenges.models import Challenge
        recent_challenges = Challenge.objects.filter(
            Q(challenger=user) | Q(opponent=user)
        ).order_by('-created_at')[:5]
        
        # Get leaderboard data
        top_users = User.objects.order_by('-rating')[:10]
        
        context = {
            'total_games': total_games,
            'win_rate': win_rate,
            'recent_matches': recent_matches,
            'recent_challenges': recent_challenges,
            'top_users': top_users
        }
        return render(request, 'users/dashboard.html', context)
    
    # If not authenticated, show the landing page
    return render(request, 'home.html')

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user stats
    user = request.user
    total_games = user.win_count + user.loss_count
    win_rate = 0 if total_games == 0 else round((user.win_count / total_games) * 100, 1)
    
    # Get transaction history
    from challenges.models import Transaction
    transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:10]
    
    context = {
        'form': form,
        'total_games': total_games,
        'win_rate': win_rate,
        'transactions': transactions
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def match_view(request):
    """Match finding (Tinder-style swiping) view"""
    user = request.user
    
    # Get users that haven't been matched yet
    existing_matches = Match.objects.filter(
        Q(user1=user) | Q(user2=user)
    )
    excluded_users = set()
    for match in existing_matches:
        if match.user1 == user:
            excluded_users.add(match.user2.id)
        else:
            excluded_users.add(match.user1.id)
    
    # Get potential matches based on rating similarity
    potential_matches = User.objects.exclude(
        id__in=list(excluded_users) + [user.id]
    ).order_by('?')[:5]  # Random 5 users
    
    context = {
        'potential_matches': potential_matches
    }
    
    return render(request, 'users/match.html', context)

class UserViewSet(mixins.RetrieveModelMixin, 
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'me':
            return UserProfileSerializer
        return UserCardSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def potential_matches(self, request):
        """Get a list of potential matches for swiping"""
        user = request.user
        
        # Exclude users that have already been matched with
        existing_matches = Match.objects.filter(
            Q(user1=user) | Q(user2=user)
        )
        excluded_users = set()
        for match in existing_matches:
            if match.user1 == user:
                excluded_users.add(match.user2.id)
            else:
                excluded_users.add(match.user1.id)
        
        # Get potential matches based on rating similarity
        potential_matches = User.objects.exclude(
            id__in=list(excluded_users) + [user.id]
        ).order_by('?')[:10]  # Random 10 users for now
        
        serializer = UserCardSerializer(potential_matches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def swipe_right(self, request, pk=None):
        """Swipe right on a user to match with them"""
        user = request.user
        target_user = self.get_object()
        
        # Check if the other user has already swiped right on this user
        existing_match = Match.objects.filter(
            user1=target_user,
            user2=user,
            status='PENDING'
        ).first()
        
        if existing_match:
            # It's a match!
            existing_match.status = 'ACCEPTED'
            existing_match.save()
            
            # Create chat room
            ChatRoom.objects.create(match=existing_match)
            
            serializer = MatchSerializer(existing_match)
            return Response({
                'match': serializer.data,
                'is_mutual': True
            }, status=status.HTTP_201_CREATED)
        else:
            # Create new pending match
            match = Match.objects.create(
                user1=user,
                user2=target_user,
                status='PENDING'
            )
            serializer = MatchSerializer(match)
            return Response({
                'match': serializer.data,
                'is_mutual': False
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def swipe_left(self, request, pk=None):
        """Swipe left on a user to reject them"""
        user = request.user
        target_user = self.get_object()
        
        # Check if there's a pending match and reject it
        existing_match = Match.objects.filter(
            user1=target_user,
            user2=user,
            status='PENDING'
        ).first()
        
        if existing_match:
            existing_match.status = 'REJECTED'
            existing_match.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def matches(self, request):
        """Get all matches for the current user"""
        user = request.user
        matches = Match.objects.filter(
            (Q(user1=user) | Q(user2=user)) & Q(status='ACCEPTED')
        )
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)