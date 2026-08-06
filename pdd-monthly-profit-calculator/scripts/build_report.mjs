#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";


function argument(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || !process.argv[index + 1]) throw new Error(`缺少参数 ${name}`);
  return process.argv[index + 1];
}

const inputPath = argument("--input");
const outputPath = argument("--output");
const nodeModules = process.env.CODEX_NODE_MODULES;
if (!nodeModules) throw new Error("缺少 CODEX_NODE_MODULES，请先加载工作区依赖并传入 Node 模块目录");
const artifactPath = path.join(nodeModules, "@oai", "artifact-tool", "dist", "artifact_tool.mjs");
const { SpreadsheetFile, Workbook } = await import(pathToFileURL(artifactPath).href);
const data = JSON.parse(await fs.readFile(inputPath, "utf8"));

const wb = Workbook.create();
const overview = wb.worksheets.add("核算说明");
const sku = wb.worksheets.add("商品盈亏汇总");
const detail = wb.worksheets.add("有效订单明细");
const costs = wb.worksheets.add("成本映射");
const unmatched = wb.worksheets.add("未匹配商品");
const excluded = wb.worksheets.add("排除订单");

const colors = {
  dark: "#17324D", teal: "#087E8B", lightBlue: "#EAF1F8", yellow: "#FFF1B8",
  red: "#F8D7DA", green: "#D9EFD9", gray: "#F3F5F7", border: "#D8DEE6",
};
const money = "#,##0.00;[Red]-#,##0.00";

function title(sheet, range, text) {
  sheet.getRange(range).merge();
  const cell = sheet.getRange(range.split(":")[0]);
  cell.values = [[text]];
  cell.format = { fill: colors.dark, font: { bold: true, color: "#FFFFFF", size: 16 }, verticalAlignment: "center" };
  sheet.getRange(range).format.rowHeight = 32;
}

function header(range) {
  range.format = {
    fill: colors.teal, font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center",
    verticalAlignment: "center", wrapText: true,
    borders: { preset: "all", style: "thin", color: colors.border },
  };
  range.format.rowHeight = 28;
}

function body(range) {
  range.format = { verticalAlignment: "center", borders: { preset: "inside", style: "thin", color: colors.border } };
}

function putRows(sheet, startRowZeroBased, rows) {
  if (rows.length) sheet.getRangeByIndexes(startRowZeroBased, 0, rows.length, rows[0].length).values = rows;
}

function asText(value) {
  return value === null || value === undefined ? "" : String(value);
}

function productCell(value) {
  const text = asText(value);
  return /^\d{1,15}$/.test(text) ? Number(text) : text;
}

const costMap = new Map();
for (const row of data.cost_source_rows ?? []) {
  const productId = asText(row["商品id"]);
  if (productId && !costMap.has(productId)) costMap.set(productId, Number(row["总成本"]));
}
const costRows = [...costMap.entries()].map(([productId, totalCost]) => [productCell(productId), totalCost]);

title(costs, "A1:B1", "成本映射（来自原始成本表）");
costs.getRange("A2:B2").values = [["商品ID", "单件总成本"]];
header(costs.getRange("A2:B2"));
putRows(costs, 2, costRows);
const costEnd = Math.max(3, costRows.length + 2);
if (costRows.length) body(costs.getRange(`A3:B${costEnd}`));
costs.getRange(`A3:A${costEnd}`).format.numberFormat = "0";
costs.getRange(`B3:B${costEnd}`).format.numberFormat = money;
costs.getRange("A:A").format.columnWidth = 20;
costs.getRange("B:B").format.columnWidth = 18;

title(detail, "A1:L1", `有效订单明细（${data.start_date} 至 ${data.end_date}）`);
detail.getRange("A2:L2").values = [["商品", "订单号", "订单状态", "售后状态", "订单成交时间", "商品ID", "商品规格", "商家实收金额(元)", "商品数量(件)", "单件总成本", "订单总成本", "商品毛利"]];
header(detail.getRange("A2:L2"));
const detailRows = (data.matched_order_details ?? []).map((row) => [
  row["商品"] ?? "", asText(row["订单号"]), row["订单状态"] ?? "", row["售后状态"] ?? "",
  row["订单成交时间"] ?? "", productCell(row["商品id"]), row["商品规格"] ?? "",
  Number(row["商家实收金额(元)"]), Number(row["商品数量(件)"]), null, null, null,
]);
putRows(detail, 2, detailRows);
const detailEnd = Math.max(3, detailRows.length + 2);
if (detailRows.length) {
  detail.getRange("J3").formulas = [[`=IFERROR(VLOOKUP(F3,'成本映射'!$A$3:$B$${costEnd},2,FALSE),0)`]];
  detail.getRange(`J3:J${detailEnd}`).fillDown();
  detail.getRange("K3").formulas = [["=I3*J3"]];
  detail.getRange(`K3:K${detailEnd}`).fillDown();
  detail.getRange("L3").formulas = [["=H3-K3"]];
  detail.getRange(`L3:L${detailEnd}`).fillDown();
  body(detail.getRange(`A3:L${detailEnd}`));
}
detail.getRange(`B3:B${detailEnd}`).format.numberFormat = "@";
detail.getRange(`F3:F${detailEnd}`).format.numberFormat = "0";
detail.getRange(`H3:H${detailEnd}`).format.numberFormat = money;
detail.getRange(`I3:I${detailEnd}`).format.numberFormat = "#,##0";
detail.getRange(`J3:L${detailEnd}`).format.numberFormat = money;
detail.freezePanes.freezeRows(2);

