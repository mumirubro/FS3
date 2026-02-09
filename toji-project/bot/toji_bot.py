#!/usr/bin/env python3
"""
TOJI Telegram Bot - Advanced Session Management & User Registration
Bot: @TOJIchk_bot
Token: 8543073349:AAE4g6AcLSgBTEz5b3sXaBJlDIhZnQopVE0
"""

import asyncio
import json
import secrets
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
import io

# Fix Windows console encoding issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# JWT-like token functions
def create_session_token(user_id: int, username: str) -> str:
    """Create a JWT-like session token that frontend can validate"""
    expires_at = datetime.now() + timedelta(seconds=SESSION_DURATION)
    
    # Create payload
    payload = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "active": True
    }
    
    # Encode as base64 (simple JWT-like format)
    header = base64.urlsafe_b64encode(json.dumps({"typ": "JWT", "alg": "none"}).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
    
    return f"{header}.{payload_b64}.{signature}"

# Bot Configuration
BOT_TOKEN = "8543073349:AAE4g6AcLSgBTEz5b3sXaBJlDIhZnQopVE0"
WEBAPP_URL = "http://localhost:5173"  # Local development URL
SESSION_DURATION = 30 * 60  # 30 minutes in seconds

# Data Storage - Use absolute path to shared directory
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRIPT_DIR)  # Parent directory (toji-project)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

# Path logs disabled to prevent encoding errors on Windows
# print(f"Data directory: {DATA_DIR}")
# print(f"Users file: {USERS_FILE}")
# print(f"Sessions file: {SESSIONS_FILE}")


class DataManager:
    """Manage user data and sessions"""
    
    @staticmethod
    def load_users() -> Dict:
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def save_users(users: Dict):
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    
    @staticmethod
    def load_sessions() -> Dict:
        try:
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @staticmethod
    def save_sessions(sessions: Dict):
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    @staticmethod
    def generate_session_token(user_id: int = 0, username: str = "") -> str:
        """Generate a session token - now uses JWT-like format"""
        return create_session_token(user_id, username)
    
    @staticmethod
    def is_session_valid(session_token: str) -> bool:
        sessions = DataManager.load_sessions()
        if session_token not in sessions:
            return False
        session = sessions[session_token]
        expiry = datetime.fromisoformat(session['expires_at'])
        return datetime.now() < expiry


