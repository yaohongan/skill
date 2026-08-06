#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import pandas as pd


COST_ID_ALIASES = ("商品id", "商品ID", "商品Id", "商品编号")
ORDER_ID_ALIASES = COST_ID_ALIASES
ORDER_STATUS_EXCLUDE = re.compile(r"取消|待付款|未付款|退款|退货")
AFTER_SALE_EXCLUDE = re.compile(r"退款中|退款成功|退货中|退货成功|售后处理中|处理中|待买家退货|待商家处理")


def _read_table(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        last_error = None
        for encoding in ("utf-8-sig", "gb18030"):
            try:
                return pd.read_csv(path, encoding=encoding, dtype=str), "CSV"
            except UnicodeDecodeError as exc:
                last_error = exc
        raise ValueError(f"订单 CSV 编码无法识别：{last_error}")
    if suffix in (".xlsx", ".xls"):
        with pd.ExcelFile(path) as book:
            sheet_name = book.sheet_names[0]
            frame = pd.read_excel(book, sheet_name=sheet_name, dtype=str)
        return frame, sheet_name
    raise ValueError(f"不支持的文件格式：{suffix}")


def _clean_frame(frame):
    frame = frame.copy()
    frame.columns = [str(column).replace("\ufeff", "").strip() for column in frame.columns]
    for column in frame.columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].str.replace("\t", "", regex=False).str.strip()
    return frame


def _find_column(frame, aliases, label):
    for alias in aliases:
        if alias in frame.columns:
            return alias
    raise ValueError(f"缺少{label}字段，可识别字段：{', '.join(aliases)}")


def _normalize_id(value):
    if pd.isna(value):
        return ""
    text = str(value).replace("\t", "").strip()
    return re.sub(r"\.0$", "", text)


