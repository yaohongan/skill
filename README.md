# 🧰 Hongan Skills

#### 我把自己反复使用、真正跑通的 AI 工作流，整理成可以直接安装的 Skills

这里不是提示词收藏夹，而是一套面向真实业务的 Agent 工作流：从海外 SEO 需求验证，到拼多多月度利润核算，每个 Skill 都有明确的输入、步骤、校验规则和交付物。

我的目标很简单：**把一次次重复解释的经验，变成 Agent 可以稳定执行的能力。**

这些 Skills 主要为 Codex 构建，也采用通用的 `SKILL.md` 结构，便于迁移到其他支持 Agent Skills 的工具中。

---

## 📋 Skill 目录

| Skill | 一句话说明 | 适合谁 |
| --- | --- | --- |
| 🔎 [`seo-demand-research`](./seo-demand-research) | 从关键词、真实 SERP 和竞品出发，找到值得做的海外 SEO 产品机会 | AI 工具站、SaaS、内容站创业者 |
| 📊 [`pdd-monthly-profit`](./pdd-monthly-profit) | 读取投流截图、成本表和订单文件，核算拼多多月度盈亏并生成客户版 Excel | 电商运营、财务复盘、代运营团队 |

> 我只会把经过实际使用、能够节省时间的工作流放进这里。项目会持续更新。

---

## 📦 安装方式

最省事的方式，是把对应 Skill 的 GitHub 地址发给 Codex：

```text
帮我安装这个 Skill：
https://github.com/yaohongan/skill/tree/main/<skill-name>
```

把 `<skill-name>` 替换成 `seo-demand-research` 或 `pdd-monthly-profit`。

也可以手动复制到本地 Codex Skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R <skill-name> ~/.codex/skills/
```

一个标准 Skill 通常包含：

```text
skill-name/
├── SKILL.md              # 触发条件与主工作流
├── agents/
│   └── openai.yaml       # Codex 中的名称、简介与默认提示词
└── references/           # SOP、规则、案例与输出模板
```

---

## ✨ Skills

### 🔎 SEO Demand Research｜海外 SEO 需求研究

> “有搜索量，不等于有机会；真正要找的是需求明确、竞争可打、产品能承接的关键词。”

这个 Skill 用来把一个模糊方向，逐步验证成可执行的 SEO 产品机会。它不会只看关键词工具给出的分数，而会优先检查真实 Google SERP、竞品产品形态和用户搜索意图。

它能帮你：

- 围绕一个方向拓展关键词与需求簇
- 判断搜索意图、竞争强度和商业价值
- 结合 Ahrefs、Semrush、Similarweb、Google Trends 等数据交叉验证
- 分析竞品定位、功能、定价、流量结构与内容策略
- 输出关键词机会表、MVP 范围、页面地图和建站 SOP
- 在投入开发前识别“看起来有量，实际上不适合做”的伪机会

适合：海外 AI 工具站、SaaS、内容站的选题验证和冷启动。

不适合：只想机械批量生成关键词，而不准备验证 SERP 和真实竞争环境。

触发示例：

```text
使用 seo-demand-research，完整调研「PDF to study tools」这个方向。

使用 seo-demand-research，帮我判断 AI Flashcard Generator 是否适合冷启动。

围绕 AI learning tools，找 20 个低竞争关键词，并推荐最值得做的 5 个。
```

→ 查看 [`SKILL.md`](./seo-demand-research/SKILL.md)

### 📊 PDD Monthly Profit｜拼多多月度利润核算

> “利润核算最怕的不是公式复杂，而是成本漏匹配、退款没排除，最后得到一个看似精确的错误答案。”

这个 Skill 面向拼多多店铺月度经营复盘。它会读取投流截图、商品成本表和订单文件，按统一规则完成清洗、SKU 匹配和利润计算，并生成方便客户或团队核对的中文 Excel。

它能帮你：

- 从投流截图识别核算日期与推广总花费
- 跨多个成本表工作表匹配订单 SKU
- 排除退款、取消、交易关闭和售后处理中订单
- 按商品数量计算总成本
- 按“商家实收 − 商品成本 − 推广花费”核算最终盈亏
- 成本缺失时停止正式结算，并给出未匹配 SKU 清单
- 输出客户汇报、SKU 汇总、订单明细、成本标准、剔除订单等核对表

适合：电商运营月报、代运营客户汇报、店铺利润复盘。

不适合：缺少成本表，或需要按会计准则生成正式财务报表的场景。

触发示例：

```text
使用 pdd-monthly-profit，帮我根据投流截图、成本表和订单文件，
核算 7 月份利润，并生成客户核对版 Excel。
```

→ 查看 [`SKILL.md`](./pdd-monthly-profit/SKILL.md)

---

## ✅ 这个仓库坚持什么

- **真实工作流优先**：先在业务里跑通，再沉淀成 Skill。
- **结果可核对**：关键数据保留来源、计算过程和检查项。
- **缺信息不硬算**：输入不足时明确指出缺口，不制造“精确幻觉”。
- **能直接交付**：不止给分析，还要产出表格、报告或下一步 SOP。
- **持续迭代**：随着实际使用不断补充边界条件和案例。

---

## 🌟 关于我

我是虹安，长期关注 AI Agent、海外工具站与电商业务自动化。

我喜欢做的一件事，是把原本依赖个人经验、需要反复沟通的复杂流程，拆成 Agent 能理解、能执行、也能验证的工作流。这个仓库就是这些实践的公开沉淀。

如果这里的 Skill 对你有帮助，欢迎点一个 ⭐。有问题、使用反馈或改进建议，也欢迎提交 Issue。

Made by [@yaohongan](https://github.com/yaohongan)
