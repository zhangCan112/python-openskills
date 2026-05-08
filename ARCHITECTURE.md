# OpenSkills v2 架构文档

本文档详细介绍 OpenSkills v2 每个模块和脚本的功能、工作原理和相互关系。

## 整体架构

```
用户输入 (CLI)
     │
     ▼
  cli.py  ← Click 命令解析
     │
     ├── list     → finder.py (扫描目录) → 输出列表
     ├── install  → installer.py → market.py / git clone / 本地复制
     ├── update   → updater.py → 读取 metadata → 重新安装
     ├── remove   → remover.py → 删除目录
     ├── manage   → remover.py → 交互式选择 → 删除目录
     └── market   → market.py → 读取 JSON 数据 → 终端/HTML 展示
```

所有模块都依赖以下基础层：

```
models.py      数据类型定义
dirs.py        目录路径管理
yaml_utils.py  YAML frontmatter 解析
metadata.py    安装元数据读写
config.py      配置文件加载
```

---

## 核心模块详解

### `models.py` (43 行) — 数据类型定义

定义了系统中所有核心数据结构：

| 类型 | 用途 |
|------|------|
| `SkillLocation` | 枚举：`PROJECT`（项目级）/ `GLOBAL`（全局） |
| `SkillSourceType` | 枚举：`GIT`（从 git 仓库安装）/ `LOCAL`（从本地路径安装） |
| `Skill` | 已安装的 skill 信息：名称、描述、位置、路径 |
| `SkillLocationInfo` | skill 的具体文件位置：SKILL.md 路径、base 目录、来源目录 |
| `SkillSourceMetadata` | 安装来源元数据：原始 source、来源类型、repo URL、子路径、本地路径、安装时间 |
| `InstallOptions` | 安装选项：是否全局安装、是否跳过交互确认 |

**工作原理：** 纯数据定义模块，无逻辑。所有其他模块通过 import 使用这些类型。`SkillLocation` 和 `SkillSourceType` 继承自 `str` 和 `Enum`，可以同时作为字符串和枚举使用。

---

### `dirs.py` (30 行) — 目录路径管理

管理所有 skill 相关的目录路径。

**三个函数：**

1. **`get_skills_dir(global_install=False)`** — 获取 skill 安装目标目录
   - 项目级：`./.claude/skills/`
   - 全局级：`~/.claude/skills/`

2. **`get_search_dirs()`** — 返回 skill 搜索目录列表（按优先级排序）
   ```
   1. ./.agent/skills       （项目级通用）
   2. ./.claude/skills      （项目级 Claude）
   3. ~/.agent/skills       （全局通用）
   4. ~/.claude/skills      （全局 Claude）
   ```
   高优先级的目录中的 skill 会覆盖低优先级中的同名 skill。

3. **`get_cache_dir()`** — 获取 git 仓库缓存目录
   - 路径：`~/.openskills/cache/`
   - 自动创建目录（如果不存在）

**工作原理：** 使用 `os.path` 和 `pathlib.Path` 拼接路径。`os.getcwd()` 用于判断项目级路径，`Path.home()` 用于全局路径。

---

### `yaml_utils.py` (12 行) — YAML frontmatter 解析

解析 SKILL.md 文件中的 YAML frontmatter（开头 `---` 包围的元数据块）。

**两个函数：**

1. **`extract_yaml_field(content, field)`** — 从文本中提取指定 YAML 字段值
   - 使用正则 `^field:\s*(.+?)$` 匹配（多行模式）
   - 返回字段值（去除首尾空格），未找到则返回空字符串

2. **`has_valid_frontmatter(content)`** — 检查内容是否以 `---` 开头
   - 用于验证 SKILL.md 文件是否格式正确

**SKILL.md 文件格式示例：**
```markdown
---
name: my-skill
description: A useful skill
---

# My Skill

Skill content here...
```

---

### `metadata.py` (39 行) — 安装元数据读写

管理 `.openskills.json` 文件，记录每个 skill 的安装来源信息。

**两个函数：**

1. **`read_skill_metadata(skill_dir)`** — 读取元数据
   - 读取 `skill_dir/.openskills.json`
   - 解析 JSON 并构建 `SkillSourceMetadata` 对象
   - 文件不存在或格式错误时返回 `None`

