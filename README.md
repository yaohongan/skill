# Codex Skills

这个仓库用于保存可复用的 Codex skills。当前包含两个技能：

- [`seo-demand-research`](./seo-demand-research)：海外 SEO 需求调研、关键词找词、SERP 竞争判断、竞品分析和建站前 SOP。
- [`pdd-monthly-profit`](./pdd-monthly-profit)：根据拼多多投流截图、成本表和订单文件核算月度盈亏，并生成中文客户版 Excel。

## 什么是 Skill

Skill 是给 Codex 使用的专用工作流说明。它可以把一套重复流程固化下来，让后续新对话不用重新解释背景。

一个标准 skill 通常包含：

```text
skill-name/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    └── ...
```

其中：

- `SKILL.md`：触发条件和主流程。
- `agents/openai.yaml`：Codex UI 里的显示名称、短描述和默认提示词。
- `references/`：按需加载的详细 SOP、评分表、案例库和输出模板。

## Skill：pdd-monthly-profit

`pdd-monthly-profit` 用于核算拼多多店铺月度盈利或亏损，适合电商运营、财务复盘和客户月报场景。

适用场景：

- 读取投流截图中的核算日期和“总花费（元）”
- 使用订单商品规格匹配成本表全部工作表中的 SKU 名称
- 排除退款、取消、交易关闭和售后处理中订单
- 按“单件总成本 × 商品数量”计算商品总成本
- 按“商家实收 - 商品总成本 - 推广总花费”计算最终盈亏
- 成本缺失时暂停正式核算，并输出去重后的未匹配 SKU 清单
- 生成包含八个中文工作表的客户版 Excel

### 必要输入

1. 拼多多投流数据截图。
2. 商品成本 Excel，支持多工作表。
3. 月度订单 CSV、XLS 或 XLSX 文件。

### 默认输出

1. 盈利或亏损结论及计算拆解。
2. 去重后的未匹配 SKU 清单；全部匹配时显示“无”。
3. 中文客户版 Excel，包含客户汇报、SKU 汇总、订单明细、成本标准、剔除订单、未匹配 SKU、参数与来源、核对检查。

详细核算流程见 [`pdd-monthly-profit/SKILL.md`](./pdd-monthly-profit/SKILL.md)，字段别名和匹配规则见 [`pdd-monthly-profit/references/field-mapping.md`](./pdd-monthly-profit/references/field-mapping.md)。

## Skill：seo-demand-research

`seo-demand-research` 用于把一个粗糙方向变成可执行的 SEO 产品机会。

适用场景：

- 找词
- 挖需求
- 判断关键词是否值得做
- 分析搜索意图
- 看 Google SERP
- 查 Ahrefs / Semrush / Similarweb / Google Trends
- 调研竞品网站
- 输出关键词机会表
- 输出建站前 SOP
- 为海外 AI 工具站、SaaS 站、内容站找冷启动切口

## 安装方式

把本仓库中的技能目录复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R seo-demand-research ~/.codex/skills/
cp -R pdd-monthly-profit ~/.codex/skills/
```

安装后路径应类似：

```text
~/.codex/skills/seo-demand-research/SKILL.md
```

如果你已经在当前机器上创建过这个 skill，可以用下面命令覆盖更新：

```bash
rm -rf ~/.codex/skills/seo-demand-research
cp -R seo-demand-research ~/.codex/skills/

