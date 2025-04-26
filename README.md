# College Challenge

College Challenge is a social gaming platform that allows students to connect, compete, and challenge each other to simple games like Coin Flip and Dice Roll. The app features a Tinder-style matching system, in-app chat, and a virtual token economy.

## Features

- **User Registration & Profiles**: Students can create accounts, set up profiles with program/major info and profile pictures
- **Tinder-Style Matching**: A swipe interface to match with other students on campus
- **Challenges**: Create and accept challenges for games like Coin Flip and Dice Roll
- **Virtual Token Economy**: Wager tokens on challenges and earn more by winning
- **Real-Time Chat**: In-app messaging with matched users
- **Leaderboard**: Track your performance, win streaks and ranking among other students

## Tech Stack

- **Backend**: Django, Django REST Framework, Django Channels
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (for development)
- **Real-time Communication**: WebSockets (Django Channels)
- **Asynchronous Tasks**: Redis (as channel layer backend)

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Redis server (for WebSocket support)
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/college_challenge.git
cd college_challenge
```

2. Create and activate a virtual environment
```bash
python -m venv venv
# For Windows
venv\Scripts\activate
# For macOS/Linux
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Make migrations and migrate the database
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser (for admin access)
```bash
python manage.py createsuperuser
```

6. Start the Redis server (required for chat functionality)
```bash
# On macOS (using Homebrew)
brew install redis
brew services start redis

# On Ubuntu/Debian
sudo apt-get install redis-server
sudo service redis-server start

# On Windows, download and install from https://redis.io/download
# Then start the Redis server
```

7. Run the Django development server
```bash
python manage.py runserver
```

8. Access the application at http://localhost:8000

### Project Structure

```
college_challenge/
├── challenges/               # Challenge app (games, betting)
├── chat/                     # Chat app (messaging, chat rooms)
├── college_challenge/        # Project settings and main configuration
├── static/                   # Static files (CSS, JS, images)
├── templates/                # Base HTML templates
└── users/                    # User app (auth, profiles, matching)
```

## Usage

### Registration and Profile Setup

1. Visit the homepage and click "Register"
2. Create an account with your username and profile information
3. You'll receive 100 virtual tokens upon registration

### Finding Matches

1. Go to "Find Matches" in the navigation bar
2. Swipe right on students you'd like to challenge
3. When both users swipe right on each other, it's a match!

### Creating Challenges

1. Once matched, you can access your chat with the other student
2. In the chat interface, create a challenge by selecting:
   - Game type (Coin Flip or Dice Roll)
   - Token wager amount
   - Game-specific settings

### Playing Challenges

1. The other student must accept your challenge
2. When both are ready, the challenge can be executed
3. Results are determined randomly and fairly
4. Tokens are automatically transferred to the winner

### Chatting

- Use the chat interface to communicate with your matches
- Discuss challenge details or just socialize

## Development

### Running Tests

```bash
python manage.py test
```

### Database Diagram

The database consists of several key models:
- User: Extended Django User model with game-related stats
- Match: Connections between two users
- ChatRoom: For message exchange between matches
- Challenge: Game instances between users
- Game-specific models: CoinFlipGame, DiceRollGame
- Transaction: Record of token exchanges

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Requirements.txt

Create a `requirements.txt` file with the following dependencies:

```
Django>=5.0,<5.3
channels>=4.0.0
channels-redis>=4.1.0
django-rest-framework>=0.1.0
djangorestframework>=3.14.0
Pillow>=10.0.0
django-widget-tweaks>=1.5.0
redis>=5.0.0
```