2. **`write_skill_metadata(skill_dir, metadata)`** — 写入元数据
   - 将 `SkillSourceMetadata` 序列化为 JSON
   - 自动补充 `installed_at` 时间戳（ISO 格式）
   - 写入 `skill_dir/.openskills.json`

**元数据文件示例：**
```json
{
  "source": "https://github.com/anthropics/skills/skills/pdf",
  "source_type": "git",
  "repo_url": "https://github.com/anthropics/skills",
  "subpath": "skills/pdf",
  "local_path": null,
  "installed_at": "2026-05-07T23:41:00.123456"
}
```

**用途：** `updater.py` 读取这些元数据来知道从哪里重新拉取 skill 的最新版本。

---

### `config.py` (44 行) — 配置文件加载

加载 `market_sources.yaml` 配置文件，用于指定市场 skill 的数据源。

**两个函数：**

1. **`get_config_file_path()`** — 查找配置文件路径
   - 搜索顺序：当前目录 → 上级目录（最多 5 层）→ 用户主目录
   - 找到则返回路径，未找到返回 `None`

2. **`load_config()`** — 加载配置
   - 读取 YAML 文件并返回字典
   - 未找到配置文件时返回默认值 `{'sources': []}`

**注意：** 这个模块主要被 `scripts/collect_market_skills.py`（开发脚本）使用，CLI 本身不直接调用它。

---

### `finder.py` (78 行) — Skill 发现引擎

在所有搜索目录中扫描并发现已安装的 skill。

**四个函数：**

1. **`normalize_skill_names(skill_names)`** — 标准化 skill 名称输入
   - 字符串 → 列表（支持逗号分隔）
   - 列表 → 直接返回
   - 用途：让 CLI 的 `update` 命令同时支持空格和逗号分隔的名称

2. **`is_directory_or_symlink_to_directory(entry, parent_dir)`** — 检查目录入口是否为目录（包括符号链接指向的目录）

3. **`find_all_skills()`** — 发现所有已安装的 skill
   - 调用 `get_search_dirs()` 获取搜索目录列表
   - 遍历每个目录，使用 `os.scandir()` 高效扫描
   - 对每个子目录检查是否包含 `SKILL.md` 文件
   - 读取 SKILL.md 的 YAML frontmatter 提取 `description`
   - 通过 `seen` 集合按名称去重（高优先级目录优先）
   - 返回 `list[Skill]`

4. **`find_skill(skill_name)`** — 按名称查找单个 skill
   - 按搜索目录优先级顺序查找
   - 返回 `SkillLocationInfo`（包含路径信息）或 `None`

**工作原理：**
```
搜索目录列表:
  ./.agent/skills/  ──→ 扫描子目录 ──→ 检查 SKILL.md ──→ 加入结果
  ./.claude/skills/ ──→ 扫描子目录 ──→ 检查 SKILL.md ──→ 去重后加入结果
  ~/.agent/skills/  ──→ ...
  ~/.claude/skills/ ──→ ...
```

---

### `installer.py` (569 行) — 安装逻辑

整个系统最复杂的模块，负责从 git 仓库、本地路径或市场名称安装 skill。

#### 常量

**`ANTHROPIC_MARKETPLACE_SKILLS`** — Anthropic 官方市场 skill 名称列表。全局安装时如果 skill 名称匹配此列表，会发出冲突警告。

#### 验证函数

| 函数 | 作用 |
|------|------|
| `is_local_path(source)` | 判断来源是否为本地路径（`/`、`./`、`../`、`~/` 开头） |
| `is_git_url(source)` | 判断来源是否为 git URL（`git@`、`http://`、`https://`、`.git` 结尾） |
| `is_path_inside(target_path, target_dir)` | 安全检查：确保目标路径在目标目录内（防止路径遍历攻击） |
| `expand_path(source)` | 展开 `~` 为用户主目录，转换为绝对路径 |
| `warn_if_conflict(skill_name, target_path, is_project, skip_prompt)` | 检查覆盖冲突和市场冲突，交互确认 |

#### 缓存管理

Git 仓库使用 SHA256 哈希键的本地缓存系统：

| 函数 | 作用 |
|------|------|
| `get_cache_key(repo_url)` | 对 repo URL 做 SHA256 哈希，取前 16 位作为缓存键 |
| `clone_to_cache(repo_url, cache_path)` | `git clone --depth 1` 浅克隆到缓存目录 |
| `get_cached_repo(repo_url)` | 获取缓存仓库：有缓存则 `git pull` 更新，否则克隆 |