title(sku, "A1:H1", "按商品ID汇总盈亏（未分摊投流）");
sku.getRange("A2:H2").values = [["商品ID", "单件总成本", "有效订单行数", "有效数量", "商家实收金额(元)", "商品总成本", "商品毛利", "毛利率"]];
header(sku.getRange("A2:H2"));
const skuRows = (data.sku_summary ?? []).map((row) => [
  productCell(row["商品id"]), Number(row["单件总成本"]), Number(row["有效订单行数"]), Number(row["有效数量"]),
  Number(row["商家实收"]), Number(row["订单总成本"]), Number(row["商品毛利"]), Number(row["毛利率"]),
]);
putRows(sku, 2, skuRows);
const skuEnd = Math.max(3, skuRows.length + 2);
if (skuRows.length) body(sku.getRange(`A3:H${skuEnd}`));
const totalRow = skuEnd + 1;
sku.getRange(`A${totalRow}:H${totalRow}`).values = [["合计", "", data.matched_valid_rows, data.valid_qty, data.merchant_received, data.product_cost, data.gross_profit, data.merchant_received ? data.gross_profit / data.merchant_received : 0]];
sku.getRange(`A${totalRow}:H${totalRow}`).format = { fill: colors.lightBlue, font: { bold: true, color: colors.dark } };
sku.getRange(`A3:A${skuEnd}`).format.numberFormat = "0";
sku.getRange(`B3:B${skuEnd}`).format.numberFormat = money;
sku.getRange(`C3:D${totalRow}`).format.numberFormat = "#,##0";
sku.getRange(`E3:G${totalRow}`).format.numberFormat = money;
sku.getRange(`H3:H${totalRow}`).format.numberFormat = "0.00%";
sku.freezePanes.freezeRows(2);

title(unmatched, "A1:E1", "成本未匹配商品（未计算成本与利润）");
unmatched.getRange("A2:E2").values = [["商品ID", "订单行数", "商品数量", "商家实收金额(元)", "处理说明"]];
header(unmatched.getRange("A2:E2"));
const unmatchedRows = (data.unmatched_products ?? []).map((row) => [
  productCell(row["商品id"]), Number(row["订单行数"]), Number(row["商品数量"]), Number(row["商家实收"]), "请补充单件总成本后重新核算",
]);
if (unmatchedRows.length) putRows(unmatched, 2, unmatchedRows);
else unmatched.getRange("A3:E3").values = [["无", 0, 0, 0, "成本表已覆盖全部有效订单商品ID"]];
const unmatchedEnd = Math.max(3, unmatchedRows.length + 2);
body(unmatched.getRange(`A3:E${unmatchedEnd}`));
unmatched.getRange(`A3:A${unmatchedEnd}`).format.numberFormat = "0";
unmatched.getRange(`D3:D${unmatchedEnd}`).format.numberFormat = money;

title(excluded, "A1:I1", "退款、退货、取消或售后处理中订单（不纳入核算）");
excluded.getRange("A2:I2").values = [["商品", "订单号", "订单状态", "售后状态", "订单成交时间", "商品ID", "商品规格", "商家实收金额(元)", "商品数量(件)"]];
header(excluded.getRange("A2:I2"));
const excludedRows = (data.excluded_order_details ?? []).map((row) => [
  row["商品"] ?? "", asText(row["订单号"]), row["订单状态"] ?? "", row["售后状态"] ?? "",
  row["订单成交时间"] ?? "", productCell(row["商品id"]), row["商品规格"] ?? "",
  Number(row["商家实收金额(元)"]), Number(row["商品数量(件)"]),
]);
if (excludedRows.length) putRows(excluded, 2, excludedRows);
else excluded.getRange("A3:I3").values = [["无", "", "", "", "", "", "", 0, 0]];
const excludedEnd = Math.max(3, excludedRows.length + 2);
body(excluded.getRange(`A3:I${excludedEnd}`));
excluded.getRange(`B3:B${excludedEnd}`).format.numberFormat = "@";
excluded.getRange(`F3:F${excludedEnd}`).format.numberFormat = "0";
excluded.getRange(`H3:H${excludedEnd}`).format.numberFormat = money;

