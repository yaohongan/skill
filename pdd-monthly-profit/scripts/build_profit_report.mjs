import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error(`参数格式错误：${key ?? ""}`);
    }
    result[key.slice(2)] = value;
  }
  return result;
}

function requireArg(args, key) {
  if (!args[key]) throw new Error(`缺少参数：--${key}`);
  return args[key];
}

function asDate(value) {
  const [datePart, timePart = "00:00:00"] = String(value).split(" ");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute, second] = timePart.split(":").map(Number);
  return new Date(year, month - 1, day, hour, minute, second);
}

function safeName(value) {
  return value.replace(/[\\/:*?"<>|]/g, "_");
}

const args = parseArgs(process.argv.slice(2));
const dataPath = requireArg(args, "data");
const outputPath = requireArg(args, "output");
const previewDir = requireArg(args, "preview-dir");
const data = JSON.parse(await fs.readFile(dataPath, "utf8"));
if (data.状态 !== "完成" || !data.正式汇总) {
  throw new Error("存在未匹配SKU或其他阻断项，不能生成正式客户版Excel");
}
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const workbook = Workbook.create();
const summary = workbook.worksheets.add("客户汇报");
const skuSummary = workbook.worksheets.add("SKU汇总");
const detail = workbook.worksheets.add("订单明细");
const costs = workbook.worksheets.add("成本标准");
const excluded = workbook.worksheets.add("剔除订单");
const unmatched = workbook.worksheets.add("未匹配SKU");
const params = workbook.worksheets.add("参数与来源");
const checks = workbook.worksheets.add("核对检查");
workbook.comments.setSelf({ displayName: "User" });

const colors = {
  navy: "#17324D",
  blue: "#2563EB",
  green: "#138A72",
  red: "#C53B3B",
  amber: "#D28A00",
  ink: "#202B38",
  muted: "#667085",
  line: "#D7DEE8",
  paleBlue: "#EAF2FF",
  paleGreen: "#EAF7F3",
  paleRed: "#FDEBEC",
  paleAmber: "#FFF5DB",
  white: "#FFFFFF",
  gray: "#F6F8FA",
};
const moneyFormat = "#,##0.00;[Red](#,##0.00);-";
const countFormat = "#,##0;[Red](#,##0);-";

function title(sheet, range, text) {
  sheet.getRange(range).merge();
  const cell = range.split(":")[0];
  sheet.getRange(cell).values = [[text]];
  sheet.getRange(range).format = {
    fill: colors.navy,
    font: { name: "Microsoft YaHei", size: 16, bold: true, color: colors.white },
    verticalAlignment: "center",
  };
}

function header(sheet, range) {
  sheet.getRange(range).format = {
    fill: colors.navy,
    font: { name: "Microsoft YaHei", size: 10, bold: true, color: colors.white },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "inside", style: "thin", color: colors.white },
  };
}

function base(sheet, range) {
  sheet.getRange(range).format.font = { name: "Microsoft YaHei", size: 10, color: colors.ink };
  sheet.getRange(range).format.borders = { preset: "inside", style: "thin", color: colors.line };
}

function dateOrBlank(value) {
  return value ? asDate(value) : null;
}

// 参数与来源
params.showGridLines = false;
title(params, "A1:D2", "核算参数与数据来源");
params.getRange("A3:D3").values = [["参数", "数值", "来源", "说明"]];
const parameterRows = [
  ["店铺名称", data.参数.店铺名称, "用户提供/文件识别", "用于报告标题"],
  ["统计开始日期", dateOrBlank(data.参数.统计开始日期), "投流截图", "含当日"],
  ["统计结束日期", dateOrBlank(data.参数.统计结束日期), "投流截图", "含当日"],
  ["订单时间字段", data.参数.时间字段, "订单文件", data.参数.时间口径说明],
  ["推广总花费(元)", data.参数.推广总花费, data.参数.推广费来源 || "拼多多投流数据截图", "只使用总花费，不使用成交花费"],
  ["推广截图", data.参数.推广截图 || "未记录路径", "用户提供", "截图用于确认日期和总花费"],
  ["订单文件", data.参数.订单文件, data.参数.订单数据来源, "月度订单源文件"],
  ["成本文件", data.参数.成本文件, "成本Excel全部工作表", "使用SKU名称和总成本"],
  ["区间订单数", data.数据概况.区间订单数, "订单文件", "含剔除订单"],
  ["有效订单数", data.数据概况.有效订单数, "订单文件", "已排除退款、取消及售后处理中"],
  ["退款/取消订单数", data.数据概况.退款取消数, "订单文件", "不计收入和成本"],
  ["售后处理中订单数", data.数据概况.售后处理中数, "订单文件", "不计收入和成本"],
  ["剔除订单数", data.数据概况.剔除订单数, "订单文件", "退款/取消加售后处理中"],
  ["唯一规格映射数", data.数据概况.唯一规格映射数, "有效订单", "按商品ID和商品规格统计"],
  ["未匹配规格数", data.数据概况.未匹配规格数, "成本匹配", "正式结果必须为0"],
  ["源数据商家实收(元)", data.正式汇总.商家实收, "计算结果JSON", "用于Excel公式勾稽"],
  ["源数据商品总成本(元)", data.正式汇总.商品总成本, "计算结果JSON", "用于Excel公式勾稽"],
  ["源数据推广前利润(元)", data.正式汇总.推广前利润, "计算结果JSON", "用于Excel公式勾稽"],
  ["源数据最终盈亏(元)", data.正式汇总.最终盈亏, "计算结果JSON", "用于Excel公式勾稽"],
];
params.getRangeByIndexes(3, 0, parameterRows.length, 4).values = parameterRows;
const paramsEnd = parameterRows.length + 3;
header(params, "A3:D3");
base(params, `A4:D${paramsEnd}`);
params.getRange("B5:B6").format.numberFormat = "yyyy-mm-dd";
params.getRange("B8:B8").format.numberFormat = moneyFormat;
params.getRange(`B19:B22`).format.numberFormat = moneyFormat;
params.getRange("A:A").format.columnWidth = 27;
params.getRange("B:B").format.columnWidth = 47;
params.getRange("C:C").format.columnWidth = 35;
params.getRange("D:D").format.columnWidth = 54;
params.getRange(`A3:D${paramsEnd}`).format.rowHeight = 24;
params.getRange(`B4:D${paramsEnd}`).format.wrapText = true;
workbook.comments.addThread({ cell: params.getRange("B8") }, "推广费用采用截图中的“总花费（元）”，不采用“成交花费（元）”。");

// 订单明细
const detailHeaders = ["序号", "订单号", "商品ID", "订单时间", "订单状态", "售后状态", "商品名称", "商品规格", "商品数量", "商家实收金额(元)", "成本工作表", "匹配成本SKU", "单件总成本(元)", "订单总成本(元)", "推广前利润(元)", "匹配方式"];
detail.getRange("A1:P1").values = [detailHeaders];
const detailRows = data.订单明细.map((row) => [
  row.序号,
  row.订单号,
  row.商品ID,
  asDate(row.订单时间),
  row.订单状态,
  row.售后状态,
  row.商品名称,
  row.商品规格,
  row.商品数量,
  row.商家实收,
  row.成本工作表,
  row.成本SKU名称,
  row.单件总成本,
  null,
  null,
  row.匹配方式,
]);
if (detailRows.length) detail.getRangeByIndexes(1, 0, detailRows.length, detailHeaders.length).values = detailRows;
const detailEnd = Math.max(2, detailRows.length + 1);
if (detailRows.length) {
  detail.getRangeByIndexes(1, 2, detailRows.length, 1).formulas = data.订单明细.map((row) => [`="${String(row.商品ID).replaceAll('"', '""')}"`]);
  detail.getRange("N2").formulas = [["=I2*M2"]];
  detail.getRange(`N2:N${detailEnd}`).fillDown();
  detail.getRange("O2").formulas = [["=J2-N2"]];
  detail.getRange(`O2:O${detailEnd}`).fillDown();
}
header(detail, "A1:P1");
base(detail, `A2:P${detailEnd}`);
detail.getRange(`C2:C${detailEnd}`).format.numberFormat = "0";
detail.getRange(`D2:D${detailEnd}`).format.numberFormat = "yyyy-mm-dd hh:mm:ss";
detail.getRange(`I2:I${detailEnd}`).format.numberFormat = "#,##0.####";
detail.getRange(`J2:J${detailEnd}`).format.numberFormat = moneyFormat;
detail.getRange(`M2:O${detailEnd}`).format.numberFormat = moneyFormat;
detail.getRange("A:A").format.columnWidth = 9;
detail.getRange("B:C").format.columnWidth = 24;
detail.getRange("D:D").format.columnWidth = 22;
detail.getRange("E:F").format.columnWidth = 19;
detail.getRange("G:H").format.columnWidth = 52;
detail.getRange("I:O").format.columnWidth = 18;
detail.getRange("P:P").format.columnWidth = 30;
detail.getRange(`G2:H${detailEnd}`).format.wrapText = true;

// SKU汇总
const skuHeaders = ["商品ID", "商品名称", "商品规格", "有效订单数", "商品件数", "商家实收金额(元)", "成本工作表", "匹配成本SKU", "单件总成本(元)", "商品总成本(元)", "推广前利润(元)", "匹配状态", "匹配方式"];
skuSummary.getRange("A1:M1").values = [skuHeaders];
const skuRows = data.SKU映射.map((row) => [
  row.商品ID, row.商品名称, row.商品规格, row.有效订单数, row.商品件数,
  row.商家实收, row.成本工作表, row.成本SKU名称, row.单件总成本,
  null, null, row.匹配状态, row.匹配方式,
]);
if (skuRows.length) skuSummary.getRangeByIndexes(1, 0, skuRows.length, skuHeaders.length).values = skuRows;
const skuEnd = Math.max(2, skuRows.length + 1);
if (skuRows.length) {
  skuSummary.getRangeByIndexes(1, 0, skuRows.length, 1).formulas = data.SKU映射.map((row) => [`="${String(row.商品ID).replaceAll('"', '""')}"`]);
  skuSummary.getRange("J2").formulas = [["=E2*I2"]];
  skuSummary.getRange(`J2:J${skuEnd}`).fillDown();
  skuSummary.getRange("K2").formulas = [["=F2-J2"]];
  skuSummary.getRange(`K2:K${skuEnd}`).fillDown();
}
header(skuSummary, "A1:M1");
base(skuSummary, `A2:M${skuEnd}`);
skuSummary.getRange(`A2:A${skuEnd}`).format.numberFormat = "0";
skuSummary.getRange(`D2:E${skuEnd}`).format.numberFormat = countFormat;
skuSummary.getRange(`F2:F${skuEnd}`).format.numberFormat = moneyFormat;
skuSummary.getRange(`I2:K${skuEnd}`).format.numberFormat = moneyFormat;
skuSummary.getRange("A:A").format.columnWidth = 24;
skuSummary.getRange("B:C").format.columnWidth = 50;
skuSummary.getRange("D:F").format.columnWidth = 18;
skuSummary.getRange("G:H").format.columnWidth = 35;
skuSummary.getRange("I:M").format.columnWidth = 21;
skuSummary.getRange(`B2:C${skuEnd}`).format.wrapText = true;

// 成本标准
const costHeaders = ["工作表", "行号", "口味说明", "成本SKU名称", "重量(g)", "分类", "口味", "商品成本(元)", "运费(元)", "总成本(元)"];
costs.getRange("A1:J1").values = [costHeaders];
const costRows = data.成本标准.map((row) => [row.工作表, row.行号, row.口味说明, row.成本SKU名称 || "（成本表未填写SKU名称）", row.重量克数, row.分类, row.口味, row.成本, row.运费, row.总成本]);
if (costRows.length) costs.getRangeByIndexes(1, 0, costRows.length, costHeaders.length).values = costRows;
const costEnd = Math.max(2, costRows.length + 1);
header(costs, "A1:J1");
base(costs, `A2:J${costEnd}`);
costs.getRange(`B2:B${costEnd}`).format.numberFormat = countFormat;
costs.getRange(`E2:E${costEnd}`).format.numberFormat = countFormat;
costs.getRange(`H2:J${costEnd}`).format.numberFormat = moneyFormat;
costs.getRange("A:A").format.columnWidth = 27;
costs.getRange("B:B").format.columnWidth = 10;
costs.getRange("C:D").format.columnWidth = 48;
costs.getRange("E:J").format.columnWidth = 18;

// 剔除订单
const excludedHeaders = ["序号", "订单号", "商品ID", "订单时间", "订单状态", "售后状态", "商品名称", "商品规格", "商品数量", "商家实收金额(元)", "剔除原因"];
excluded.getRange("A1:K1").values = [excludedHeaders];
const excludedRows = data.剔除订单.map((row) => [row.序号, row.订单号, row.商品ID, asDate(row.订单时间), row.订单状态, row.售后状态, row.商品名称, row.商品规格, row.商品数量, row.商家实收, row.剔除原因]);
if (excludedRows.length) excluded.getRangeByIndexes(1, 0, excludedRows.length, excludedHeaders.length).values = excludedRows;
const excludedEnd = Math.max(2, excludedRows.length + 1);
if (excludedRows.length) excluded.getRangeByIndexes(1, 2, excludedRows.length, 1).formulas = data.剔除订单.map((row) => [`="${String(row.商品ID).replaceAll('"', '""')}"`]);
header(excluded, "A1:K1");
base(excluded, `A2:K${excludedEnd}`);
excluded.getRange(`C2:C${excludedEnd}`).format.numberFormat = "0";
excluded.getRange(`D2:D${excludedEnd}`).format.numberFormat = "yyyy-mm-dd hh:mm:ss";
excluded.getRange(`I2:I${excludedEnd}`).format.numberFormat = countFormat;
excluded.getRange(`J2:J${excludedEnd}`).format.numberFormat = moneyFormat;
excluded.getRange("A:A").format.columnWidth = 9;
excluded.getRange("B:C").format.columnWidth = 24;
excluded.getRange("D:F").format.columnWidth = 21;
excluded.getRange("G:H").format.columnWidth = 50;
excluded.getRange("I:K").format.columnWidth = 18;
excluded.getRange(`G2:H${excludedEnd}`).format.wrapText = true;

// 未匹配SKU
unmatched.showGridLines = false;
title(unmatched, "A1:H2", "未匹配SKU清单");
unmatched.getRange("A4:H4").values = [["商品ID", "商品名称", "商品规格", "有效订单数", "商品件数", "商家实收金额(元)", "未匹配原因", "处理状态"]];
const unmatchedRows = data.未匹配SKU.length
  ? data.未匹配SKU.map((row) => [row.商品ID, row.商品名称, row.商品规格, row.有效订单数, row.商品件数, row.商家实收, row.未匹配原因, "等待补成本"])
  : [["", "", "无", 0, 0, 0, "全部SKU已匹配", "已完成"]];
unmatched.getRangeByIndexes(4, 0, unmatchedRows.length, 8).values = unmatchedRows;
const unmatchedEnd = unmatchedRows.length + 4;
if (data.未匹配SKU.length) unmatched.getRangeByIndexes(4, 0, unmatchedRows.length, 1).formulas = data.未匹配SKU.map((row) => [`="${String(row.商品ID).replaceAll('"', '""')}"`]);
header(unmatched, "A4:H4");
base(unmatched, `A5:H${unmatchedEnd}`);
unmatched.getRange(`A5:A${unmatchedEnd}`).format.numberFormat = "0";
unmatched.getRange(`D5:E${unmatchedEnd}`).format.numberFormat = countFormat;
unmatched.getRange(`F5:F${unmatchedEnd}`).format.numberFormat = moneyFormat;
unmatched.getRange("A:A").format.columnWidth = 24;
unmatched.getRange("B:C").format.columnWidth = 50;
unmatched.getRange("D:H").format.columnWidth = 21;

// 客户汇报
summary.showGridLines = false;
const reportMonth = data.参数.统计开始日期.slice(0, 7).replace("-", "年") + "月";
title(summary, "A1:H2", `${reportMonth}${data.参数.店铺名称}盈亏汇报`);
summary.getRange("A4:H4").merge();
summary.getRange("A4").values = [[`核算期间：${data.参数.统计开始日期} 至 ${data.参数.统计结束日期}    有效订单：${data.数据概况.有效订单数.toLocaleString("zh-CN")}笔`]];
summary.getRange("A4:H4").format = { fill: colors.paleBlue, font: { name: "Microsoft YaHei", size: 11, bold: true, color: colors.blue }, verticalAlignment: "center" };
summary.getRange("A6:B8").merge();
summary.getRange("A6").values = [["最终结果"]];
summary.getRange("A6:B8").format = { fill: data.正式汇总.最终盈亏 >= 0 ? colors.paleGreen : colors.paleRed, font: { name: "Microsoft YaHei", size: 14, bold: true, color: data.正式汇总.最终盈亏 >= 0 ? colors.green : colors.red }, horizontalAlignment: "center", verticalAlignment: "center" };
summary.getRange("C6:E8").merge();
summary.getRange("C6").formulas = [["=B15"]];
summary.getRange("C6:E8").format = { fill: data.正式汇总.最终盈亏 >= 0 ? colors.paleGreen : colors.paleRed, font: { name: "Microsoft YaHei", size: 20, bold: true, color: data.正式汇总.最终盈亏 >= 0 ? colors.green : colors.red }, horizontalAlignment: "center", verticalAlignment: "center", numberFormat: moneyFormat };
summary.getRange("F6:H8").merge();
summary.getRange("F6").formulas = [["=IF(B15>=0,\"盈利\",\"亏损\")"]];
summary.getRange("F6:H8").format = { fill: colors.paleAmber, font: { name: "Microsoft YaHei", size: 17, bold: true, color: colors.amber }, horizontalAlignment: "center", verticalAlignment: "center" };
summary.getRange("A10:C10").values = [["核算项目", "金额/比例", "说明"]];
summary.getRange("A11:A17").values = [["商家实收金额"], ["减：商品总成本"], ["推广前利润"], ["减：推广总花费"], ["最终盈亏"], ["净利润率"], ["盈亏状态"]];
summary.getRange("B11:B17").formulas = [
  [`=SUM('订单明细'!J2:J${detailEnd})`],
  [`=SUM('订单明细'!N2:N${detailEnd})`],
  ["=B11-B12"],
  ["='参数与来源'!B8"],
  ["=B13-B14"],
  ["=IFERROR(B15/B11,0)"],
  ["=IF(B15>=0,\"盈利\",\"亏损\")"],
];
summary.getRange("C11:C17").values = [["有效订单实际到账"], ["单件总成本×商品数量"], ["尚未扣除推广费"], ["截图中的总花费（元）"], ["推广前利润-推广总花费"], ["最终盈亏÷商家实收"], ["根据最终盈亏自动判断"]];
header(summary, "A10:C10");
base(summary, "A11:C17");
summary.getRange("B11:B15").format.numberFormat = moneyFormat;
summary.getRange("B16").format.numberFormat = "0.0%";
summary.getRange("A15:C15").format = { fill: data.正式汇总.最终盈亏 >= 0 ? colors.paleGreen : colors.paleRed, font: { name: "Microsoft YaHei", size: 12, bold: true, color: data.正式汇总.最终盈亏 >= 0 ? colors.green : colors.red }, borders: { preset: "inside", style: "thin", color: colors.line } };
summary.getRange("A:A").format.columnWidth = 31;
summary.getRange("B:B").format.columnWidth = 24;
summary.getRange("C:C").format.columnWidth = 48;
summary.getRange("D:H").format.columnWidth = 17;
summary.getRange("A1:H2").format.rowHeight = 28;
summary.getRange("A4:H4").format.rowHeight = 30;
summary.getRange("A6:H8").format.rowHeight = 27;
summary.getRange("A10:C17").format.rowHeight = 27;
workbook.comments.addThread({ cell: summary.getRange("B14") }, "推广总花费已在此处单独扣除，并进入最终盈亏公式。" );

// 核对检查
checks.showGridLines = false;
title(checks, "A1:E2", "核对检查");
checks.getRange("A3:E3").values = [["检查项目", "计算值", "目标值", "差异", "状态"]];
checks.getRange("A4:A10").values = [["区间订单数=有效订单+剔除订单"], ["有效订单数=订单明细行数"], ["订单明细实收=源数据实收"], ["订单明细成本=源数据成本"], ["推广前利润=源数据推广前利润"], ["最终盈亏=推广前利润-推广费"], ["未匹配SKU数=0"]];
checks.getRange("B4:C10").formulas = [
  ["='参数与来源'!B12", "='参数与来源'!B13+'参数与来源'!B16"],
  ["='参数与来源'!B13", `=COUNTA('订单明细'!B2:B${detailEnd})`],
  [`=SUM('订单明细'!J2:J${detailEnd})`, "='参数与来源'!B19"],
  [`=SUM('订单明细'!N2:N${detailEnd})`, "='参数与来源'!B20"],
  ["='客户汇报'!B13", "='参数与来源'!B21"],
  ["='客户汇报'!B15", "='客户汇报'!B13-'客户汇报'!B14"],
  ["='参数与来源'!B18", "=0"],
];
checks.getRange("D4").formulas = [["=B4-C4"]];
checks.getRange("D4:D10").fillDown();
checks.getRange("E4").formulas = [["=IF(ABS(D4)<0.01,\"PASS\",\"FAIL\")"]];
checks.getRange("E4:E10").fillDown();
checks.getRange("A12:B12").values = [["模型状态", null]];
checks.getRange("B12").formulas = [["=IF(COUNTIF(E4:E10,\"FAIL\")=0,\"PASS\",\"FAIL\")"]];
header(checks, "A3:E3");
base(checks, "A4:E10");
checks.getRange("B4:D10").format.numberFormat = moneyFormat;
checks.getRange("A12:B12").format = { fill: colors.paleGreen, font: { name: "Microsoft YaHei", size: 12, bold: true, color: colors.green }, borders: { preset: "inside", style: "thin", color: colors.line } };
checks.getRange("A:A").format.columnWidth = 48;
checks.getRange("B:D").format.columnWidth = 22;
checks.getRange("E:E").format.columnWidth = 15;
checks.getRange("A3:E12").format.rowHeight = 26;

const summaryInspect = await workbook.inspect({ kind: "table", sheetId: "客户汇报", range: "A10:C17", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8, maxChars: 6000 });
const checksInspect = await workbook.inspect({ kind: "table", sheetId: "核对检查", range: "A3:E12", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8, maxChars: 6000 });
const formulaErrors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "公式错误扫描", maxChars: 6000 });

