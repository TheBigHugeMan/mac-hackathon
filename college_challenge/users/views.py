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
from chat.models import ChatRoom
from django.shortcuts import render

def home_view(request):
    return render(request, 'users/home.html')

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
