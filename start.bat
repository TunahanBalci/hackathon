@echo off
echo Starting the Diet Analysis System...

REM Activate virtual environment
call .venv\Scripts\activate

REM Start backend server
start cmd /k "echo Starting Backend Server... && python app.py"

REM Wait for backend to start
timeout /t 5

REM Start frontend server
start cmd /k "cd client && echo Starting Frontend Server... && npm start"

echo System is starting up...
echo Backend will be available at: http://localhost:5000
echo Frontend will be available at: http://localhost:3000 