缓存位置：`~/.openskills/cache/<sha256-hash>/`

#### 交互选择

**`prompt_for_selection(message, choices)`** — 交互式多选
- 优先使用 `questionary` 库的 checkbox 组件
- `questionary` 不可用时回退到简单的数字输入方式

#### 核心安装流程

**`install_skill(source, options)`** — 安装入口函数，决策流程：

```
输入 source
  │
  ├─ 不是 URL 也不是本地路径？
  │   └─ 尝试 market 查找 → try_install_from_market()
  │       └─ 找到 → 递归调用 install_skill(source.url)
  │
  ├─ 是本地路径？
  │   └─ install_from_local() → 复制文件
  │
  └─ 是 git URL？
      └─ _install_from_git()
          ├─ 解析 URL（分离 repo URL 和子路径）
          ├─ get_cached_repo()（获取或克隆缓存）
          ├─ 有子路径 → _install_from_subpath()（安装单个 skill）
          └─ 无子路径 → install_from_repo()（扫描仓库中所有 skill）
```

**`find_skills_in_repo(repo_dir)`** — 递归扫描仓库中所有包含 `SKILL.md` 的子目录

**`install_from_repo(repo_dir, target_dir, ...)`** — 从仓库安装多个 skill
- 扫描仓库找到所有 skill
- 如果有多个 skill 且非 `-y` 模式，弹出交互选择
- 逐个复制到目标目录并写入元数据

**`install_from_local(local_path, target_dir, ...)`** — 从本地路径安装
- 如果路径直接包含 `SKILL.md`，作为单个 skill 安装
- 否则作为包含多个 skill 的目录处理（委托给 `install_from_repo`）

**`try_install_from_market(skill_name, options, install_func)`** — 从市场安装
- 在市场数据中按名称查找
- 唯一匹配 → 直接安装
- 多个匹配 → 让用户选择

---

### `updater.py` (180 行) — 更新逻辑

根据安装时记录的元数据，从原始来源重新安装 skill 以获取最新版本。

**核心函数：**

1. **`update_skills(skill_names)`** — 更新入口
   - 没有指定名称 → 更新所有已安装 skill
   - 指定名称 → 只更新指定的
   - 对每个 skill 读取 `.openskills.json` 元数据
   - 根据来源类型（git/local）调用对应的更新函数
   - 分类汇总错误（缺少元数据、源不存在、克隆失败等）

2. **`_update_skill_from_git(target_path, metadata, skill_name)`** — 从 git 更新
   - 在临时目录中 `git clone --depth 1`
   - 根据 `subpath` 找到 skill 源目录
   - 删除旧 skill 目录，复制新内容
   - 重新写入元数据

3. **`_update_skill_from_local(target_path, metadata, skill_name)`** — 从本地路径更新
   - 检查原始本地路径是否仍存在
   - 复制最新内容覆盖

4. **`_update_skill_from_dir(target_path, source_dir)`** — 通用更新操作
   - 安全检查（路径遍历防护）
   - `shutil.rmtree` 删除旧目录 + `shutil.copytree` 复制新内容

**错误分类：**

| 类别 | 含义 |
|------|------|
| `missing_metadata` | skill 没有 `.openskills.json`（手动放置的 skill） |
| `missing_local_source` | 本地源路径已不存在 |
| `missing_local_skill_file` | 本地源路径中 SKILL.md 已丢失 |
| `missing_repo_url` | git 类型但缺少 repo URL |
| `missing_repo_skill_file` | 仓库中指定路径下找不到 SKILL.md |
| `clone_failures` | git clone 失败 |

---

### `remover.py` (84 行) — 删除与交互管理

提供单个删除和批量交互管理两种删除方式。

**三个函数：**

1. **`remove_skill(skill_name)`** — 删除单个 skill
   - 调用 `find_skill()` 查找位置
   - 未找到 → 输出错误并退出
   - 找到 → `shutil.rmtree()` 删除整个目录
   - 显示删除结果（名称、位置、来源目录）

