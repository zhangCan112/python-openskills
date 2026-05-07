import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")
try:
    import openskills
    print(f"[OK] openskills v{openskills.__version__}")
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
    from openskills import models
    print("[OK] openskills.models imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.models: {e}")
    sys.exit(1)

try:
    from openskills import finder
    print("[OK] openskills.finder imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.finder: {e}")
    sys.exit(1)

try:
    from openskills import market
    print("[OK] openskills.market imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.market: {e}")
    sys.exit(1)

try:
    from openskills import installer
    print("[OK] openskills.installer imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.installer: {e}")
    sys.exit(1)

try:
    from openskills import updater
    print("[OK] openskills.updater imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.updater: {e}")
    sys.exit(1)

try:
    from openskills import remover
    print("[OK] openskills.remover imported")
except ImportError as e:
    print(f"[FAIL] Failed to import openskills.remover: {e}")
    sys.exit(1)

print("\nTesting CLI help...")
try:
    from openskills.cli import cli
    cli(['--help'])
    print("\n[OK] CLI help displayed successfully")
except Exception as e:
    print(f"[FAIL] CLI test failed: {e}")
    sys.exit(1)

print("\n[SUCCESS] All tests passed!")
