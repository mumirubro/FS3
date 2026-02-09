# TOJI - Advanced Checker Platform

A comprehensive web-based checker platform with Telegram bot integration for session management.

## Features

- **Telegram Bot Integration** (@TOJIchk_bot)
  - User registration
  - Session management (30-minute sessions)
  - Real-time hit notifications

- **Web Application**
  - CC Checkers (SK Based, PayPal, Stripe Auth, Shopify)
  - AutoHitters (Checkout CVV, Mass Checker)
  - CC Killers (Visa Killers)
  - Tools (SK Key Checker, Steam, Crunchyroll, Hotmail Checkers)
  - Settings (Proxy, Deposit, Premium, Gates, Redeem)
  - Profile (Stats, Leaderboard, Online Users)

- **Session Management**
  - 30-minute session expiry
  - Real-time countdown timer
  - Auto-logout on expiry

## Project Structure

```
toji-project/
├── bot/
│   └── toji_bot.py          # Telegram Bot
├── backend/
│   └── main.py              # FastAPI Backend
├── webapp/                  # React Frontend (in /app)
├── checkers/                # Python checker scripts
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend API

```bash
cd backend
python main.py
```

Backend will start on `http://localhost:8000`

### 3. Start the Telegram Bot

```bash
cd bot
python toji_bot.py
```

### 4. Start the Web Application

```bash
cd webapp
npm install
npm run dev
```

Webapp will start on `http://localhost:5173`

## Usage Flow

1. **User finds @TOJIchk_bot on Telegram**
2. **Sends `/start`**
3. **Clicks "REGISTER NOW"** - User is registered
4. **Sends `/start` again**
5. **Clicks "CREATE SESSION"** - Session token generated (30-min expiry)
6. **Clicks "OPEN WEB APP"** - WebApp opens with `?session=xxx`
7. **Session validated** → Shows TOJI Dashboard
8. **30-min countdown starts** in sidebar

## Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Bot Token
BOT_TOKEN=8543073349:AAE4g6AcLSgBTEz5b3sXaBJlDIhZnQopVE0

# Backend URL
API_URL=http://localhost:8000

# WebApp URL
WEBAPP_URL=http://localhost:5173
```

## API Endpoints

- `GET /api/session/validate` - Validate session token
- `GET /api/user/profile` - Get user profile
- `POST /api/checker/stripe` - Stripe CC Checker
- `POST /api/checker/paypal` - PayPal CC Checker
- `POST /api/checker/sk` - SK Key Checker
- `POST /api/checker/accounts` - Account Checker
- `GET /api/leaderboard` - Get top carders
- `GET /api/online-users` - Get online users

## Bot Commands

- `/start` - Start bot / View main menu
- `/help` - Show help message
- `/status` - Check session status
- `/stats` - View statistics

## Security Notes

- Sessions expire after 30 minutes of inactivity
- Direct access without session shows restricted page
- All API endpoints require valid session token
- Telegram notifications sent for all hits

## License

This project is for educational purposes only.