2. **`manage_skills()`** — 交互式批量管理
   - 列出所有已安装 skill（项目级在前）
   - 使用 questionary checkbox 让用户勾选要删除的 skill
   - 批量删除选中的 skill
   - 支持 Ctrl+C 取消

3. **`_prompt_for_selection(message, choices)`** — 交互选择组件
   - 与 `installer.py` 中的同名函数逻辑相同
   - 优先 questionary，回退到数字输入

---

### `market.py` (712 行) — 市场数据与展示

包含市场 skill 的数据模型、加载、搜索、终端展示和 HTML 页面生成。

#### 数据模型

**`MarketSkill` 类** — 市场中的 skill 条目

| 属性 | 说明 |
|------|------|
| `name` | skill 名称 |
| `description` | 描述 |
| `repo` | 所属 git 仓库 URL |
| `branch` | 分支名 |
| `subpath` | 在仓库中的子路径 |
| `version` | 版本号 |
| `author` | 作者 |

`source` 属性：自动拼接 `repo/subpath` 作为安装来源字符串。

#### 数据加载

**`load_market_skills()`** — 从 `openskills/data/marketskills/*.json` 加载所有市场 skill
- 遍历 JSON 文件，解析为 `MarketSkill` 对象列表
- 每个 JSON 文件对应一个 git 仓库，包含该仓库下所有 skill 的元数据

**`find_skill_by_name(name)`** — 按名称精确查找（不区分大小写）

**`search_skills(keyword)`** — 按关键词搜索
- 搜索范围：名称、描述
- 不区分大小写

#### 命令处理

**`market_list(html)`** — 列表命令处理
- `--html` 模式：生成 HTML 页面并在浏览器中打开
- 终端模式：格式化输出到终端

**`market_search(keyword)`** — 搜索命令处理
- 调用 `search_skills()` 查找
- 高亮匹配的关键词

#### 终端展示

**`_display_terminal_output(skills, keyword)`** — 格式化终端输出
- 按名称分组（同名 skill 可能来自不同仓库）
- 显示描述、来源、作者、版本
- 如果提供了关键词，在描述中高亮匹配部分

#### HTML 生成

**`generate_market_html(skills)`** — 生成交互式 HTML 页面
- 包含搜索框和标签过滤功能
- skill 按仓库分组展示为卡片
- 每个卡片显示名称、描述、来源
- "Copy Install Command" 按钮（复制 `openskills install <source>`）
- 仓库分组可折叠/展开
- 生成到临时文件并在浏览器中打开

---

### `cli.py` (126 行) — CLI 命令定义

使用 Click 框架定义所有 CLI 命令，是用户与系统交互的入口。

**命令映射：**

| CLI 命令 | 处理函数 | 所在模块 |
|----------|----------|----------|
| `openskills list` | `_list_skills()`（内联） | cli.py |
| `openskills install` | `install_skill()` | installer.py |
| `openskills update` | `update_skills()` | updater.py |
| `openskills remove` | `remove_skill()` | remover.py |
| `openskills rm` | `remove_skill()` | remover.py |
| `openskills manage` | `manage_skills()` | remover.py |
| `openskills market list` | `market_list()` | market.py |
| `openskills market search` | `market_search()` | market.py |

**`list` 命令** 直接在 cli.py 中实现（逻辑简单）：
- 调用 `find_all_skills()` 获取列表
- 按 project/global 分组，每组内按名称排序
- 显示名称、位置标签、描述
- 底部显示统计摘要

**`--version`** 使用 `importlib.metadata.version()` 获取版本号（pip 安装后可正确获取）。

### `__main__.py` (4 行) — 模块入口

支持 `python -m openskills` 方式运行。简单地导入并调用 `cli()`。

---

## 开发脚本

### `scripts/collect_market_skills.py` — 市场数据收集

**功能：** 从 `market_sources.yaml` 中配置的 GitHub 仓库收集 skill 元数据，保存为 JSON 文件。

**工作流程：**
1. 读取 `market_sources.yaml` 配置
2. 对每个配置的仓库：
   - 克隆到临时目录
   - 扫描指定路径（如 `skills/`）下的所有 SKILL.md 文件
    - 提取 YAML frontmatter 中的元数据（name、description 等）
3. 将收集到的数据保存到 `openskills/data/marketskills/` 目录下的 JSON 文件