rm -rf ~/.codex/skills/pdd-monthly-profit
cp -R pdd-monthly-profit ~/.codex/skills/
```

## 如何调用

在 Codex 新对话里可以直接说：

```text
使用 pdd-monthly-profit，帮我根据投流截图、成本表和订单文件核算7月份利润，并生成客户核对版 Excel。
```

或者：

```text
使用 seo-demand-research 技能，帮我找一个海外 AI 工具站方向，要求有搜索量、竞争低、能订阅变现。
```

也可以说：

```text
用 SEO Demand Research skill，帮我调研 pdf to flashcards 这个方向还能扩展哪些低竞争关键词。
```

或者：

```text
使用 seo-demand-research，帮我分析这个关键词能不能做：AI Flashcard Generator。
```

## 推荐工作流

### 1. 快速找词

适合早期探索。

```text
使用 seo-demand-research，围绕「AI learning tools」帮我找 20 个低竞争关键词，并给出前 5 个推荐。
```

输出应包括：

- keyword cluster
- 搜索意图
- 初步竞争判断
- 推荐优先级
- 下一步验证动作

### 2. 完整赛道调研

适合决定是否建站。

```text
使用 seo-demand-research，完整调研「PDF to study tools」这个方向。
需要包含 Semrush/Ahrefs/SERP/竞品分析、关键词评分表、推荐切口和建站 SOP。
```

输出应包括：

- 推荐方向
- 关键词机会表
- SERP 竞争分析
- 竞品矩阵
- MVP 功能范围
- SEO 页面地图
- 风险和下一步

### 3. 质疑某个关键词

适合复查误判。

```text
使用 seo-demand-research，重新判断「AI Flashcard Generator」适不适合冷启动。
请重点看 Google SERP、Ahrefs KD、需要多少外链、top competitors。
```

该 skill 会优先检查真实 SERP，而不是只看关键词工具分数。

### 4. 竞品产品体验

适合建站前定义 MVP。

```text
使用 seo-demand-research，帮我体验并分析这 5 个竞品网站。
输出它们的首屏、功能、价格、限制、SEO 页面、弱点，以及我应该复刻/优化什么。
```

## 输出格式

默认输出中文 Markdown。

常见输出包括：

```markdown
# Keyword Opportunity Report

## Recommendation

## Ranked Keywords

| Rank | Keyword | Volume | KD | CPC | Intent | SERP Reality | Score | Decision |
|---:|---|---:|---:|---:|---|---|---:|---|

## Competitor Notes

## MVP Scope

## SEO Page Plan

## Next Actions
```

## 重要判断原则

这个 skill 固化了一个关键经验：

> 不要因为关键词工具显示 KD 不高，就直接认为一个词适合冷启动。必须看真实 Google SERP。

例如之前调研 `AI Flashcard Generator` 时，表面上它是一个商业相关词，但真实 SERP 里有 Revisely、StudyFetch、NoteGPT 等强竞品，且 Ahrefs 显示竞争并不轻。因此最终没有把它作为第一冷启动切口，而是转向更具体的 `pdf to flashcards`、`pdf to anki cards`、`pdf to quizlet` 等长尾方向。

## 文件说明

### 拼多多月度利润核算

- [`SKILL.md`](./pdd-monthly-profit/SKILL.md)：技能触发条件与完整核算流程。
- [`field-mapping.md`](./pdd-monthly-profit/references/field-mapping.md)：订单、成本、状态字段别名与 SKU 匹配边界。
- [`prepare_profit_data.py`](./pdd-monthly-profit/scripts/prepare_profit_data.py)：命令行入口，读取订单和成本表并输出核算数据。
- [`profit_core.py`](./pdd-monthly-profit/scripts/profit_core.py)：订单筛选、SKU 匹配和利润核算核心逻辑。
- [`build_profit_report.mjs`](./pdd-monthly-profit/scripts/build_profit_report.mjs)：生成中文客户版 Excel 和预览图。

### SEO 需求调研

- [`SKILL.md`](./seo-demand-research/SKILL.md)：主技能说明。
- [`research-sop.md`](./seo-demand-research/references/research-sop.md)：完整调研流程。
- [`keyword-scorecard.md`](./seo-demand-research/references/keyword-scorecard.md)：关键词评分表。
- [`tool-playbook.md`](./seo-demand-research/references/tool-playbook.md)：Ahrefs、Semrush、Similarweb、Google Trends 使用说明。
- [`output-templates.md`](./seo-demand-research/references/output-templates.md)：报告和 SOP 输出模板。
- [`case-study-pdf-flashcards.md`](./seo-demand-research/references/case-study-pdf-flashcards.md)：PDF flashcards 项目复盘案例。

## 维护规范

- 更新 skill 后，优先保持 `SKILL.md` 精简。
- 详细流程放进 `references/`。
- 不要把 API key、cookie、账号信息写进 skill。
- 不要把单个项目的私密信息写进 skill。
- 如果某次关键词调研踩了新坑，可以新增到 `references/` 作为案例库。

