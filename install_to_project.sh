#!/bin/bash
# OpenSkills installation to target project script (Linux/Mac)
# Usage: bash install_to_project.sh <target_project_path>

# Check parameters
if [ -z "$1" ]; then
    echo "========================================"
    echo "OpenSkills Installation to Target Project"
    echo "========================================"
    echo ""
    echo "Usage: bash install_to_project.sh <target_project_path>"
    echo ""
    echo "Examples:"
    echo "  bash install_to_project.sh /home/user/my-project"
    echo "  bash install_to_project.sh ../my-project"
    echo ""
    exit 1
fi

TARGET_PROJECT="$1"

echo "========================================"
echo "OpenSkills Installation to Target Project"
echo "========================================"
echo ""
echo "Target project path: $TARGET_PROJECT"
echo ""

# Check if target project path exists
if [ ! -d "$TARGET_PROJECT" ]; then
    echo "[Error] Target project path does not exist: $TARGET_PROJECT"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "[Check] Python version: $(python3 --version)"

# Get absolute path of OpenSkills project BEFORE changing directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Enter target project directory
cd "$TARGET_PROJECT" || {
    echo "[Error] Cannot enter target project directory: $TARGET_PROJECT"
    exit 1
}

echo "[1/5] Creating virtual environment in target project..."
if [ -d ".venv" ]; then
    echo "[Info] Virtual environment already exists, removing..."
    rm -rf .venv
fi

python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "[Error] Failed to create virtual environment."
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source .venv/bin/activate

echo "[3/5] Installing OpenSkills..."
pip install -e "$SCRIPT_DIR"
if [ $? -ne 0 ]; then
    echo "[Error] Failed to install OpenSkills."
    exit 1
fi

echo "[4/5] Adding to .gitignore..."
GITIGNORE=".gitignore"
FOUND=0

if [ -f "$GITIGNORE" ]; then
    if grep -q "^\.venv" "$GITIGNORE" || grep -q "^\.venv/" "$GITIGNORE"; then
        FOUND=1
    fi
fi

if [ $FOUND -eq 0 ]; then
    echo "" >> "$GITIGNORE"
    echo "# OpenSkills virtual environment" >> "$GITIGNORE"
    echo ".venv/" >> "$GITIGNORE"
    echo "[Info] Added .venv to .gitignore"
else
    echo "[Info] .venv already in .gitignore, skipped"
fi

echo "[5/5] Creating startup script..."
# Create convenient startup script
cat > openskills.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
openskills "$@"
deactivate
EOF

chmod +x openskills.sh

echo ""
echo "========================================"
echo "[Success] OpenSkills Installation Complete!"
echo "========================================"
echo ""
echo "Usage:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Use command: openskills --help"
echo "  3. Or use quick command: ./openskills.sh --help"
echo "  4. Deactivate virtual environment: deactivate"
echo ""
echo "Note:"
echo "  - Virtual environment added to .gitignore, will not commit to git"
echo "  - Created openskills.sh quick script in project root"
echo ""