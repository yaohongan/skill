---
name: pdd-monthly-profit
description: Use when the user asks to calculate a Pinduoduo monthly store profit or loss from an ad-spend screenshot, order export, and multi-sheet cost workbook, including Chinese requests such as 拼多多算账、月度盈亏、算利润、算亏损、扣推广费、匹配SKU、生成客户汇报表, or when the user provides 拼多多投流图、订单表和成本表.
---

# 拼多多月度盈亏计算

## 核心原则

使用订单实收、单件总成本、商品数量和推广总花费计算可核对的月度盈亏。关键字段、日期、推广费或成本不明确时暂停并询问，不估算正式结果。

默认交付：

1. 对话中的盈亏结论与计算拆解。
2. 去重后的未匹配SKU清单；全部匹配时写“无”。
3. 包含八个中文工作表的客户版Excel。

## 必要输入

- 拼多多投流数据截图，可为一张或多张。
- 商品成本Excel，支持XLS/XLSX并读取全部工作表。
- 月度订单文件，支持CSV/XLS/XLSX。
- 可选的店铺名称和核算月份。

缺少任一必要输入时，先向用户索取。不要从上月资料推断本月推广费或成本。

## 工作流程

### 1. 确认日期与推广费

使用 `view_image` 查看投流截图：

- 优先读取截图右上角的明确起止日期。
- 只采用“总花费（元）”，不得采用“成交花费（元）”。
- 截图以“万”展示时，按截图值乘以10000，并在报告中保留来源说明。
- 日期或总花费看不清时，先请用户确认，不继续正式核算。
- 订单文件跨多个可能月份且截图日期不明确时，先确认核算区间。

开始计算前，用一句话复述核算日期和推广总花费。

### 2. 准备运行环境

读取并遵守 `spreadsheets:Spreadsheets` 技能。调用 `codex_app__load_workspace_dependencies` 获取捆绑的Python、Node.js和 `@oai/artifact-tool` 路径。

在本次任务的独立输出目录中：

1. 创建运行目录和预览目录。
2. 将 `scripts/build_profit_report.mjs` 复制到运行目录。
3. 在运行目录创建指向加载器提供的 `node_modules` 的Windows Junction。
4. 所有中间JSON和预览图留在输出目录中，不修改用户源文件。

不要安装新的表格库，不要修改加载器提供的依赖目录。

### 3. 计算订单与成本

运行：

```powershell
python <skill-root>/scripts/prepare_profit_data.py `
  --orders <订单文件> `
  --cost-workbook <成本文件> `
  --start <YYYY-MM-DD> `
  --end <YYYY-MM-DD> `
  --ad-spend <推广总花费元> `
  --store-name <店铺名称> `
  --ad-source <截图来源说明> `
  --ad-screenshot <截图路径> `
  --output-json <输出目录/report_data.json>
```

脚本执行以下固定规则：

- 优先使用“支付时间”；没有支付时间时使用“订单成交时间”，并在报告中注明。
- 排除退款成功、取消、交易关闭和售后处理中订单。
- 读取成本表全部工作表。
- 使用订单“商品规格”关联成本“SKU名称”。
- 单笔商品成本 = 单件总成本 × 商品数量。
- 推广前利润 = 商家实收金额 - 商品总成本。
- 最终盈亏 = 推广前利润 - 推广总花费。

常见字段别名和匹配边界见 [references/field-mapping.md](references/field-mapping.md)。

### 4. 处理未匹配SKU

脚本状态为“等待补成本”或返回非零状态时：

1. 读取输出JSON中的 `未匹配SKU`。
2. 按商品规格去重，保留商品ID、商品名称、有效订单数、件数和未匹配原因。
3. 直接把清单发给用户补成本。
4. 暂停正式盈亏核算，不生成正式客户版Excel。

不要执行以下操作：

- 不按名称相似就随意套成本。
- 不只看克重而忽略品类和口味。
- 不沿用上月人工补充成本。
- 不把已匹配订单的临时盈亏当作全店正式结果。

用户补完成本表后，重新从步骤3运行全部核算。

### 5. 生成中文客户版Excel

仅当状态为“完成”且未匹配SKU数量为0时运行复制到运行目录的生成器：

```powershell
node <运行目录>/build_profit_report.mjs `
  --data <输出目录/report_data.json> `
  --output <输出目录/月份-店铺-拼多多盈亏汇报表.xlsx> `
  --preview-dir <输出目录/previews>
```

Excel必须包含：

- `客户汇报`
- `SKU汇总`
- `订单明细`
- `成本标准`
- `剔除订单`
- `未匹配SKU`
- `参数与来源`
- `核对检查`

“客户汇报”必须单独列示“减：推广总花费”，不能只把推广费隐藏在最终公式中。

### 6. 强制核验

交付前完成全部检查：

1. 查看生成器输出的客户汇报和核对检查结果。
2. 确认核对检查全部为 `PASS`。
3. 确认公式错误扫描为0。
4. 使用 `view_image` 查看八张预览图。
5. 确认中文无乱码、商品ID完整、长规格可读、金额未截断、推广费扣除可见。
6. 确认最终Excel存在且可读取。

任何一项失败都先修复并重新导出，不把失败文件作为正式交付。

## 最终回复格式

先写最终盈利或亏损金额，再列出：

- 商家实收
- 商品总成本
- 推广前利润
- 推广总花费
- 最终盈亏
- 净利润率
- 有效订单数和剔除订单数
- 未匹配SKU：无

明确说明推广费已在客户汇报页“减：推广总花费”处扣除。最终Excel只引用一次，不向用户展示中间JSON、脚本或预览图。

## 调用示例

- “帮我按拼多多月度算账技能核算这个店铺，并生成客户版Excel。”
- “用 `$pdd-monthly-profit` 算7月份赚了还是亏了。”
