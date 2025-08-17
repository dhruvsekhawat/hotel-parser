#!/bin/bash

# Hotel Quote Parser - Startup Script
# This script starts both the Next.js frontend and FastAPI microservice

echo "Starting Hotel Quote Parser..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is required but not installed."
    exit 1
fi

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    echo "Loading environment variables from .env.local..."
    export $(grep -v '^#' .env.local | xargs)
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable is required."
    echo "   The microservice uses OpenAI API for intelligent extraction."
    echo "   Please add it to .env.local: OPENAI_API_KEY=your_key_here"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    exit 1
fi

echo "SUCCESS: OpenAI API key found"

# Function to cleanup background processes
cleanup() {
    echo "Shutting down services..."
    kill $FRONTEND_PID $MICROSERVICE_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start microservice in background
echo "Starting FastAPI microservice..."
cd microservice
python3 main.py &
MICROSERVICE_PID=$!
cd ..

# Wait a moment for microservice to start
sleep 3

# Check if microservice is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "ERROR: Microservice failed to start. Check the logs above."
    kill $MICROSERVICE_PID 2>/dev/null
    exit 1
fi

echo "SUCCESS: Microservice is running on http://localhost:8000"

# Start frontend in background
echo "Starting Next.js frontend..."
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Check if frontend is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "ERROR: Frontend failed to start. Check the logs above."
    kill $FRONTEND_PID $MICROSERVICE_PID 2>/dev/null
    exit 1
fi

echo "SUCCESS: Frontend is running on http://localhost:3000"
echo ""
echo "Hotel Quote Parser is ready!"
echo "   Frontend: http://localhost:3000"
echo "   Microservice: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
