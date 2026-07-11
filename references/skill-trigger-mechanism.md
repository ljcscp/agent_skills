# 技能触发机制说明

## 概述

Hermes 技能可以通过以下方式被加载到会话中。不同环境（桌面版、CLI、TUI）支持的机制不同。

---

## 方案 A：Description 关键词匹配（所有环境）

Hermes 的 system prompt 中有一个 `<available_skills>` 列表，包含所有已安装技能的 name + description。系统提示词指示模型：

> "Before replying, scan the skills below. If a skill matches or is even partially relevant to your task, you MUST load it with skill_view(name) and follow its instructions."

因此，**模型的主动判断**是触发技能的第一道门槛。为了让模型准确命中，description 必须包含触发关键词（尤其是中文关键词）。

### 优化要点
- description 应包含中文触发词：写代码、做报告、做PPT、制定计划、决策建议、学习路径等
- 也应包含不触发的例外说明：facts, general knowledge, simple calculations
- 中英双语比纯英文更容易让中文场景的模型命中

### 局限性
- 依赖模型自主判断，不同模型（deepseek, claude, gpt）行为不同
- 如果模型不主动调用 skill_view()，技能不会生效

---

## 方案 B：手动加载 `/skill <name>`

在会话中手动输入 `/skill situation-goal-solver` 加载。

- 所有环境（CLI、TUI、桌面版）都支持
- 即时生效，不需要重启
- 适合临时需要某个技能的场景

---

## 方案 C：CLI 预加载 `hermes -s <skill>`

启动 CLI 时通过 `-s` / `--skills` 参数预加载：

```bash
hermes -s situation-goal-solver
# 或加载多个
hermes -s situation-goal-solver -s writing-plans
```

- 技能会被注入到 system prompt 的开头，**整个会话始终有效**
- 模型不需要主动调用 skill_view()，技能直接生效
- 仅限 CLI 启动方式

---

## 方案 D：TUI/桌面版预加载 `HERMES_TUI_SKILLS`（推荐）

TUI 和桌面版 Hermes 通过环境变量预加载技能：

### 配置方法
在 `~/.hermes/.env`（即 `C:\Users\<user>\AppData\Local\hermes\.env`）中添加：

```
HERMES_TUI_SKILLS=situation-goal-solver
```

### 原理
1. `tui_gateway/server.py` 中的 `_parse_tui_skills_env()` 读取 `HERMES_TUI_SKILLS` 环境变量
2. 技能通过 `build_preloaded_skills_prompt()` 注入 system prompt
3. 整个会话始终生效，无需模型自主判断

### 生效条件
- **需要重启 Hermes 桌面版**（关闭后重新打开）
- 之后每个新会话都会自动加载该技能

### 验证方法
启动后新建会话，看 AI 是否自动遵循技能规则。如果技能被加载，AI 在回答需要背景的问题时会先问处境和目标。

---

## 方案 E：Context File（AGENTS.md / .cursorrules）

在项目工作目录下放置 `AGENTS.md` 或 `.cursorrules`，写入引用指令：

```
Always load the "situation-goal-solver" skill. Its instructions apply to every response.
```

- 适合项目级强制要求
- 不需要修改 Hermes 配置
- 但需要每个项目目录都放一个文件

---

## 推荐组合

| 场景 | 推荐方案 |
|------|---------|
| CLI 用户 | C（`-s` 参数） |
| 桌面版用户 | **D（`HERMES_TUI_SKILLS`）+ A（description）** |
| 团队共享项目 | E（Context File） |
| 临时使用 | B（`/skill` 命令） |
