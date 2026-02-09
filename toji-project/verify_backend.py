import asyncio
import json
from pathlib import Path
import httpx
from backend.main import DataManager, FILE_LOCKS, SESSIONS_FILE, USERS_FILE

async def test_data_manager():
    print("Testing DataManager Async Operations...")
    
    # Test session validation
    session_token = "test_token"
    # Setup test file
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, 'w') as f:
        json.dump({
            session_token: {
                "user_id": 123,
                "expires_at": "2030-01-01T00:00:00",
                "active": True,
                "created_at": "2024-02-08T00:00:00"
            }
        }, f)
    
    # Run concurrent validations
    print("Running 10 concurrent session validations...")
    tasks = [DataManager.validate_session_async(session_token) for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r is not None)
    print(f"Success: {success_count}/10")
    
    # Check if last_activity was updated
    sessions = DataManager.load_json(SESSIONS_FILE)
    print(f"Last activity updated: {'last_activity' in sessions[session_token]}")

async def test_background_logic():
    print("\nTesting Background Logic placeholder...")
    # Since we can't easily trigger the FastAPI background tasks without a full server environment here,
    # we'll just check if the functions exist and are callable.
    from backend.main import run_paypal_cvv_check, PayPalCVVChecker
    
    print("Checking if checker endpoints logic is defined...")
    assert callable(run_paypal_cvv_check)
    print("Verification successful.")

if __name__ == "__main__":
    asyncio.run(test_data_manager())
    asyncio.run(test_background_logic())