const previews = [
  ["客户汇报", "A1:H18"],
  ["SKU汇总", `A1:M${Math.min(skuEnd, 28)}`],
  ["订单明细", `A1:P${Math.min(detailEnd, 28)}`],
  ["成本标准", `A1:J${Math.min(costEnd, 35)}`],
  ["剔除订单", `A1:K${Math.min(excludedEnd, 28)}`],
  ["未匹配SKU", `A1:H${unmatchedEnd}`],
  ["参数与来源", `A1:D${paramsEnd}`],
  ["核对检查", "A1:E12"],
];
for (const [sheetName, range] of previews) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `预览-${safeName(sheetName)}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const verification = {
  summary: summaryInspect.ndjson,
  checks: checksInspect.ndjson,
  formulaErrors: formulaErrors.ndjson,
  sheetNames: workbook.worksheets.items.map((sheet) => sheet.name),
};
await fs.writeFile(path.join(previewDir, "核验结果.json"), JSON.stringify(verification, null, 2), "utf8");
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(summaryInspect.ndjson);
console.log(checksInspect.ndjson);
console.log(formulaErrors.ndjson);
console.log(JSON.stringify({ outputPath, previewDir, sheetNames: verification.sheetNames, detailRows: detailRows.length, excludedRows: excludedRows.length, skuRows: skuRows.length }, null, 2));
