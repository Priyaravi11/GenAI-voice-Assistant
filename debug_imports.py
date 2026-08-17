import sys
sys.path.insert(0, '.')

# Test each import step by step
print("[1] Testing config import...")
try:
    from backend.app.config import settings
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

print("[2] Testing context import...")
try:
    from backend.app.context import get_or_create_session
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

print("[3] Testing validation import...")
try:
    from backend.app.validation import validate_session_id
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

print("[4] Testing RAG import...")
try:
    from backend.app.rag import retrieve_context
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

print("[5] Testing orchestrator import...")
try:
    from backend.app.orchestrator import orchestrator
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[6] Testing main import...")
try:
    from backend.app.main import app
    print("    OK")
    print(f"\nSUCCESS: All imports OK")
    print(f"App: {app.title}")
except Exception as e:
    print(f"    FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
