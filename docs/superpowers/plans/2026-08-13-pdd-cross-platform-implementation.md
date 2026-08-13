# 拼多多月度盈亏 Skill 跨平台实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `pdd-monthly-profit` 在 Windows 和 macOS 上由 Codex、Claude Code、WorkBuddy 使用同一套 Python 核算与报表代码。

**Architecture:** 保留现有 `profit_core.py` 核算逻辑，使用 `openpyxl` 重写客户版 Excel 生成器，并新增独立环境检查脚本。技能正文只依赖 Agent Skills 通用能力：读取图片和文件、运行 Python，不再绑定 Codex 工具、PowerShell、Node.js 或 Windows Junction。

**Tech Stack:** Python 3.10+、pandas、openpyxl、xlrd、unittest、GitHub Actions

---

### Task 1: 锁定跨平台契约

**Files:**
- Modify: `pdd-monthly-profit/tests/test_report_contract.py`
- Create: `pdd-monthly-profit/tests/test_cross_platform_contract.py`

- [ ] 增加测试，要求 Python 报表生成器、依赖文件、三客户端安装说明和无平台专属运行依赖。
- [ ] 运行测试并确认因缺少实现而失败。

### Task 2: 实现纯 Python 报表与环境检查

**Files:**
- Create: `pdd-monthly-profit/scripts/build_profit_report.py`
- Create: `pdd-monthly-profit/scripts/check_environment.py`
- Create: `pdd-monthly-profit/requirements.txt`
- Delete: `pdd-monthly-profit/scripts/build_profit_report.mjs`

- [ ] 使用 `openpyxl` 生成八张中文工作表、公式、样式和核对项。
- [ ] 增加环境检查，验证 Python 版本与依赖，不自动安装软件。
- [ ] 运行报表契约和完整技能测试。

### Task 3: 改写跨平台技能说明

**Files:**
- Modify: `pdd-monthly-profit/SKILL.md`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-08-06-cross-platform-pdd-profit-skill-design.md`

- [ ] 使用 `python3`/`python` 自动选择规则和与 shell 无关的参数说明。
- [ ] 写明 Codex、Claude Code、WorkBuddy 的安装位置和调用方式。
- [ ] 明确截图读取依赖宿主 Agent 的图片能力，Excel 计算逻辑由同一套 Python 完成。

### Task 4: 多系统持续集成与发布

**Files:**
- Create: `.github/workflows/pdd-monthly-profit.yml`

- [ ] 在 Windows、macOS、Ubuntu 和 Python 3.10/3.13 上运行测试与技能校验。
- [ ] 本地生成并重新读取示例工作簿，确认八张工作表、公式和关键金额。
- [ ] 提交、推送并等待 GitHub Actions 结果。
