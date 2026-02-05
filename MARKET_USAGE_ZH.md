# Skill Market 功能使用说明

## 概述

Skill Market 功能允许维护者从远端仓库收集 skills 信息，并让使用者通过简单的命令安装这些 skills。

## 维护者使用指南

### 1. 配置源仓库

编辑 `market_sources.yaml` 文件，添加要收集的仓库：

```yaml
sources:
  - repo: "https://github.com/owner/repo1"
    branch: "main"
  - repo: "https://github.com/owner/repo2"
    branch: "master"
```

**重要提示**: 仓库URL必须是完整的URL。不支持 `owner/repo` 这样的简写格式。

### 2. 收集 Skills

运行收集脚本从配置的仓库中收集 skills 信息：

```bash
python scripts/collect_market_skills.py
```

脚本会：
- Clone 配置的仓库到临时目录
- 解析每个仓库中的 SKILL.md 文件
- 提取技能信息（名称、描述、版本、作者、标签等）
- 保存到 `marketskills/owner_repo.json` 文件中

### 3. 更新 Market 数据

当仓库有更新时，重新运行收集脚本即可更新 market 数据。

## 使用者使用指南

### 1. 查看可用的 Skills

#### 列出所有 skills

```bash
openskills market list
```

#### 按 tag 过滤

支持通过 tag 过滤 skills：

```bash
# 单个 tag 过滤
openskills market list -t development

# 多个 tag 过滤（AND 逻辑）
openskills market list -t development -t workflow
```

**说明**：
- `-t` 或 `--tag` 选项可以多次使用
- 多个 tag 之间使用 AND 逻辑（skill 必须包含所有指定的 tags）
- tag 过滤不区分大小写

### 2. 搜索 Skills

通过关键词搜索 skills：

```bash
openskills market search <keyword>
```

搜索范围包括：技能名称、描述、标签

### 3. 安装 Skills

#### 方法 1：通过 Skill 名称安装

如果知道 skill 名称，直接使用：

```bash
openskills install <skill-name>
```

系统会：
- 在 market 中查找该 skill
- 如果找到唯一 skill，直接安装
- 如果找到多个同名 skill，显示选项让你选择

#### 方法 2：通过 URL 安装

仍然支持原有的安装方式：

```bash
openskills install https://github.com/owner/repo
openskills install https://github.com/owner/repo/skill-path
openskills install git@github.com:owner/repo.git
```

**重要提示**: Git仓库URL必须是完整的。不支持 `owner/repo` 或 `github.com/owner/repo` 这样的简写格式。

## 文件结构

```
python-openskills/
├── market_sources.yaml           # Market 源配置（维护者编辑）
├── marketskills/                  # Market 数据目录
│   ├── owner_repo1.json          # 仓库 1 的 skills
│   └── owner_repo2.json          # 仓库 2 的 skills
├── scripts/
│   └── collect_market_skills.py  # 收集脚本（维护者使用）
└── openskills/
    ├── utils/
    │   └── market.py            # Market 数据管理
    └── commands/
        └── market.py             # Market 命令
```

## 注意事项

1. **Market 数据更新**：维护者需要在仓库更新后重新运行收集脚本
2. **同名 Skills**：当多个仓库中有同名 skill 时，安装时会显示选项让用户选择
3. **Git 要求**：收集脚本需要系统安装 git 命令
4. **临时文件**：收集过程中会创建临时目录，脚本会自动清理

## 示例

### 维护者操作

```bash
# 1. 编辑 market_sources.yaml，添加仓库
vim market_sources.yaml

# 2. 运行收集脚本
python scripts/collect_market_skills.py

# 输出示例：
# ============================================================
# Market Skills Collector
# ============================================================
#
# Found 2 source(s) to process
#
# 📦 Collecting from: owner/repo1
#   Found 3 skill(s):
#     - skill-a (root)
#     - skill-b (at 'skills/skill-b')
#     - skill-c (at 'skills/skill-c')
#   ✓ Saved 3 skill(s) to owner_repo1.json
#
# ============================================================
# Collection complete: 2/2 source(s) processed
# Market skills saved to: marketskills/
# ============================================================
```

### 使用者操作

```bash
# 1. 查看所有可用的 skills
openskills market list

# 2. 搜索特定的 skill
openskills market search pdf

# 3. 安装 skill
openskills install pdf-reader

# 4. 如果有同名 skill，会显示选项：
# Found multiple skills named 'pdf-reader':
#
# 1. pdf-reader
#    Source: owner/repo1
#    Description: A skill for reading PDF files
#    Author: Author1
#
# 2. pdf-reader
#    Source: owner/repo2
#    Description: Another PDF reading skill
#    Author: Author2
#
# Select which skill to install [1-2]: 1
```

## 故障排除

### 收集脚本失败

- 确保系统已安装 git
- 检查仓库 URL 是否正确
- 检查网络连接

### 找不到 Skill

- 运行 `openskills market list` 确认 skill 是否在 market 中
- 检查 skill 名称拼写
- 尝试使用搜索功能

### 安装失败

- 确保有写入权限
- 检查磁盘空间
- 查看错误信息获取更多详情