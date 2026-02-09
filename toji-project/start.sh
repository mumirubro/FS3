#!/bin/bash

# TOJI - Advanced Checker Platform
# Startup Script

echo "🚀 Starting TOJI Platform..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to start backend
start_backend() {
    echo -e "${BLUE}Starting Backend API...${NC}"
    cd backend
    python main.py &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}Backend started on http://localhost:8000${NC}"
}

# Function to start bot
start_bot() {
    echo -e "${BLUE}Starting Telegram Bot...${NC}"
    cd bot
    python toji_bot.py &
    BOT_PID=$!
    cd ..
    echo -e "${GREEN}Bot started${NC}"
}

# Function to start webapp
start_webapp() {
    echo -e "${BLUE}Starting Web Application...${NC}"
    cd webapp
    npm run dev &
    WEBAPP_PID=$!
    cd ..
    echo -e "${GREEN}WebApp started on http://localhost:5173${NC}"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.deps_installed" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    touch venv/.deps_installed
fi

# Start all services
echo ""
echo "========================================"
echo "  TOJI Platform is starting..."
echo "========================================"
echo ""

start_backend
sleep 2

start_bot
sleep 2

start_webapp

echo ""
echo "========================================"
echo -e "${GREEN}All services started!${NC}"
echo "========================================"
echo ""
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "WebApp:   ${BLUE}http://localhost:5173${NC}"
echo -e "Bot:      ${BLUE}@TOJIchk_bot${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
trap "echo ''; echo 'Stopping all services...'; kill $BACKEND_PID $BOT_PID $WEBAPP_PID 2>/dev/null; exit" INT
wait
