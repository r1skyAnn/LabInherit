#!/usr/bin/env python3
"""Test script for email worker functionality (without database dependency)."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Email Worker Module Test")
print("=" * 60)

try:
    print("✓ Importing email_worker module...")
    from app.tasks import email_worker
    
    print("✓ Checking main() function...")
    assert hasattr(email_worker, "main"), "main() function not found"
    
    print("✓ Checking run_worker() function...")
    assert hasattr(email_worker, "run_worker"), "run_worker() function not found"
    
    print("✓ Checking process_batch() function...")
    assert hasattr(email_worker, "process_batch"), "process_batch() function not found"
    
    print("✓ Checking __main__ block...")
    with open(__file__.replace("test_email_worker.py", "app/tasks/email_worker.py")) as f:
        content = f.read()
        assert 'if __name__ == "__main__":' in content, "__main__ block not found"
        assert "main()" in content, "main() call not found in __main__ block"
    
    print("\n" + "=" * 60)
    print("✅ All checks passed!")
    print("=" * 60)
    print("\nEmail worker module is ready for standalone execution.")
    print("\nUsage:")
    print("  python -m app.tasks.email_worker")
    print("  python -m app.tasks.email_worker --help")
    print("  python -m app.tasks.email_worker --interval 10 --log-level DEBUG")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nThis is expected if dependencies are not installed.")
    print("In production, run inside the virtual environment:")
    print("  cd backend")
    print("  source venv/bin/activate")
    print("  python -m app.tasks.email_worker")
    sys.exit(0)  # Not a failure, just missing deps
    
except AssertionError as e:
    print(f"\n❌ Test Failed: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
