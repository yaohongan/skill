# 拼多多月度利润 Skill 跨平台改造设计

## 目标

让 `pdd-monthly-profit` 使用同一套技能文件和计算代码，在以下环境中工作：

- Windows 与 macOS
- OpenAI Codex
- Anthropic Claude Code
- 腾讯 WorkBuddy / CodeBuddy

三个 Agent 的核算口径和客户核对版 Excel 必须一致。

## 兼容基础

技能继续采用 Agent Skills 通用结构：

```text
pdd-monthly-profit/
├── SKILL.md
├── scripts/
├── references/
└── agents/openai.yaml
```

`SKILL.md` 的 YAML 仅使用 `name` 和 `description`。`agents/openai.yaml` 是 Codex 可选界面元数据；Claude Code 和 WorkBuddy 可以忽略，不作为运行依赖。

## 运行依赖

统一要求 Python 3.10 或更高版本，并通过 `requirements.txt` 安装：

- `pandas`
- `openpyxl`

不再要求 Codex 捆绑的 Node.js、`@oai/artifact-tool`、Windows Junction 或 PowerShell 专属流程。

## 组件设计

### 数据核算

保留 `scripts/analyze_profit.py`，继续负责：

- 读取 CSV、XLS 和 XLSX
- 日期过滤
- 订单状态与售后状态过滤
- 商品 ID 与成本匹配
- 商品数量成本计算
- 未匹配暂算与成本冲突检查
- 输出可追溯 JSON

### Excel 报告

使用 `scripts/build_report.py` 替代 Node.js 报告脚本。它读取分析 JSON，生成与现有版本等价的六张中文工作表：

- 核算说明
- 商品盈亏汇总
- 有效订单明细
- 成本映射
- 未匹配商品
- 排除订单

投流金额保持黄色可编辑单元格，净利润和逐单毛利保留 Excel 公式，商品 ID 完整显示。

### 环境检查

新增 `scripts/check_environment.py`，检查 Python 版本和依赖。缺少依赖时输出 Windows/macOS 都可使用的安装命令，不静默修改用户环境。

## Agent 安装与调用

- Codex 用户级目录：`~/.codex/skills/pdd-monthly-profit/`
- Claude Code 用户级目录：`~/.claude/skills/pdd-monthly-profit/`
- WorkBuddy / CodeBuddy：优先使用产品设置页“导入 Skill”；项目级可放入产品识别的 skills 目录。

技能正文不写死 Agent 专属工具名。Agent 需要读取截图、访问文件和运行 Python；权限不足时先向用户申请。

## 命令兼容

技能先检测可用解释器：

1. 尝试 `python3`。
2. 尝试 `python`。
3. 两者均不存在时提示安装 Python 3.10+。

所有 Python 命令使用参数数组或正确引用路径，支持包含中文和空格的 Windows/macOS 路径。

## 错误处理

- 缺少 Python 或依赖：停止并给出安装命令。
- 截图日期或投流金额不清楚：请求用户确认。
- 成本冲突：停止最终核算并列出冲突商品 ID。
- 未匹配成本：继续已匹配部分，结果明确标为“暂算”。
- Excel 生成失败：保留分析 JSON，报告失败原因，不宣称已交付。

## 测试与验收

本地测试覆盖：

- 日期边界、数量成本和状态排除
- 未匹配暂算
- 重复成本冲突
- CSV/XLSX 输入
- Excel 工作表、公式、黄色投流格和完整商品 ID
- 技能中文说明与跨平台命令
- 代码中不存在用户目录、盘符或 Codex 专属报告依赖

GitHub Actions 使用 `windows-latest` 和 `macos-latest`，至少覆盖 Python 3.10 与当前稳定 Python。两个系统全部通过后，才在 README 中标记为已验证。

## 非目标

- 不实现拼多多后台自动登录或下载。
- 不在技能中保存真实订单、成本、截图或客户名称。
- 不为三个 Agent 维护不同的计算脚本。
- 不保证未授权终端或文件访问的 Agent 能执行本地核算。
