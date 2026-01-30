"""
Test script to verify OpenSkills Python package functionality
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
print("Testing imports...")
try:
    import openskills
    print(f"[OK] openskills imported from: {openskills.__file__ if hasattr(openskills, '__file__') else 'namespace package'}")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills: {e}")
    sys.exit(1)

try:
    from openskills import cli
    print("[OK] openskills.cli imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.cli: {e}")
    sys.exit(1)

try:
    from openskills import types
    print("[OK] openskills.types imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.types: {e}")
    sys.exit(1)

try:
    from openskills import commands
    print(f"[OK] openskills.commands imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.commands: {e}")
    sys.exit(1)

try:
    from openskills import utils
    print("[OK] openskills.utils imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.utils: {e}")
    sys.exit(1)

print("\nTesting CLI help...")
try:
    from openskills.cli import cli
    cli(['--help'])
    print("\n[OK] CLI help displayed successfully")
except Exception as e:
    print(f"[FAIL] CLI test failed: {e}")
    sys.exit(1)

print("\n[SUCCESS] All tests passed! OpenSkills Python package is working correctly.")
