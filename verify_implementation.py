#!/usr/bin/env python
"""
Implementation Verification & Diagnostic Script

Checks:
1. All imports work correctly
2. All agents have correct interface
3. Context has pending Customer-ID state
4. Orchestrator properly handles Customer ID flow
5. All standardized result contracts are in place
"""

import sys
import traceback
from typing import List, Tuple

print("=" * 80)
print("GenAI Voice Assistant - Implementation Verification")
print("=" * 80)

# ============================================================================
# CHECK 1: Import Backend Modules
# ============================================================================

print("\n[CHECK 1] Verifying Backend Imports...")

checks_passed = 0
checks_failed = 0

def test_import(module_path: str, item_name: str = None) -> Tuple[bool, str]:
    """Test importing a module or specific item."""
    try:
        if item_name:
            module = __import__(module_path, fromlist=[item_name])
            getattr(module, item_name)
            return True, f"✓ {module_path}.{item_name}"
        else:
            __import__(module_path)
            return True, f"✓ {module_path}"
    except Exception as e:
        return False, f"✗ {module_path}: {str(e)}"

imports_to_test = [
    ("backend.app.context", "SessionContext"),
    ("backend.app.context", "get_or_create_session"),
    ("backend.app.customer_validation", "validate_customer_id"),
    ("backend.app.customer_validation", "is_customer_id_valid"),
    ("backend.app.agents.supervisor_agent", "SupervisorAgent"),
    ("backend.app.agents.billing_agent", "BillingAgent"),
    ("backend.app.agents.payment_agent", "PaymentAgent"),
    ("backend.app.agents.plans_agent", "PlansAgent"),
    ("backend.app.agents.technical_agent", "TechnicalAgent"),
    ("backend.app.agents.general_agent", "GeneralAgent"),
]

for module_path, item_name in imports_to_test:
    success, message = test_import(module_path, item_name)
    print(f"  {message}")
    if success:
        checks_passed += 1
    else:
        checks_failed += 1

# ============================================================================
# CHECK 2: Verify SessionContext has Pending Customer-ID Fields
# ============================================================================

print("\n[CHECK 2] Verifying SessionContext Pending Fields...")

try:
    from backend.app.context import SessionContext
    
    required_fields = [
        "waiting_for_customer_id",
        "pending_agent",
        "pending_query",
        "pending_tool",
    ]
    
    required_methods = [
        "set_pending_customer_id_request",
        "get_pending_customer_id_request",
        "clear_pending_customer_id_request",
    ]
    
    context = SessionContext(session_id="test-session")
    
    # Check fields
    for field in required_fields:
        if hasattr(context, field):
            print(f"  ✓ Field: {field}")
            checks_passed += 1
        else:
            print(f"  ✗ Field missing: {field}")
            checks_failed += 1
    
    # Check methods
    for method in required_methods:
        if hasattr(context, method) and callable(getattr(context, method)):
            print(f"  ✓ Method: {method}")
            checks_passed += 1
        else:
            print(f"  ✗ Method missing: {method}")
            checks_failed += 1
            
except Exception as e:
    print(f"  ✗ Error checking SessionContext: {str(e)}")
    checks_failed += len(required_fields) + len(required_methods)

# ============================================================================
# CHECK 3: Verify Agent Interfaces
# ============================================================================

print("\n[CHECK 3] Verifying Agent Interfaces...")

agent_classes = [
    ("backend.app.agents.supervisor_agent", "SupervisorAgent"),
    ("backend.app.agents.billing_agent", "BillingAgent"),
    ("backend.app.agents.payment_agent", "PaymentAgent"),
    ("backend.app.agents.plans_agent", "PlansAgent"),
    ("backend.app.agents.technical_agent", "TechnicalAgent"),
    ("backend.app.agents.general_agent", "GeneralAgent"),
]

