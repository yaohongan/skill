import argparse
import json
import sys
from pathlib import Path

from profit_core import prepare_report_data


def build_parser():
    parser = argparse.ArgumentParser(description="准备拼多多月度盈亏核算数据")
    parser.add_argument("--orders", required=True, help="订单CSV/XLS/XLSX路径")
    parser.add_argument("--cost-workbook", required=True, help="成本XLS/XLSX路径")
    parser.add_argument("--start", required=True, help="统计开始日期 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="统计结束日期 YYYY-MM-DD")
    parser.add_argument("--ad-spend", required=True, type=float, help="推广总花费（元）")
    parser.add_argument("--store-name", default="拼多多店铺", help="店铺名称")
    parser.add_argument("--ad-source", default="拼多多投流数据截图", help="推广费来源说明")
    parser.add_argument("--ad-screenshot", default="", help="推广截图路径")
    parser.add_argument("--output-json", required=True, help="结构化结果JSON路径")
    return parser


def main():
    args = build_parser().parse_args()
    result = prepare_report_data(
        args.orders,
        args.cost_workbook,
        args.start,
        args.end,
        args.ad_spend,
        args.store_name,
    )
    result["参数"]["推广费来源"] = args.ad_source
    result["参数"]["推广截图"] = args.ad_screenshot
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary = {
        "状态": result["状态"],
        "数据概况": result["数据概况"],
        "未匹配SKU": result["未匹配SKU"],
        "正式汇总": result.get("正式汇总"),
        "输出JSON": str(output_path.resolve()),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if result["状态"] != "完成":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
