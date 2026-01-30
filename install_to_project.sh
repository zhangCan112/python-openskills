#!/bin/bash
# OpenSkills 安装到目标项目脚本 (Linux/Mac)
# 用法: bash install_to_project.sh <目标项目路径>

# 检查参数
if [ -z "$1" ]; then
    echo "========================================"
    echo "OpenSkills 安装到目标项目"
    echo "========================================"
    echo ""
    echo "用法: bash install_to_project.sh <目标项目路径>"
    echo ""
    echo "示例:"
    echo "  bash install_to_project.sh /home/user/my-project"
    echo "  bash install_to_project.sh ../my-project"
    echo ""
    exit 1
fi

TARGET_PROJECT="$1"

echo "========================================"
echo "OpenSkills 安装到目标项目"
echo "========================================"
echo ""
echo "目标项目路径: $TARGET_PROJECT"
echo ""

# 检查目标项目路径是否存在
if [ ! -d "$TARGET_PROJECT" ]; then
    echo "[错误] 目标项目路径不存在: $TARGET_PROJECT"
    exit 1
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3。请先安装Python 3.8或更高版本。"
    exit 1
fi

echo "[检查] Python版本: $(python3 --version)"

# 进入目标项目目录
cd "$TARGET_PROJECT" || {
    echo "[错误] 无法进入目标项目目录: $TARGET_PROJECT"
    exit 1
}

echo "[1/5] 在目标项目中创建虚拟环境..."
if [ -d ".venv" ]; then
    echo "[提示] 虚拟环境已存在，正在移除..."
    rm -rf .venv
fi

python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "[错误] 创建虚拟环境失败。"
    exit 1
fi

echo "[2/5] 激活虚拟环境..."
source .venv/bin/activate

echo "[3/5] 安装OpenSkills..."
# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pip install -e "$SCRIPT_DIR"
if [ $? -ne 0 ]; then
    echo "[错误] 安装OpenSkills失败。"
    exit 1
fi

echo "[4/5] 添加到.gitignore..."
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
    echo "[提示] 已添加 .venv 到 .gitignore"
else
    echo "[提示] .venv 已在 .gitignore 中，跳过"
fi

echo "[5/5] 创建启动脚本..."
# 创建便捷的启动脚本
cat > openskills.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
openskills "$@"
deactivate
EOF

chmod +x openskills.sh

echo ""
echo "========================================"
echo "[成功] OpenSkills安装完成！"
echo "========================================"
echo ""
echo "使用说明："
echo "  1. 激活虚拟环境: source .venv/bin/activate"
echo "  2. 使用命令: openskills --help"
echo "  3. 或使用快捷命令: ./openskills.sh --help"
echo "  4. 退出虚拟环境: deactivate"
echo ""
echo "注意："
echo "  - 虚拟环境已添加到 .gitignore，不会提交到git"
echo "  - 项目根目录已创建 openskills.sh 快捷脚本"
echo ""