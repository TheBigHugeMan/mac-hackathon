@echo off
echo Setting up College Challenge for Windows...

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run database migrations
echo Setting up database...
python manage.py makemigrations
python manage.py migrate

REM Ask if user wants to create a superuser
set /p create_superuser="Do you want to create a superuser? (y/n): "
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

REM Check if Redis is installed (basic check, might not be accurate)
where redis-server >nul 2>&1 || where redis-cli >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Redis does not appear to be installed. It is required for chat functionality.
    echo Please download and install Redis from: https://github.com/tporadowski/redis/releases
)

echo.
echo Setup complete! Run the server with: python manage.py runserver
echo Then access the application at: http://localhost:8000