**输出文件格式：**
```json
{
  "repo": "https://github.com/anthropics/skills",
  "branch": "main",
  "skills": [
    {
      "name": "pdf",
      "description": "...",
      "subpath": "skills/pdf"
    }
  ]
}
```

### `market_sources.yaml` — 市场数据源配置

```yaml
sources:
  - repo: https://github.com/anthropics/skills
    branch: main
    skills_path: skills/
  - repo: https://github.com/zhangCan112/python-openskills
    branch: main
    skills_path: skills/
```

| 字段 | 说明 |
|------|------|
| `repo` | Git 仓库 URL |
| `branch` | 要克隆的分支 |
| `skills_path` | 仓库中 skill 所在的目录路径 |

---

## 数据流

### 安装流程

```
用户: openskills install pdf
  │
  ├─ cli.py 解析参数，构建 InstallOptions
  │
  ├─ installer.py:install_skill("pdf", options)
  │   ├─ is_local_path?  No
  │   ├─ is_git_url?     No
  │   └─ try_install_from_market("pdf")
  │       ├─ market.py:find_skill_by_name("pdf")
  │       │   └─ 从 JSON 文件中找到 → MarketSkill(source="https://github.com/anthropics/skills/skills/pdf")
  │       └─ 递归调用 install_skill("https://github.com/anthropics/skills/skills/pdf")
  │           ├─ is_git_url? Yes
  │           ├─ 解析 URL → repo="https://github.com/anthropics/skills", subpath="skills/pdf"
  │           ├─ get_cached_repo() → 克隆/更新缓存
  │           ├─ _install_from_subpath("skills/pdf", ...)
  │           │   ├─ 验证 SKILL.md 存在且格式正确
  │           │   ├─ warn_if_conflict() → 检查冲突
  │           │   ├─ shutil.copytree() → 复制到 .claude/skills/pdf/
  │           │   └─ write_skill_metadata() → 写入 .openskills.json
  │           └─ 输出安装结果
  │
  └─ .claude/skills/pdf/
      ├── SKILL.md
      ├── scripts/
      ├── references/
      └── .openskills.json   ← 记录安装来源
```

### 更新流程

```
用户: openskills update pdf
  │
  ├─ cli.py 调用 updater.py:update_skills(["pdf"])
  │
  ├─ finder.py:find_all_skills() → 找到 pdf skill
  │
  ├─ metadata.py:read_skill_metadata() → 读取 .openskills.json
  │   └─ {source_type: "git", repo_url: "...", subpath: "skills/pdf"}
  │
  ├─ _update_skill_from_git()
  │   ├─ git clone 到临时目录
  │   ├─ 定位 skills/pdf/ 子目录
  │   ├─ _update_skill_from_dir(): 删除旧目录 + 复制新内容
  │   └─ write_skill_metadata(): 更新元数据
  │
  └─ 输出更新结果
```

---

## 文件布局

```
python-openskills/
├── openskills/                         # 主包
│   ├── __init__.py                     # v2.0.0
│   ├── __main__.py                     # python -m 入口
│   ├── cli.py                          # CLI 命令定义 (126 行)
│   ├── models.py                       # 数据类型 (43 行)
│   ├── finder.py                       # Skill 发现 (78 行)
│   ├── installer.py                    # 安装逻辑 (569 行)
│   ├── updater.py                      # 更新逻辑 (180 行)
│   ├── remover.py                      # 删除/管理 (84 行)
│   ├── market.py                       # 市场数据+展示 (712 行)
│   ├── metadata.py                     # 元数据读写 (39 行)
│   ├── dirs.py                         # 目录路径 (30 行)
│   ├── config.py                       # 配置加载 (44 行)
│   ├── yaml_utils.py                   # YAML 解析 (12 行)
│   └── data/
│       └── marketskills/               # 市场数据缓存
│           ├── github.com_anthropics_skills.json
│           └── github.com_zhangCan112_python-openskills.json
├── scripts/
│   └── collect_market_skills.py        # 市场数据收集脚本
├── skills/
│   └── skill-creator/                  # 内置 skill（随项目分发）
├── market_sources.yaml                 # 市场数据源配置
├── pyproject.toml                      # 现代打包配置
├── setup.py                            # 传统打包配置
├── requirements.txt                    # 依赖列表
├── test_cli.py                         # 导入/CLI 冒烟测试
└── README.md                           # 项目说明
```