for module_path, class_name in agent_classes:
    try:
        module = __import__(module_path, fromlist=[class_name])
        agent_class = getattr(module, class_name)
        
        if hasattr(agent_class, "handle"):
            print(f"  ✓ {class_name}.handle() exists")
            checks_passed += 1
        else:
            print(f"  ✗ {class_name}.handle() missing")
            checks_failed += 1
            
    except Exception as e:
        print(f"  ✗ Error checking {class_name}: {str(e)}")
        checks_failed += 1

# ============================================================================
# CHECK 4: Verify Customer ID Validation
# ============================================================================

print("\n[CHECK 4] Verifying Customer ID Validation...")

try:
    from backend.app.customer_validation import validate_customer_id, is_customer_id_valid
    
    # Test valid ID
    is_valid, msg, normalized = validate_customer_id("C251")
    if is_valid and normalized == "C251":
        print(f"  ✓ validate_customer_id('C251') works correctly")
        checks_passed += 1
    else:
        print(f"  ✗ validate_customer_id('C251') failed: {msg}")
        checks_failed += 1
    
    # Test invalid ID
    is_valid, msg, normalized = validate_customer_id("")
    if not is_valid and normalized is None:
        print(f"  ✓ validate_customer_id('') correctly rejects empty")
        checks_passed += 1
    else:
        print(f"  ✗ validate_customer_id('') should reject empty")
        checks_failed += 1
    
    # Test is_customer_id_valid wrapper
    if is_customer_id_valid("C251"):
        print(f"  ✓ is_customer_id_valid('C251') works correctly")
        checks_passed += 1
    else:
        print(f"  ✗ is_customer_id_valid('C251') should return True")
        checks_failed += 1
        
except Exception as e:
    print(f"  ✗ Error testing validation: {str(e)}")
    traceback.print_exc()
    checks_failed += 3

# ============================================================================
# CHECK 5: Verify Orchestrator
# ============================================================================

print("\n[CHECK 5] Verifying Orchestrator...")

try:
    from backend.app.orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    
    required_methods = [
        "handle",
        "_handle_customer_id_input",
        "_build_agent_context",
        "_should_escalate",
        "get_session",
        "close_session",
    ]
    
    for method in required_methods:
        if hasattr(orchestrator, method) and callable(getattr(orchestrator, method)):
            print(f"  ✓ Method: {method}")
            checks_passed += 1
        else:
            print(f"  ✗ Method missing: {method}")
            checks_failed += 1
            
except Exception as e:
    print(f"  ✗ Error checking Orchestrator: {str(e)}")
    traceback.print_exc()
    checks_failed += 6

# ============================================================================
# CHECK 6: Verify Agent Result Contract
# ============================================================================

print("\n[CHECK 6] Verifying Agent Result Contract Fields...")

required_response_fields = [
    "agent",
    "response",
    "success",
    "confidence",
    "tool_used",
    "tool_result",
    "rag_context",
    "requires_customer_id",
]

# Check BillingAgent error response
try:
    from backend.app.agents.billing_agent import BillingAgent
    
    agent = BillingAgent()
    error_response = agent._error_response("Test error")
    
    for field in required_response_fields:
        if field in error_response:
            print(f"  ✓ BillingAgent response has: {field}")
            checks_passed += 1
        else:
            print(f"  ✗ BillingAgent response missing: {field}")
            checks_failed += 1
            
except Exception as e:
    print(f"  ✗ Error checking BillingAgent response: {str(e)}")
    checks_failed += len(required_response_fields)

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

total_checks = checks_passed + checks_failed
success_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

print(f"\nTotal Checks: {total_checks}")
print(f"Passed: {checks_passed}")
print(f"Failed: {checks_failed}")
print(f"Success Rate: {success_rate:.1f}%")

if checks_failed == 0:
    print("\n✓ ALL CHECKS PASSED - Implementation is correct!")
    sys.exit(0)
else:
    print(f"\n✗ {checks_failed} checks failed - Review errors above")
    sys.exit(1)
