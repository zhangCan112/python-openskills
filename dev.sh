#!/usr/bin/env bash
set -e

cmd="${1:-install}"

case "$cmd" in
    install)
        pip install --force-reinstall --no-deps .
        ;;
    install-dev)
        pip install --force-reinstall --no-deps -e .
        ;;
    uninstall)
        pip uninstall -y openskills
        ;;
    clean)
        rm -rf build/ dist/ *.egg-info openskills.egg-info
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        ;;
    test)
        python -m pytest tests/ -v
        ;;
    *)
        echo "Usage: $0 [install|install-dev|uninstall|clean|test]"
        echo ""
        echo "  install      Install from source (default)"
        echo "  install-dev  Install in editable mode"
        echo "  uninstall    Uninstall openskills"
        echo "  clean        Remove build artifacts"
        echo "  test         Run tests"
        exit 1
        ;;
esac