def _number(series):
    cleaned = series.astype(str).str.replace("\t", "", regex=False)
    cleaned = cleaned.str.replace(",", "", regex=False).str.replace("￥", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def _records(frame, columns=None):
    data = frame if columns is None else frame[columns]
    data = data.copy()
    for column in data.columns:
        if pd.api.types.is_datetime64_any_dtype(data[column]):
            data[column] = data[column].dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
    return json.loads(data.where(pd.notna(data), "").to_json(orient="records", force_ascii=False))


def analyze_profit(cost_path, order_path, start_date, end_date, ad_spend, shop_name="拼多多店铺"):
    costs, cost_sheet_name = _read_table(cost_path)
    orders, order_sheet_name = _read_table(order_path)
    costs = _clean_frame(costs)
    orders = _clean_frame(orders)

    cost_id_column = _find_column(costs, COST_ID_ALIASES, "成本表商品 ID")
    order_id_column = _find_column(orders, ORDER_ID_ALIASES, "订单表商品 ID")
    required_order = {
        "订单号", "订单状态", "商家实收金额(元)", "商品数量(件)", "订单成交时间", "售后状态"
    }
    missing_order = sorted(required_order - set(orders.columns))
    if "总成本" not in costs.columns:
        raise ValueError("成本表缺少总成本字段")
    if missing_order:
        raise ValueError(f"订单表缺少字段：{', '.join(missing_order)}")

    costs["商品id"] = costs[cost_id_column].map(_normalize_id)
    costs["总成本"] = _number(costs["总成本"])
    costs = costs[(costs["商品id"] != "") & costs["总成本"].notna()].copy()

    duplicate_rows = costs[costs.duplicated("商品id", keep=False)].copy()
    conflicting_ids = sorted(
        product_id
        for product_id, group in duplicate_rows.groupby("商品id")
        if group["总成本"].nunique(dropna=True) > 1
    )
    if conflicting_ids:
        raise ValueError(f"成本冲突，以下商品 ID 存在多个不同总成本：{', '.join(conflicting_ids)}")
    duplicate_same_ids = sorted(duplicate_rows["商品id"].unique().tolist())
    unique_costs = costs.drop_duplicates("商品id", keep="first").copy()
    cost_map = unique_costs.set_index("商品id")["总成本"]

    orders["商品id"] = orders[order_id_column].map(_normalize_id)
    orders["商家实收金额(元)"] = _number(orders["商家实收金额(元)"]).fillna(0)
    orders["商品数量(件)"] = _number(orders["商品数量(件)"]).fillna(0)
    orders["订单成交时间_dt"] = pd.to_datetime(orders["订单成交时间"], errors="coerce")

    start = pd.Timestamp(start_date)
    end_exclusive = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    in_period_mask = (orders["订单成交时间_dt"] >= start) & (orders["订单成交时间_dt"] < end_exclusive)
    period = orders[in_period_mask].copy()
    invalid_date_rows = int(orders["订单成交时间_dt"].isna().sum())
    outside_date_rows = int((orders["订单成交时间_dt"].notna() & ~in_period_mask).sum())

    order_status = period["订单状态"].fillna("")
    after_sale = period["售后状态"].fillna("")
    valid_status_mask = ~order_status.str.contains(ORDER_STATUS_EXCLUDE, regex=True)
    valid_after_sale_mask = ~after_sale.str.contains(AFTER_SALE_EXCLUDE, regex=True)
    valid_mask = valid_status_mask & valid_after_sale_mask
    excluded = period[~valid_mask].copy()
    valid_period = period[valid_mask].copy()

    matched_mask = valid_period["商品id"].isin(cost_map.index)
    matched = valid_period[matched_mask].copy()
    unmatched_detail = valid_period[~matched_mask].copy()
    matched["单件总成本"] = matched["商品id"].map(cost_map)
    matched["订单总成本"] = matched["单件总成本"] * matched["商品数量(件)"]
    matched["商品毛利"] = matched["商家实收金额(元)"] - matched["订单总成本"]

    sku_summary = matched.groupby("商品id", as_index=False).agg(
        有效订单行数=("订单号", "size"),
        有效数量=("商品数量(件)", "sum"),
        商家实收=("商家实收金额(元)", "sum"),
        单件总成本=("单件总成本", "first"),
        订单总成本=("订单总成本", "sum"),
        商品毛利=("商品毛利", "sum"),
    )
    sku_summary["毛利率"] = sku_summary["商品毛利"].div(sku_summary["商家实收"].replace(0, pd.NA)).fillna(0)

    unmatched = unmatched_detail.groupby("商品id", as_index=False).agg(
        订单行数=("订单号", "size"),
        商品数量=("商品数量(件)", "sum"),
        商家实收=("商家实收金额(元)", "sum"),
    )

    merchant_received = round(float(matched["商家实收金额(元)"].sum()), 2)
    product_cost = round(float(matched["订单总成本"].sum()), 2)
    gross_profit = round(float(matched["商品毛利"].sum()), 2)
    ad_spend = round(float(ad_spend), 2)
    detail_columns = [
        column for column in ["商品", "订单号", "订单状态", "售后状态", "订单成交时间",
                              "商品id", "商品规格", "商家实收金额(元)", "商品数量(件)"]
        if column in orders.columns
    ]
    matched_columns = detail_columns + ["单件总成本", "订单总成本", "商品毛利"]

    return {
        "shop_name": shop_name,
        "start_date": str(start.date()),
        "end_date": str((end_exclusive - pd.Timedelta(days=1)).date()),
        "cost_path": str(Path(cost_path)),
        "order_path": str(Path(order_path)),
        "cost_sheet_name": cost_sheet_name,
        "order_sheet_name": order_sheet_name,
        "ad_spend_input": ad_spend,
        "ad_spend_is_approximate": True,
        "order_rows_total": int(len(orders)),
        "period_rows": int(len(period)),
        "valid_rows": int(len(valid_period)),
        "matched_valid_rows": int(len(matched)),
        "valid_qty": float(matched["商品数量(件)"].sum()),
        "excluded_status_rows": int(len(excluded)),
        "outside_date_rows": outside_date_rows,
        "invalid_date_rows": invalid_date_rows,
        "merchant_received": merchant_received,
        "product_cost": product_cost,
        "gross_profit": gross_profit,
        "net_profit_after_ads": round(gross_profit - ad_spend, 2),
        "unmatched_rows": int(len(unmatched_detail)),
        "unmatched_qty": float(unmatched_detail["商品数量(件)"].sum()),
        "unmatched_received": round(float(unmatched_detail["商家实收金额(元)"].sum()), 2),
        "is_temporary": bool(len(unmatched_detail)),
        "cost_duplicate_same_ids": duplicate_same_ids,
        "cost_conflicting_ids": [],
        "sku_summary": _records(sku_summary.round(4)),
        "matched_order_details": _records(matched, matched_columns),
        "excluded_order_details": _records(excluded, detail_columns),
        "unmatched_order_details": _records(unmatched_detail, detail_columns),
        "unmatched_products": _records(unmatched.round(4)),
        "cost_source_rows": _records(costs),
    }


def main():
    parser = argparse.ArgumentParser(description="拼多多月度利润核算")
    parser.add_argument("--cost", required=True, help="成本 Excel 文件")
    parser.add_argument("--orders", required=True, help="订单 CSV/XLSX 文件")
    parser.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--ad-spend", required=True, type=float, help="投流总花费（元）")
    parser.add_argument("--shop-name", default="拼多多店铺", help="店铺名称")
    parser.add_argument("--output", required=True, help="分析 JSON 输出路径")
    args = parser.parse_args()
    result = analyze_profit(args.cost, args.orders, args.start, args.end, args.ad_spend, args.shop_name)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "核算状态": "暂算" if result["is_temporary"] else "完整核算",
        "商品毛利": result["gross_profit"],
        "投流花费": result["ad_spend_input"],
        "投流后净利润": result["net_profit_after_ads"],
        "未匹配订单行数": result["unmatched_rows"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
