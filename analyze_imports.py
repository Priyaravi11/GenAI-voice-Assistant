#!/usr/bin/env python3
"""
Comprehensive import and code analysis script.
Identifies broken imports, circular dependencies, and missing implementations.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_import(module_name, description):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✓ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"✗ {description}: {module_name}")
        print(f"  Error: {e}")
        return False
    except Exception as e:
        print(f"✗ {description}: {module_name}")
        print(f"  Unexpected error: {type(e).__name__}: {e}")
        return False

def check_file_content(filepath, search_terms):
    """Check if a file contains expected content."""
    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    missing = []
    for term in search_terms:
        if term not in content:
            missing.append(term)
    
    if missing:
        print(f"✗ {filepath} missing: {missing}")
        return False
    
    print(f"✓ {filepath} contains expected code")
    return True

# ============================================================
# MAIN IMPORT TESTS
# ============================================================

print("\n" + "="*60)
print("IMPORT ANALYSIS")
print("="*60 + "\n")

results = {}

print("Backend App Core:")
results['main'] = test_import('backend.app.main', 'Main app')
results['config'] = test_import('backend.app.config', 'Config')
results['orchestrator'] = test_import('backend.app.orchestrator', 'Orchestrator')
results['gemini'] = test_import('backend.app.gemini', 'Gemini client')
results['rag'] = test_import('backend.app.rag', 'RAG service')
results['tools'] = test_import('backend.app.tools', 'Tools registry')
results['validation'] = test_import('backend.app.validation', 'Validation')
results['context'] = test_import('backend.app.context', 'Session context')
results['escalation'] = test_import('backend.app.escalation', 'Escalation handler')

print("\nBackend Agents:")
try:
    from backend.app.agents import general_agent
    print("✓ General agent imports")
    results['agents'] = True
except Exception as e:
    print(f"✗ General agent failed: {e}")
    results['agents'] = False

print("\nBackend API Routes:")
results['session_route'] = test_import('backend.app.api.routes.session', 'Session routes')

print("\nRAG Module:")
results['rag_module'] = test_import('rag', 'RAG package')

print("\nTools Module:")
results['tools_module'] = test_import('tools', 'Tools package')

# ============================================================
# FILE CONTENT CHECKS
# ============================================================

print("\n" + "="*60)
print("CODE IMPLEMENTATION STATUS")
print("="*60 + "\n")

print("Checking websocket.py implementation:")
ws_path = PROJECT_ROOT / "backend" / "app" / "websocket.py"
websocket_checks = check_file_content(str(ws_path), ['@router.websocket', 'async def'])

print("\nChecking orchestrator.py implementation:")
orch_path = PROJECT_ROOT / "backend" / "app" / "orchestrator.py"
orchestrator_checks = check_file_content(str(orch_path), ['class Orchestrator', 'async def process_text'])

print("\nChecking agents imports:")
gen_path = PROJECT_ROOT / "backend" / "app" / "agents" / "general_agent.py"
general_checks = check_file_content(str(gen_path), ['class GeneralAgent', 'async def handle'])

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "="*60)
print("SUMMARY")
print("="*60 + "\n")

success_count = sum(1 for v in results.values() if v)
total_count = len(results)

print(f"Import Results: {success_count}/{total_count} successful")
print(f"\nFailed imports:")
for name, success in results.items():
    if not success:
        print(f"  - {name}")

print("\nCritical Issues Identified:")
if not websocket_checks:
    print("  ✗ WebSocket router not implemented")
if not orchestrator_checks:
    print("  ✗ Orchestrator class not properly implemented")
