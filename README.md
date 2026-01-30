# OpenSkills Python版本

OpenSkills的Python实现 - 通用的AI编码代理技能加载器，用于安装和管理Anthropic SKILL.md格式的技能。

## 安装

```bash
cd python-openskills
pip install -e .
```

## 依赖项

- Python 3.8+
- click >= 8.1.0
- questionary >= 2.0.0

## 使用方法

### 列出已安装的技能

```bash
openskills list
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
```

### 更新技能

```bash
# 更新所有已安装的技能
openskills update

# 更新特定技能
openskills update skill-name skill-two
```

### 同步到AGENTS.md

```bash
# 交互式同步（预选择当前状态）
openskills sync

# 跳过交互，同步所有技能
openskills sync --yes

# 指定输出文件
openskills sync --output CUSTOM.md
```

### 管理技能（交互式删除）

```bash
openskills manage
```

### 删除特定技能

```bash
openskills remove skill-name

# 或使用别名
openskills rm skill-name
```

## 技能目录结构

OpenSkills在以下位置查找技能（按优先级）：

1. `./.agent/skills` - 项目通用（.agent）
2. `~/.agent/skills` - 全局通用（.agent）
3. `./.claude/skills` - 项目Claude
4. `~/.claude/skills` - 全局Claude

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
