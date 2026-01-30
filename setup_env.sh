#!/bin/bash
# OpenSkills 虚拟环境设置脚本 (Linux/Mac)

echo "========================================"
echo "OpenSkills 虚拟环境设置"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3。请先安装Python 3.8或更高版本。"
    exit 1
fi

echo "[检查] Python版本: $(python3 --version)"

# 检查虚拟环境是否已存在
if [ -d ".venv" ]; then
    echo "[提示] 虚拟环境已存在，正在移除..."
    rm -rf .venv
fi

echo "[1/3] 创建虚拟环境..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "[错误] 创建虚拟环境失败。"
    exit 1
fi

echo "[2/3] 激活虚拟环境..."
source .venv/bin/activate

echo "[3/3] 安装依赖..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "[错误] 安装依赖失败。"
    exit 1
fi

echo
echo "========================================"
echo "[成功] 虚拟环境设置完成！"
echo "========================================"
echo
echo "使用说明："
echo "  1. 激活虚拟环境: source .venv/bin/activate"
echo "  2. 使用命令: openskills --help"
echo "  3. 退出虚拟环境: deactivate"
echo