const statusLabel = data.is_temporary ? "暂算：存在成本未匹配商品" : "完整核算：成本已全部匹配";
title(overview, "A1:F1", `${data.shop_name}｜${data.start_date} 至 ${data.end_date}｜利润核算｜${statusLabel}`);
overview.getRange("A3:B3").values = [["核算项目", "结果"]];
header(overview.getRange("A3:B3"));
overview.getRange("A4:B10").values = [
  ["核算日期", `${data.start_date} 至 ${data.end_date}`],
  ["匹配成本的有效订单行数", data.matched_valid_rows],
  ["匹配成本的商品数量", data.valid_qty],
  ["商家实收金额(元)", data.merchant_received],
  ["商品总成本(元)", data.product_cost],
  ["商品毛利(元)", data.gross_profit],
  ["投流总花费(元，可修改)", data.ad_spend_input],
];
body(overview.getRange("A4:B10"));
overview.getRange("A12:B14").values = [["最终结果", ""], ["扣投流后净利润(元)", null], ["盈利/亏损", null]];
overview.getRange("B13").formulas = [["=B9-B10"]];
overview.getRange("B14").formulas = [[`=IF(B13>=0,"盈利","亏损")`]];
overview.getRange("A12:B12").format = { fill: colors.dark, font: { bold: true, color: "#FFFFFF" } };
overview.getRange("A13:B14").format = { fill: colors.lightBlue, font: { bold: true, color: colors.dark } };
overview.getRange("B7:B10").format.numberFormat = money;
overview.getRange("B13").format.numberFormat = money;
overview.getRange("B10").format = { fill: colors.yellow, font: { bold: true, color: colors.dark }, numberFormat: money };

overview.getRange("D3:F3").merge();
overview.getRange("D3").values = [["核算说明与追溯口径"]];
overview.getRange("D3").format = { fill: colors.teal, font: { bold: true, color: "#FFFFFF" } };
const notes = [
  `1. 日期范围以投流截图为准：${data.start_date} 至 ${data.end_date}。`,
  `2. 投流总花费来自截图，当前按${Number(data.ad_spend_input).toLocaleString("zh-CN", { minimumFractionDigits: 2 })}元录入；黄色单元格可替换为平台精确值。`,
  "3. 每笔订单成本 = 单件总成本 × 商品数量；商品毛利 = 商家实收 - 订单总成本。",
  `4. 已排除退款、退货、取消或售后处理中订单${data.excluded_status_rows}行。`,
  data.is_temporary
    ? `5. 当前为暂算：另有${data.unmatched_rows}行、${data.unmatched_qty}件、商家实收${Number(data.unmatched_received).toFixed(2)}元因缺成本未计利润。`
    : "5. 成本表已覆盖全部有效订单商品ID，本次为完整核算。",
  "6. 未计入平台技术服务费、税费等输入资料之外的费用。",
];
overview.getRange("D4:F9").merge(true);
overview.getRange("D4:F9").values = notes.map((note) => [note, "", ""]);
overview.getRange("D4:F9").format = { fill: colors.gray, wrapText: true, verticalAlignment: "top", font: { color: colors.dark } };

for (const sheet of [overview, sku, detail, costs, unmatched, excluded]) sheet.showGridLines = false;
overview.getRange("A:A").format.columnWidth = 27;
overview.getRange("B:B").format.columnWidth = 20;
overview.getRange("C:C").format.columnWidth = 3;
overview.getRange("D:F").format.columnWidth = 23;
overview.getRange("D4:F9").format.rowHeight = 52;
sku.getRange("A:A").format.columnWidth = 20;
sku.getRange("B:H").format.columnWidth = 16;
detail.getRange("A:A").format.columnWidth = 34;
detail.getRange("B:B").format.columnWidth = 24;
detail.getRange("C:F").format.columnWidth = 20;
detail.getRange("G:G").format.columnWidth = 34;
detail.getRange("H:L").format.columnWidth = 16;
unmatched.getRange("A:A").format.columnWidth = 20;
unmatched.getRange("B:D").format.columnWidth = 18;
unmatched.getRange("E:E").format.columnWidth = 34;
excluded.getRange("A:A").format.columnWidth = 34;
excluded.getRange("B:I").format.columnWidth = 20;

await wb.comments.setSelf({ displayName: "核算人员" });
wb.comments.addThread(
  { cell: overview.getRange("B10") },
  "来源：用户提供的拼多多投流数据截图。截图若以“万”为单位显示则属于四舍五入近似值，请取得平台精确金额后替换此黄色单元格。",
);

const exported = await SpreadsheetFile.exportXlsx(wb);
await exported.save(outputPath);
console.log(JSON.stringify({ output: outputPath, status: statusLabel }, null, 2));
