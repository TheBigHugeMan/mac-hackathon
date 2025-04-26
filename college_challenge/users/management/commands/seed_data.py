from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Match, GamePreference
from chat.models import ChatRoom, Message
import random
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        # Create test users
        test_users = []
        programs = ['Computer Science', 'Business', 'Engineering', 'Medicine', 'Arts']
        majors = ['Software Engineering', 'Finance', 'Mechanical Engineering', 'General Medicine', 'Visual Arts']
        
        for i in range(1, 11):
            username = f'testuser{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password='testpassword',
                    program=random.choice(programs),
                    major=random.choice(majors),
                    token_balance=100 + random.randint(0, 100),
                    win_count=random.randint(0, 10),
                    loss_count=random.randint(0, 5),
                    current_streak=random.randint(0, 3),
                    best_streak=random.randint(3, 5),
                    rating=1000 + random.randint(-100, 100)
                )
                test_users.append(user)
                self.stdout.write(f'Created user: {username}')
                
                # Add game preferences
                if random.random() > 0.5:
                    GamePreference.objects.create(
                        user=user,
                        game_type='COIN_FLIP'
                    )
                if random.random() > 0.5:
                    GamePreference.objects.create(
                        user=user,
                        game_type='DICE_ROLL'
                    )
            else:
                test_users.append(User.objects.get(username=username))
                self.stdout.write(f'User {username} already exists')
        
        # Create matches between users
        for i in range(5):  # Create 5 matches
            user1 = random.choice(test_users)
            user2 = random.choice([u for u in test_users if u != user1])
            
            # Check if match already exists
            if not Match.objects.filter(
                (models.Q(user1=user1) & models.Q(user2=user2)) | 
                (models.Q(user1=user2) & models.Q(user2=user1))
            ).exists():
                match = Match.objects.create(
                    user1=user1,
                    user2=user2,
                    status='ACCEPTED'
                )
                self.stdout.write(f'Created match between {user1.username} and {user2.username}')
                
                # Create chat room for the match
                chat_room = ChatRoom.objects.create(match=match)
                self.stdout.write(f'Created chat room for match {match.id}')
                
                # Add some messages
                for _ in range(random.randint(3, 8)):
                    sender = random.choice([user1, user2])
                    content = random.choice([
                        'Hey there!',
                        'Want to play a game?',
                        'How are you doing?',
                        'I challenge you to a coin flip!',
                        'Ready for a dice roll?',
                        'Let\'s bet 20 tokens!',
                        'Good game!',
                        'Better luck next time.',
                        'I\'ll win next time for sure!'
                    ])
                    
                    Message.objects.create(
                        chat_room=chat_room,
                        sender=sender,
                        content=content,
                        timestamp=timezone.now() - timezone.timedelta(minutes=random.randint(1, 1000))
                    )
                self.stdout.write(f'Added messages to chat room {chat_room.id}')
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))