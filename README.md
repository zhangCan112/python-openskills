# OpenSkills Python版本

OpenSkills的Python实现 - 通用的AI编码代理技能加载器，用于安装和管理Anthropic SKILL.md格式的技能。

## 安装

本项目提供多种安装方式，您可以根据需要选择：

### 方式1：直接使用（无需安装，推荐快速测试）

不需要任何安装，直接使用 Python 模块运行：

```bash
# 查看帮助
python -m openskills.cli --help

# 列出已安装的技能
python -m openskills.cli list

# 安装技能
python -m openskills.cli install anthropics/skills
```

### 方式2：使用虚拟环境（推荐，隔离环境）

在特定文件夹下创建虚拟环境：

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

使用便捷脚本（自动创建虚拟环境并安装）：

```bash
# Windows
setup_env.bat

# Linux/Mac
bash setup_env.sh
```

### 方式3：全局安装

```bash
pip install -e .
```

安装后可以直接使用 `openskills` 命令。

### 方式4：安装到指定项目（推荐，隔离且便捷）

将OpenSkills安装到任意目标项目中，自动创建虚拟环境并配置，不会影响目标项目的git：

```bash
# Windows
install_to_project.bat C:\path\to\your\project

# Linux/Mac
bash install_to_project.sh /path/to/your/project
```

**脚本会自动完成以下操作：**
1. 在目标项目中创建虚拟环境 `.venv`
2. 安装OpenSkills到虚拟环境
3. 自动将 `.venv` 添加到 `.gitignore`（不会提交到git）
4. 创建便捷启动脚本 `openskills.bat`（Windows）或 `openskills.sh`（Linux/Mac）

**使用方式：**
```bash
# 方式1：激活虚拟环境后使用
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
openskills --help

# 方式2：使用快捷脚本（更方便）
openskills.bat --help  # Windows
./openskills.sh --help  # Linux/Mac
```

## 依赖项

- Python 3.8+
- click >= 8.1.0
- questionary >= 2.0.0

## 使用方法

根据您选择的安装方式，命令格式略有不同：

- **方式1（直接使用）**: 使用 `python -m openskills.cli` 前缀
- **方式2/3（虚拟环境/全局安装）**: 直接使用 `openskills` 命令
- **方式4（安装到项目）**: 激活虚拟环境后使用 `openskills` 命令，或使用快捷脚本

以下示例使用 `openskills` 命令，如果使用方式1，请在命令前加上 `python -m openskills.cli`。

### 列出已安装的技能

```bash
openskills list

# 如果使用方式1，请使用：
python -m openskills.cli list
```

### 安装技能

从GitHub仓库安装：

```bash
# 安装到项目目录（默认）
openskills install anthropics/skills

# 安装到全局目录
openskills install owner/skill --global

# 安装到.agent/skills（用于通用AGENTS.md）
openskills install owner/skill --universal

# 跳过交互式选择，安装所有找到的技能
openskills install owner/skill --yes

# 如果使用方式1，请在命令前加上 python -m openskills.cli
# 例如：python -m openskills.cli install anthropics/skills
```

从本地路径安装：

```bash
openskills install ./local-skill
openskills install ~/my-skills/skill-name
```

从完整Git URL安装：

```bash
openskills install https://github.com/owner/repo.git
openskills install git@github.com:owner/repo.git
```

### 读取技能内容

```bash
# 读取单个技能
openskills read skill-name

# 读取多个技能
openskills read skill-one skill-two

# 使用逗号分隔
openskills read skill-one,skill-two

# 如果使用方式1，请在命令前加上 python -m openskills.cli
```

### 更新技能

```bash
# 更新所有已安装的技能
openskills update

# 更新特定技能
openskills update skill-name skill-two

# 如果使用方式1，请在命令前加上 python -m openskills.cli
```

### 同步到AGENTS.md

```bash
# 交互式同步（预选择当前状态）
openskills sync

# 跳过交互，同步所有技能
openskills sync --yes

# 指定输出文件
openskills sync --output CUSTOM.md

# 如果使用方式1，请在命令前加上 python -m openskills.cli
```

### 管理技能（交互式删除）

```bash
openskills manage

# 如果使用方式1，请在命令前加上 python -m openskills.cli
```

### 删除特定技能

```bash
openskills remove skill-name

# 或使用别名
openskills rm skill-name

# 如果使用方式1，请在命令前加上 python -m openskills.cli
```

## 技能目录结构

OpenSkills在以下位置查找技能（按优先级）：

1. `./.agent/skills` - 项目通用（.agent）
2. `~/.agent/skills` - 全局通用（.agent）
3. `./.claude/skills` - 项目Claude
4. `~/.claude/skills` - 全局Claude

## 快速参考

| 操作 | 虚拟环境/全局安装 | 安装到项目 | 直接运行 |
|------|------------------|------------|----------|
| 查看帮助 | `openskills --help` | `openskills.bat --help`<br>`./openskills.sh --help` | `python -m openskills.cli --help` |
| 列出技能 | `openskills list` | `openskills.bat list`<br>`./openskills.sh list` | `python -m openskills.cli list` |
| 安装技能 | `openskills install <skill>` | `openskills.bat install <skill>`<br>`./openskills.sh install <skill>` | `python -m openskills.cli install <skill>` |
| 读取技能 | `openskills read <skill>` | `openskills.bat read <skill>`<br>`./openskills.sh read <skill>` | `python -m openskills.cli read <skill>` |
| 更新技能 | `openskills update` | `openskills.bat update`<br>`./openskills.sh update` | `python -m openskills.cli update` |
| 同步技能 | `openskills sync` | `openskills.bat sync`<br>`./openskills.sh sync` | `python -m openskills.cli sync` |
| 管理技能 | `openskills manage` | `openskills.bat manage`<br>`./openskills.sh manage` | `python -m openskills.cli manage` |
| 删除技能 | `openskills remove <skill>` | `openskills.bat remove <skill>`<br>`./openskills.sh remove <skill>` | `python -m openskills.cli remove <skill>` |

## 与TypeScript版本的差异

Python版本实现了与TypeScript版本相同的核心功能，但使用不同的技术栈：

- **CLI框架**: 使用Click（Python）替代Commander（TypeScript）
- **交互式提示**: 使用questionary（Python）替代@inquirer/prompts（TypeScript）
- **终端美化**: 使用Click的样式功能替代chalk（TypeScript）

所有命令的参数和行为保持一致，确保无缝迁移。

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行CLI
python -m openskills.cli --help
```

### 项目结构

```
python-openskills/
├── openskills/
│   ├── __init__.py
│   ├── cli.py              # CLI入口
│   ├── types.py            # 类型定义
│   ├── commands/           # 命令模块
│   │   ├── install.py
│   │   ├── list.py
│   │   ├── read.py
│   │   ├── remove.py
│   │   ├── update.py
│   │   ├── sync.py
│   │   └── manage.py
│   └── utils/             # 工具模块
│       ├── dirs.py
│       ├── yaml.py
│       ├── skills.py
│       ├── skill_metadata.py
│       ├── agents_md.py
│       └── marketplace_skills.py
├── requirements.txt
├── setup.py
└── README.md
```

## 许可证

Apache License 2.0

## 贡献

欢迎贡献！请参阅主项目的CONTRIBUTING.md文件。

## 原项目

这是[OpenSkills](https://github.com/numman-ali/openskills)项目的Python实现版本。
