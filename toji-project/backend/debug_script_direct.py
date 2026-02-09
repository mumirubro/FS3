import sys
import os
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Setup paths (mimicking script_wrappers.py)
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # backend -> toji-project -> root
GATES_DIR = PROJECT_ROOT / "gates"

print(f"DEBUG: Project Root: {PROJECT_ROOT}")
print(f"DEBUG: Gates Dir: {GATES_DIR}")

def test_paypal_cvv():
    print("DEBUG: Starting test_paypal_cvv...")
    try:
        paypal_cvv_dir = GATES_DIR / "paypal cvv 0.1$"
        if not paypal_cvv_dir.exists():
            print(f"ERROR: Directory not found: {paypal_cvv_dir}")
            return
            
        print(f"DEBUG: Adding to path: {paypal_cvv_dir}")
        sys.path.insert(0, str(paypal_cvv_dir))
        
        print("DEBUG: Attempting import...")
        try:
            import paypalcvv
            print(f"DEBUG: Imported module: {paypal_cvv}")
            from paypalcvv import drgam
        except ImportError as e:
            print(f"ERROR: Import failed: {e}")
            # List files in that dir to help debug
            print(f"Files in {paypal_cvv_dir}:")
            for f in paypal_cvv_dir.glob("*"):
                print(f"  - {f.name}")
            return

        test_card = "4960780013941619|03|27|779"
        print(f"DEBUG: Calling drgam with {test_card}...")
        
        # Set a timeout signal if possible, but for now just run it
        result = drgam(test_card)
        print(f"DEBUG: Result: {result}")
        
    except Exception as e:
        print(f"ERROR: Exception during check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_paypal_cvv()
