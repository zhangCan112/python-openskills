# OpenSkills

一个 Python CLI 工具，用于管理 AI 编码 Agent 的技能（SKILL.md 格式）。覆盖完整生命周期：发现、安装、更新和卸载。

## 安装

```bash
pip install .
# 或从 git 安装
pip install git+https://github.com/zhangCan112/python-openskills
```

需要 Python 3.11+。

## CLI 命令

```
openskills list                          # 列出所有已安装的 skill
openskills install <source>              # 从 git URL / 本地路径 / 市场名称安装
        [--global]                       #   安装到全局目录
        [--yes / -y]                     #   跳过交互确认
openskills update [skill1 skill2 ...]    # 更新 skill（默认：全部）
openskills remove <skill>                # 卸载单个 skill
openskills rm <skill>                    # remove 的别名
openskills manage                        # 交互式批量管理（卸载）
openskills market list                   # 列出市场中的 skill
                    [--html]             #   HTML 格式（在浏览器中打开）
openskills market search <keyword>       # 搜索市场 skill
openskills recommends check [skill]      # 检查推荐依赖安装状态
openskills recommends tree [skill]       # 展示推荐依赖树
openskills recommends install <skill>    # 安装缺失的推荐依赖
openskills recommends add <skill>        # 交互式添加推荐伴生 skill
openskills --version                     # 显示版本
```

### 安装来源

```bash
# 从 git URL（HTTPS 或 SSH）
openskills install https://github.com/owner/repo
openskills install git@github.com:owner/repo.git

# 从 git URL 指定子路径（安装仓库中的特定 skill）
openskills install https://github.com/owner/repo/skills/my-skill

# 从本地路径
openskills install ./local-skill

# 从市场名称（在市场数据库中查找）
openskills install pdf
openskills install skill-creator
```

### 更新

更新时，没有 `.openskills.json` 元数据的 skill 会被列出，并通过交互式提示引导添加来源信息 — 只需粘贴完整的 git URL 或本地路径，系统会自动解析。

```
$ openskills update
...
1 skill(s) have no source metadata. Add sources to enable future updates:

  my-skill at .agents/skills/my-skill
  Add source metadata for 'my-skill'? [Y/n] y
  Source (git URL or local path): https://github.com/owner/repo/skills/my-skill
  Metadata saved for 'my-skill'.
```

更新过程中，如果源目录不包含 `.openskills.json`，本地的配置文件会被保留。如果源目录自带 `.openskills.json`，则以源的版本为准。

### 推荐依赖

Skill 可以通过 `.openskills.json` 中的 `recommends` 字段声明推荐的伴生 skill：

```json
{
  "recommends": [
    {"name": "pdf", "source": "https://github.com/anthropics/skills/skills/pdf"}
  ]
}
```

- `openskills recommends check` — 查看推荐依赖的安装状态（带可点击的源链接）
- `openskills recommends tree` — 展示完整的推荐依赖树
- `openskills recommends install <skill>` — 交互式选择并安装缺失的推荐依赖

执行 `openskills install` 后也会自动检测并提示安装推荐依赖。

## Skill 搜索路径

Skill 按以下优先级顺序发现：

1. `.agents/skills`（项目级）
2. `.claude/skills`（项目级，向后兼容）
3. `~/.agents/skills`（全局级）
4. `~/.claude/skills`（全局级，向后兼容）

默认安装目标是 `.agents/skills/`（项目级）。使用 `--global` 安装到 `~/.agents/skills/`。

## 项目结构

```
openskills/
├── cli.py               # Click CLI 命令组 + 所有命令定义
├── models.py            # 所有数据类型（Skill、SkillSourceMetadata 等）
├── finder.py            # Skill 发现引擎（跨目录扫描）
├── installer.py         # 安装逻辑（git、本地、市场）+ 缓存
├── updater.py           # 更新逻辑 + 交互式来源元数据补全
├── remover.py           # 卸载 + 交互式批量管理
├── recommends.py        # 推荐依赖管理
├── market.py            # 市场数据模型、搜索、终端/HTML 展示
├── metadata.py          # .openskills.json 读写
├── dirs.py              # Skill 目录路径和缓存目录
├── config.py            # market_sources.yaml 加载
├── yaml_utils.py        # YAML frontmatter 解析
└── data/marketskills/   # 市场数据缓存（JSON）
```

## 开发脚本

```
scripts/collect_market_skills.py   # 从配置的 GitHub 仓库收集 skill 元数据
market_sources.yaml                # 市场数据源配置（指定采集哪些仓库的 skill）
```

## 测试

```bash
pip install pytest
pytest tests/ -v
```

共 238 个测试，覆盖所有模块。

## 与 v1 的不兼容变更

- 移除了 `sync`、`compat`、`read` 命令
- 移除了 `--universal` 安装选项
- 移除了 `.cline/skills` 和 `.clinerules/skills` 搜索路径
- 移除了安装脚本（install_to_project.bat/sh、setup_env.bat/sh）
- 默认安装目录从 `.claude/skills` 改为 `.agents/skills`
- 最低 Python 版本提升到 3.11

## 许可证

Apache License 2.0
