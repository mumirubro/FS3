#!/usr/bin/env python3
"""
Test script for TOJI session validation
"""

import json
import base64
from datetime import datetime, timedelta

def create_test_session(user_id: int = 12345, username: str = "test_user") -> str:
    """Create a test session token"""
    expires_at = datetime.now() + timedelta(minutes=30)
    
    payload = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "active": True
    }
    
    header = base64.urlsafe_b64encode(json.dumps({"typ": "JWT", "alg": "none"}).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    signature = base64.urlsafe_b64encode(b"test_signature").decode().rstrip('=')
    
    return f"{header}.{payload_b64}.{signature}"

def decode_token(token: str) -> dict:
    """Decode a session token"""
    parts = token.split('.')
    if len(parts) >= 2:
        payload_base64 = parts[1]
        # Add padding
        while len(payload_base64) % 4:
            payload_base64 += '='
        payload_json = base64.urlsafe_b64decode(payload_base64.replace('-', '+').replace('_', '/'))
        return json.loads(payload_json)
    return {}

if __name__ == "__main__":
    print("🧪 Testing TOJI Session Token")
    print("=" * 50)
    
    # Create a test session
    token = create_test_session()
    print(f"\n✅ Created session token:")
    print(f"   {token[:60]}...")
    
    # Decode it
    payload = decode_token(token)
    print(f"\n📋 Decoded payload:")
    print(f"   User ID: {payload.get('user_id')}")
    print(f"   Username: {payload.get('username')}")
    print(f"   Expires: {payload.get('expires_at')}")
    
    # Check if valid
    expires_at = datetime.fromisoformat(payload.get('expires_at', ''))
    is_valid = expires_at > datetime.now()
    print(f"\n🔍 Session valid: {is_valid}")
    
    # Generate URL
    webapp_url = f"https://a5cqaelblt54g.ok.kimi.link?session={token}"
    print(f"\n🌐 Test URL:")
    print(f"   {webapp_url[:80]}...")
    
    print("\n" + "=" * 50)
    print("✨ Copy the full URL and test in your browser!")
