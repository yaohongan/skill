---
name: pdd-monthly-profit
description: Use when the user asks to calculate Pinduoduo monthly profit or loss from an ad-spend screenshot, order CSV/XLS/XLSX, and multi-sheet cost workbook, including 拼多多算账、月度盈亏、扣推广费、匹配SKU、生成客户汇报表.
---

# 拼多多月度盈亏计算

## 核算口径

使用订单实收、单件总成本、商品数量和推广总花费核算月度盈亏。日期、推广费、字段或成本不明确时暂停并询问，不估算正式结果。

默认交付：

1. 盈亏结论与计算拆解。
2. 去重后的未匹配SKU清单；全部匹配时写“无”。
3. 包含八个中文工作表的客户版Excel。

## 必要输入

- 拼多多投流截图，可为一张或多张。
- 商品成本Excel，读取全部工作表。
- 月度订单CSV、XLS或XLSX。
- 可选的店铺名称和核算月份。

## 通用运行要求

本技能遵循Agent Skills通用目录结构，可由Codex、Claude Code和WorkBuddy读取。宿主Agent需要能够读取本地图片和文件，并运行Python命令。

1. 在技能目录中定位 `scripts/` 和 `requirements.txt`。不要假设固定盘符或用户目录。
2. 优先使用 `python3`；不可用时使用 `python`。Windows也可使用 `py -3`。
3. 运行 `scripts/check_environment.py`。如果检查失败，展示其安装命令并先征得用户同意再安装依赖。
4. 所有输出放在本次任务的独立目录，不修改用户源文件。

要求Python 3.10+，依赖见 `requirements.txt`。不依赖Node.js、专属电子表格工具或特定操作系统命令。

## 工作流程

### 1. 确认日期与推广费

读取投流截图：

- 优先采用截图中明确的起止日期。
- 只采用“总花费（元）”，不得采用“成交花费（元）”。
- 截图以“万”展示时乘以10000，并记录来源说明。
- 日期或总花费看不清时先请用户确认。

开始计算前，用一句话复述核算日期和推广总花费。

### 2. 检查环境

从技能根目录运行：

```text
<python> scripts/check_environment.py
```

缺少依赖时，在技能根目录运行：

```text
<python> -m pip install -r requirements.txt
```

`<python>` 是当前系统可用的 `python3`、`python` 或 `py -3`。包含中文或空格的路径必须作为单个参数传入。

### 3. 计算订单与成本

运行：

```text
<python> scripts/prepare_profit_data.py --orders <订单文件> --cost-workbook <成本文件> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --ad-spend <推广总花费元> --store-name <店铺名称> --ad-source <截图来源说明> --ad-screenshot <截图路径> --output-json <输出目录/report_data.json>
```

固定规则：

- 优先使用“支付时间”；没有时使用“订单成交时间”并注明。
- 排除退款成功、取消、交易关闭和售后处理中订单。
- 读取成本表全部工作表。
- 使用订单“商品规格”关联成本“SKU名称”。
- 单笔商品成本 = 单件总成本 × 商品数量。
- 推广前利润 = 商家实收金额 - 商品总成本。
- 最终盈亏 = 推广前利润 - 推广总花费。

字段别名和匹配边界见 [references/field-mapping.md](references/field-mapping.md)。

### 4. 处理未匹配SKU

脚本返回“等待补成本”时：

1. 读取JSON中的 `未匹配SKU`。
2. 按商品规格去重，保留商品ID、商品名称、有效订单数、件数和原因。
3. 把清单发给用户补成本。
4. 暂停正式盈亏核算，不生成正式客户版Excel。

不得按名称相似随意套成本，不得只看克重而忽略品类和口味，不得沿用上月人工补充成本。

### 5. 生成中文客户版Excel

仅当状态为“完成”且未匹配SKU数量为0时运行：

```text
<python> scripts/build_profit_report.py --data <输出目录/report_data.json> --output <输出目录/月份-店铺-拼多多盈亏汇报表.xlsx>
```

Excel必须包含：`客户汇报`、`SKU汇总`、`订单明细`、`成本标准`、`剔除订单`、`未匹配SKU`、`参数与来源`、`核对检查`。

“客户汇报”必须单独列示“减：推广总花费”。

### 6. 强制核验

交付前确认：

1. 生成器成功重新打开Excel并完成结构检查。
2. `核对检查`页模型状态为 `PASS`。
3. 八张中文工作表齐全。
4. 商品ID完整，金额和长规格可读。
5. 推广费扣除在客户汇报页清晰可见。

任何一项失败都先修复，不把失败文件作为正式交付。

## 最终回复

先写最终盈利或亏损金额，再列出商家实收、商品总成本、推广前利润、推广总花费、最终盈亏、净利润率、有效订单数、剔除订单数和“未匹配SKU：无”。明确说明推广费已在客户汇报页“减：推广总花费”处扣除。

## 调用示例

- “帮我按拼多多月度算账技能核算这个店铺，并生成客户版Excel。”
- “使用 pdd-monthly-profit 算7月份赚了还是亏了。”
- Claude Code中可输入 `/pdd-monthly-profit` 后附带核算要求。