# Initialize data files
for file in [USERS_FILE, SESSIONS_FILE]:
    try:
        with open(file, 'r') as f:
            pass
    except FileNotFoundError:
        with open(file, 'w') as f:
            json.dump({}, f)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    users = DataManager.load_users()
    
    # Check if user is registered
    if str(user.id) not in users:
        # Show registration message
        welcome_text = f"""
🌟 <b>Welcome to TOJI Checker Platform!</b> 🌟

👤 <b>User:</b> {user.first_name}
🆔 <b>ID:</b> <code>{user.id}</code>

⚠️ <b>You are not registered yet!</b>

Click the button below to register and access the TOJI WebApp.

📌 <b>Features:</b>
• Advanced CC Checkers
• Account Checkers (Steam, Crunchyroll, Hotmail)
• SK Key Validator
• PayPal & Stripe Tools
• Real-time Results
• 30-Minute Sessions

<i>🔒 Secure • ⚡ Fast • 🎯 Reliable</i>
"""
        keyboard = [[InlineKeyboardButton("📝 REGISTER NOW", callback_data="register")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        # User is registered, show session options
        user_data = users[str(user.id)]
        welcome_back = f"""
🎉 <b>Welcome back to TOJI, {user.first_name}!</b> 🎉

✅ <b>You are registered!</b>
📅 <b>Registered:</b> {user_data.get('registered_at', 'N/A')}

Choose an option below:
"""
        keyboard = [
            [InlineKeyboardButton("🔑 CREATE SESSION", callback_data="create_session")],
            [InlineKeyboardButton("📊 MY STATS", callback_data="my_stats")],
            [InlineKeyboardButton("💬 SUPPORT", url="https://t.me/TOJISupport")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            welcome_back,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    users = DataManager.load_users()
    
    # Register user
    users[str(user.id)] = {
        "user_id": user.id,
        "username": user.username or "N/A",
        "first_name": user.first_name or "N/A",
        "last_name": user.last_name or "N/A",
        "registered_at": datetime.now().isoformat(),
        "total_checks": 0,
        "total_hits": 0,
        "premium": False
    }
    DataManager.save_users(users)
    
    success_text = f"""
✅ <b>Registration Successful!</b> ✅

🎊 <b>Welcome to TOJI, {user.first_name}!</b>

Your account has been created with:
🆔 <b>User ID:</b> <code>{user.id}</code>
👤 <b>Username:</b> @{user.username or 'N/A'}

🚀 <b>Next Step:</b> Create a session to access the WebApp!

<i>Sessions expire after 30 minutes of inactivity.</i>
"""
    keyboard = [
        [InlineKeyboardButton("🔑 CREATE SESSION", callback_data="create_session")],
        [InlineKeyboardButton("🔙 Back to Start", callback_data="start_again")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        success_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def create_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle session creation"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    users = DataManager.load_users()
    sessions = DataManager.load_sessions()
    
    # Check if user is registered
    if str(user.id) not in users:
        await query.edit_message_text(
            "⚠️ Please register first! Use /start",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Generate new session with user info
    session_token = DataManager.generate_session_token(user.id, user.username or "N/A")
    expires_at = datetime.now() + timedelta(seconds=SESSION_DURATION)
    
    # Save session
    sessions[session_token] = {
        "user_id": user.id,
        "username": user.username or "N/A",
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "active": True
    }
    DataManager.save_sessions(sessions)
    
    print(f"Session created for user {user.id}: {session_token[:30]}...")
    
    # Create WebApp URL with session
    webapp_url = f"{WEBAPP_URL}?session={session_token}"
    
    
    session_text = f"""
🔐 <b>Session Created Successfully!</b> 🔐

⏱ <b>Duration:</b> 30 Minutes
⏳ <b>Expires:</b> {expires_at.strftime('%H:%M:%S')}

🔑 <b>Your Session Token:</b>
<code>{session_token}</code>

📱 <b>To Access Web App:</b>
1. Open your browser (Chrome/Firefox)
2. Go to: <code>http://localhost:5173</code>
3. Paste this URL with your token:
<code>http://localhost:5173?session={session_token}</code>

⚠️ <b>Note:</b> Session expires in 30 minutes.
"""
    keyboard = [
        [InlineKeyboardButton("♻️ NEW SESSION", callback_data="create_session")],
        [InlineKeyboardButton("📊 MY STATS", callback_data="my_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        session_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def my_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user stats"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    users = DataManager.load_users()
    
    if str(user.id) not in users:
        await query.edit_message_text(
            "⚠️ Please register first! Use /start",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_data = users[str(user.id)]
    
    stats_text = f"""
📊 <b>Your TOJI Statistics</b> 📊

👤 <b>User:</b> {user_data.get('first_name', 'N/A')}
🆔 <b>ID:</b> <code>{user_data.get('user_id', 'N/A')}</code>
📅 <b>Registered:</b> {user_data.get('registered_at', 'N/A')[:10]}

📈 <b>Activity:</b>
• Total Checks: {user_data.get('total_checks', 0)}
• Total Hits: {user_data.get('total_hits', 0)}
• Success Rate: {((user_data.get('total_hits', 0) / max(user_data.get('total_checks', 1), 1)) * 100):.1f}%

💎 <b>Premium:</b> {'✅ Yes' if user_data.get('premium') else '❌ No'}

<i>Keep checking to increase your stats!</i>
"""
    keyboard = [
        [InlineKeyboardButton("🔑 CREATE SESSION", callback_data="create_session")],
        [InlineKeyboardButton("🔙 Back", callback_data="start_again")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def start_again_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to start menu"""
    query = update.callback_query
    await query.answer()
    
    # Trigger start command
    await start_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = f"""
📖 <b>TOJI Bot Commands</b> 📖

/start - Start the bot / View main menu
/help - Show this help message
/status - Check your session status
/stats - View your statistics

🔹 <b>How to use:</b>
1. Send /start to register
2. Click "CREATE SESSION"
3. Click "OPEN WEB APP"
4. Start checking!

🔹 <b>Session Info:</b>
• Sessions last 30 minutes
• Auto-expire after inactivity
• Create new session anytime

🔹 <b>Need Help?</b>
Contact: @TOJISupport
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check session status"""
    user = update.effective_user
    sessions = DataManager.load_sessions()
    
    # Find active session for user
    active_session = None
    for token, session in sessions.items():
        if session.get("user_id") == user.id and DataManager.is_session_valid(token):
            active_session = (token, session)
            break
    
    if active_session:
        token, session = active_session
        expires = datetime.fromisoformat(session['expires_at'])
        remaining = expires - datetime.now()
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        status_text = f"""
✅ <b>Active Session Found!</b>

⏱ <b>Time Remaining:</b> {minutes}m {seconds}s
⏳ <b>Expires At:</b> {expires.strftime('%H:%M:%S')}

🔑 <b>Session Token:</b>
<code>{token[:20]}...</code>

<a href="{WEBAPP_URL}?session={token}">🌐 Open WebApp</a>
"""
    else:
        status_text = """
❌ <b>No Active Session</b>

You don't have an active session.
Use /start to create a new session.
"""
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.HTML)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats command"""
    user = update.effective_user
    users = DataManager.load_users()
    
    if str(user.id) not in users:
        await update.message.reply_text(
            "⚠️ Please register first! Use /start",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_data = users[str(user.id)]
    
    stats_text = f"""
📊 <b>Your Statistics</b> 📊

👤 User: {user_data.get('first_name', 'N/A')}
📅 Registered: {user_data.get('registered_at', 'N/A')[:10]}

📈 Checks: {user_data.get('total_checks', 0)}
🎯 Hits: {user_data.get('total_hits', 0)}
💎 Premium: {'Yes' if user_data.get('premium') else 'No'}
"""
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)


def main():
    """Start the bot"""
    print("Starting TOJI Telegram Bot...")
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(register_callback, pattern="^register$"))
    application.add_handler(CallbackQueryHandler(create_session_callback, pattern="^create_session$"))
    application.add_handler(CallbackQueryHandler(my_stats_callback, pattern="^my_stats$"))
    application.add_handler(CallbackQueryHandler(start_again_callback, pattern="^start_again$"))
    
    print("Bot started successfully!")
    print("Waiting for users...")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
