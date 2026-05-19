# Codex Skills

这个仓库用于保存可复用的 Codex skills。当前包含一个技能：

- [`seo-demand-research`](./seo-demand-research)：海外 SEO 需求调研、关键词找词、SERP 竞争判断、竞品分析和建站前 SOP。

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

## 当前 Skill：seo-demand-research

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
```

安装后路径应类似：

```text
~/.codex/skills/seo-demand-research/SKILL.md
```

如果你已经在当前机器上创建过这个 skill，可以用下面命令覆盖更新：

```bash
rm -rf ~/.codex/skills/seo-demand-research
cp -R seo-demand-research ~/.codex/skills/
```

## 如何调用

在 Codex 新对话里可以直接说：

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

