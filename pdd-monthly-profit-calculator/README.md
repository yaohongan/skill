# 拼多多月度利润核算 Skill

一个面向拼多多店铺月度算账的 Codex Skill。提供投流截图、商品成本表和订单导出文件后，它会按商品 ID 逐单计算商品毛利，再扣除投流费用，并生成中文客户核对版 Excel。

## 适用场景

- 核算拼多多店铺一个月盈利还是亏损
- 按商品 ID 查看实收、成本和商品毛利
- 排除退款、退货、取消和售后处理中订单
- 成本缺失时先核算已匹配部分，并明确标记为“暂算”
- 生成可以发给客户逐笔核对的 Excel

## 需要提供

1. **拼多多投流截图**：包含统计日期和“总花费(元)”。
2. **商品成本 Excel**：至少包含商品 ID 和单件“总成本”。
3. **月度订单文件**：支持 CSV、XLSX 和 XLS。

截图由 Codex 读取日期和投流总花费。脚本本身不包含 OCR，也不会登录拼多多后台。

## 核算公式

```text
订单总成本 = 单件总成本 × 商品数量
商品毛利 = 商家实收金额 - 订单总成本
投流后净利润 = 商品毛利合计 - 投流总花费
```

主要规则：

- 日期范围以投流截图为准，起止日期均包含当天。
- 同时检查“订单状态”和“售后状态”。
- 未匹配成本的商品不会估算利润，而是单独列出并标记暂算。
- 同一商品 ID 的相同成本可以去重；不同成本会中止核算并提示冲突。
- 截图显示 `1.31万` 时按 `13,100元` 暂录，报告中的黄色投流金额单元格可以替换为平台精确值。

完整字段要求见 [`references/字段与口径.md`](./references/字段与口径.md)。

## 输出内容

默认生成一个中文客户核对版 Excel，包含：

| 工作表 | 内容 |
|---|---|
| 核算说明 | 日期、实收、成本、商品毛利、投流费用和最终净利润 |
| 商品盈亏汇总 | 按商品 ID 汇总订单、数量、收入、成本和毛利 |
| 有效订单明细 | 每笔有效订单及可追溯计算公式 |
| 成本映射 | 商品 ID 与单件总成本来源 |
| 未匹配商品 | 缺少成本的商品、数量和商家实收 |
| 排除订单 | 退款、退货、取消或售后处理中订单 |

## 安装

### Windows PowerShell

```powershell
git clone https://github.com/yaohongan/skill.git
Copy-Item -Recurse -Force .\skill\pdd-monthly-profit-calculator $HOME\.codex\skills\
```

### macOS / Linux

```bash
git clone https://github.com/yaohongan/skill.git
mkdir -p ~/.codex/skills
cp -R skill/pdd-monthly-profit-calculator ~/.codex/skills/
```

安装后的入口文件应位于：

```text
~/.codex/skills/pdd-monthly-profit-calculator/SKILL.md
```

## 如何调用

上传投流截图、成本表和订单文件，然后在 Codex 中说：

```text
使用 $pdd-monthly-profit-calculator 帮我核算这个拼多多店铺7月份的利润，并生成客户核对版 Excel。
```

存在成本未匹配商品时，技能会继续计算已匹配部分并明确写明“暂算”，不会用猜测成本补齐结果。

## 目录结构

```text
pdd-monthly-profit-calculator/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   └── 字段与口径.md
├── scripts/
│   ├── analyze_profit.py
│   └── build_report.mjs
└── tests/
    ├── test_analyze_profit.py
    ├── test_report_builder.py
    └── test_skill_contract.py
```

## 运行环境

- Python 3.10+
- `pandas`、`openpyxl`
- Codex 工作区提供的 Node.js 和 `@oai/artifact-tool`

通常由 Codex 自动加载并调用这些依赖，不需要手工执行脚本。

## 隐私说明

仓库不包含真实店铺订单、商品成本、客户名称、投流截图或核算报告。使用时请自行确认订单和成本文件的保存、分享及合规要求。

## 局限

- 投流截图中的“万”通常是四舍五入值，最终对账建议替换为平台导出的精确金额。
- 未提供的平台技术服务费、税费、仓储费等费用不会自动计入。
- 计算结果取决于成本表、订单状态和售后状态是否准确。
