import re
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


def clean_text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def strip_parent_spec_prefix(value):
    text = clean_text(value)
    return re.sub(
        r"^\s*\d+(?:\.\d+)?\s*(?:g|克|kg|千克|公斤)\s*[,，]\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )


def normalize_sku(value):
    text = strip_parent_spec_prefix(value).lower()
    text = text.translate(
        str.maketrans(
            {
                "（": "(",
                "）": ")",
                "【": "[",
                "】": "]",
                "，": ",",
                "＋": "+",
                "－": "-",
                "—": "-",
            }
        )
    )
    return re.sub(r"\s+", "", text)


def choose_time_field(columns):
    normalized = {clean_text(column): column for column in columns}
    payment_aliases = ["支付时间", "订单支付时间", "付款时间"]
    order_aliases = ["订单成交时间", "成交时间", "下单时间"]
    for alias in payment_aliases:
        if alias in normalized:
            return normalized[alias]
    for alias in order_aliases:
        if alias in normalized:
            return normalized[alias]
    raise ValueError("订单文件缺少支付时间或订单成交时间字段")


def is_excluded(order_status, aftersale_status):
    order_text = clean_text(order_status)
    aftersale_text = clean_text(aftersale_status)
    order_excluded = bool(
        re.search(r"退款成功|已取消|订单取消|交易关闭|订单关闭", order_text)
    )
    aftersale_excluded = bool(re.search(r"退款成功|处理中", aftersale_text))
    return order_excluded or aftersale_excluded


def calculate_totals(rows, ad_spend):
    received = round(sum(float(row["received"]) for row in rows), 2)
    cost = round(
        sum(float(row["quantity"]) * float(row["unit_cost"]) for row in rows),
        2,
    )
    pre_ad_profit = round(received - cost, 2)
    ad_spend = round(float(ad_spend), 2)
    return {
        "received": received,
        "cost": cost,
        "pre_ad_profit": pre_ad_profit,
        "ad_spend": ad_spend,
        "final_profit": round(pre_ad_profit - ad_spend, 2),
    }


def resolve_column(columns, aliases, required=True):
    cleaned = {clean_text(column).lower(): column for column in columns}
    for alias in aliases:
        key = clean_text(alias).lower()
        if key in cleaned:
            return cleaned[key]
    if required:
        raise ValueError(f"缺少字段：{' / '.join(aliases)}")
    return None


def parse_weight_grams(value):
    text = clean_text(value).lower()
    if not text:
        return None
    weights = [int(number) for number in re.findall(r"(\d+)\s*(?:g|克)", text)]
    weights.extend(
        int(round(float(number) * 1000))
        for number in re.findall(r"(\d+(?:\.\d+)?)\s*(?:kg|千克|公斤)", text)
    )
    weights.extend(
        int(round(float(number) * 500))
        for number in re.findall(r"(\d+(?:\.\d+)?)\s*斤", text)
    )
    chinese_weights = {
        "半斤": 250,
        "一斤": 500,
        "二斤": 1000,
        "两斤": 1000,
        "三斤": 1500,
        "四斤": 2000,
    }
    weights.extend(grams for label, grams in chinese_weights.items() if label in text)
    if not weights:
        return None
    per_flavor = re.search(
        r"各\s*(\d+(?:\.\d+)?)\s*(g|克|kg|千克|公斤)",
        text,
        flags=re.IGNORECASE,
    )
    if per_flavor and "原味" in text and "陈皮" in text:
        amount = float(per_flavor.group(1))
        grams = amount * 1000 if per_flavor.group(2).lower() in {"kg", "千克", "公斤"} else amount
        return int(round(grams * 2))
    if ("+" in text or "＋" in text) and len(weights) >= 2:
        return sum(weights)
    return max(weights)


def classify_category(*values):
    text = " ".join(clean_text(value) for value in values)
    if "西瓜子" in text:
        return "西瓜子"
    if "葵花子" in text or "葵瓜子" in text:
        return "葵花子"
    if "大白" in text:
        return "大白南瓜子"
    if "美人甲" in text:
        return "美人甲南瓜子"
    if "南瓜子" in text or "链接" in text or "综合" in text:
        return "南瓜子"
    return "未识别"


def classify_flavor(*values, category=""):
    text = " ".join(clean_text(value) for value in values)
    if "原味" in text and "陈皮" in text:
        return "原味+陈皮"
    if "陈皮" in text:
        return "陈皮"
    if "奶油" in text:
        return "奶油"
    if "椒盐" in text:
        return "椒盐"
    if "原味" in text or category == "葵花子":
        return "原味"
    return "未识别"


def _number(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = clean_text(value).replace(",", "")
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def build_cost_catalog(sheet_frames):
    catalog = []
    for sheet_name, frame in sheet_frames.items():
        if frame is None or frame.empty:
            continue
        sku_col = resolve_column(
            frame.columns,
            ["sku名称", "SKU名称", "sku", "商品规格", "规格名称"],
            required=False,
        )
        flavor_col = resolve_column(frame.columns, ["口味", "口味说明"], required=False)
        weight_col = resolve_column(frame.columns, ["重量", "克重", "规格重量"], required=False)
        total_col = resolve_column(frame.columns, ["总成本", "单件总成本"], required=False)
        cost_col = resolve_column(frame.columns, ["成本", "商品成本"], required=False)
        freight_col = resolve_column(frame.columns, ["运费", "物流成本"], required=False)
        if total_col is None and cost_col is None:
            continue
        for index, row in frame.iterrows():
            sku = clean_text(row.get(sku_col, "")) if sku_col else ""
            flavor_text = clean_text(row.get(flavor_col, "")) if flavor_col else ""
            weight_text = clean_text(row.get(weight_col, "")) if weight_col else ""
            product_cost = _number(row.get(cost_col)) if cost_col else None
            freight = _number(row.get(freight_col)) if freight_col else None
            total_cost = _number(row.get(total_col)) if total_col else None
            if total_cost is None and product_cost is not None:
                total_cost = product_cost + (freight or 0)
            if total_cost is None:
                continue
            category = classify_category(sku, flavor_text, sheet_name)
            flavor = classify_flavor(sku, flavor_text, category=category)
            weight = parse_weight_grams(sku) or parse_weight_grams(weight_text)
            if not sku and weight is None:
                continue
            catalog.append(
                {
                    "工作表": clean_text(sheet_name),
                    "行号": int(index) + 2,
                    "口味说明": flavor_text,
                    "成本SKU名称": sku,
                    "重量克数": weight,
                    "分类": category,
                    "口味": flavor,
                    "成本": round(product_cost, 2) if product_cost is not None else None,
                    "运费": round(freight, 2) if freight is not None else None,
                    "总成本": round(total_cost, 2),
                }
            )
    return catalog


def _name_match_score(order_spec, cost_sku):
    left = normalize_sku(order_spec)
    right = normalize_sku(cost_sku)
    score = SequenceMatcher(None, left, right).ratio()
    keyword_groups = [
        ("口碑", "复购"),
        ("双味", "混搭", "组合"),
        ("囤货", "更省"),
        ("实惠",),
        ("量贩",),
        ("尝鲜", "试吃"),
        ("轻享",),
        ("追剧", "宅家"),
        ("加量",),
        ("四袋",),
        ("两袋",),
        ("大袋",),
    ]
    for group in keyword_groups:
        left_has = any(word in order_spec for word in group)
        right_has = any(word in cost_sku for word in group)
        if left_has and right_has:
            score += 0.12
        elif left_has != right_has:
            score -= 0.04
    return score


def choose_cost(order_spec, product_name, catalog):
    spec = strip_parent_spec_prefix(order_spec)
    product = clean_text(product_name)
    normalized = normalize_sku(spec)
    exact = [
        row
        for row in catalog
        if row["成本SKU名称"] and normalize_sku(row["成本SKU名称"]) == normalized
    ]
    if exact:
        costs = {row["总成本"] for row in exact}
        if len(costs) == 1:
            return exact[0], "SKU名称标准化精确匹配"
        return None, "SKU重复成本冲突"

    category = classify_category(spec)
    if category == "未识别":
        category = classify_category(product)
    flavor = classify_flavor(spec, category=category)
    if flavor == "未识别":
        flavor = classify_flavor(product, category=category)
    weight = parse_weight_grams(spec) or parse_weight_grams(product)
    candidates = [row for row in catalog if row["分类"] == category]
    if weight is not None:
        candidates = [row for row in candidates if row["重量克数"] == weight]
    if flavor != "未识别":
        flavor_candidates = [row for row in candidates if row["口味"] == flavor]
        if flavor_candidates:
            candidates = flavor_candidates
    if len(candidates) == 1:
        return candidates[0], "品类+口味+克重唯一匹配"
    if candidates and len({row["总成本"] for row in candidates}) == 1:
        return candidates[0], "品类+口味+克重同成本匹配"
    if candidates:
        ranked = sorted(
            ((_name_match_score(spec, row["成本SKU名称"]), row) for row in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        best_score = ranked[0][0]
        second_score = ranked[1][0] if len(ranked) > 1 else 0
        if best_score >= 0.58 and best_score - second_score >= 0.05:
            return ranked[0][1], "品类+口味+克重+名称高置信匹配"
        return None, "候选成本冲突"
    return None, "无匹配"


ORDER_ALIASES = {
    "订单号": ["订单号", "订单编号", "主订单号"],
    "商品ID": ["商品id", "商品ID", "商品编号"],
    "商品名称": ["商品", "商品名称", "商品标题"],
    "商品规格": ["商品规格", "规格名称", "SKU名称", "sku名称"],
    "商品数量": ["商品数量(件)", "商品数量", "数量", "购买数量"],
    "商家实收": ["商家实收金额(元)", "商家实收金额", "商家实收"],
    "订单状态": ["订单状态", "交易状态"],
    "售后状态": ["售后状态", "退款状态"],
}


def _read_csv(path):
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as error:
            last_error = error
    raise ValueError(f"无法识别订单CSV编码：{last_error}")


def read_orders(path):
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return _read_csv(source), "CSV"
    if suffix not in {".xlsx", ".xls"}:
        raise ValueError("订单文件仅支持 CSV、XLS 或 XLSX")
    sheets = pd.read_excel(source, sheet_name=None, dtype=str)
    for sheet_name, frame in sheets.items():
        lowered = {clean_text(column).lower() for column in frame.columns}
        has_spec = any(alias.lower() in lowered for alias in ORDER_ALIASES["商品规格"])
        has_received = any(alias.lower() in lowered for alias in ORDER_ALIASES["商家实收"])
        if has_spec and has_received:
            return frame, f"Excel工作表：{sheet_name}"
    raise ValueError("订单Excel中没有找到包含商品规格和商家实收的工作表")


def read_cost_workbook(path):
    source = Path(path)
    if source.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("成本文件仅支持 XLS 或 XLSX")
    return pd.read_excel(source, sheet_name=None, dtype=str)


def exclusion_reason(order_status, aftersale_status):
    order_text = clean_text(order_status)
    aftersale_text = clean_text(aftersale_status)
    if re.search(r"退款成功|已取消|订单取消|交易关闭|订单关闭", order_text):
        return "退款/取消"
    if re.search(r"退款成功", aftersale_text):
        return "退款/取消"
    if re.search(r"处理中", aftersale_text):
        return "售后处理中"
    return ""


def _clean_frame(frame):
    cleaned = frame.copy().fillna("")
    for column in cleaned.columns:
        cleaned[column] = cleaned[column].map(clean_text)
    return cleaned


def prepare_report_data(
    order_path,
    cost_path,
    start_date,
    end_date,
    ad_spend,
    store_name,
):
    orders, order_source = read_orders(order_path)
    orders = _clean_frame(orders)
    columns = {}
    for key, aliases in ORDER_ALIASES.items():
        columns[key] = resolve_column(
            orders.columns,
            aliases,
            required=key not in {"售后状态", "商品ID", "商品名称"},
        )
    time_field = choose_time_field(orders.columns)
    orders["__时间"] = pd.to_datetime(orders[time_field], errors="coerce")
    invalid_time = orders[orders[time_field].ne("") & orders["__时间"].isna()]
    if not invalid_time.empty:
        raise ValueError(f"有{len(invalid_time)}笔订单的时间无法解析")
    start = pd.Timestamp(start_date)
    end_exclusive = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    period = orders[(orders["__时间"] >= start) & (orders["__时间"] < end_exclusive)].copy()

    status_col = columns["订单状态"]
    aftersale_col = columns["售后状态"]
    period["__剔除原因"] = period.apply(
        lambda row: exclusion_reason(
            row.get(status_col, ""),
            row.get(aftersale_col, "") if aftersale_col else "",
        ),
        axis=1,
    )
    valid = period[period["__剔除原因"].eq("")].copy()
    excluded = period[period["__剔除原因"].ne("")].copy()

    quantity_col = columns["商品数量"]
    received_col = columns["商家实收"]
    for frame, label in ((valid, "有效订单"), (excluded, "剔除订单")):
        frame["__商品数量"] = pd.to_numeric(frame[quantity_col], errors="coerce")
        frame["__商家实收"] = pd.to_numeric(frame[received_col], errors="coerce")
        invalid = frame[frame["__商品数量"].isna() | frame["__商家实收"].isna()]
        if not invalid.empty:
            raise ValueError(f"{label}中有{len(invalid)}笔订单的数量或商家实收无法解析")

    catalog = build_cost_catalog(read_cost_workbook(cost_path))
    if not catalog:
        raise ValueError("成本表中没有找到可用的SKU总成本")

    product_id_col = columns["商品ID"]
    product_name_col = columns["商品名称"]
    spec_col = columns["商品规格"]
    order_number_col = columns["订单号"]
    mapping = []
    lookup = {}
    group_fields = [spec_col]
    if product_id_col:
        group_fields.insert(0, product_id_col)
    grouped = valid.groupby(group_fields, dropna=False, sort=False)
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        product_id = clean_text(group_key[0]) if product_id_col else ""
        spec = clean_text(group_key[-1])
        product_name = clean_text(group[product_name_col].iloc[0]) if product_name_col else ""
        matched, method = choose_cost(spec, product_name, catalog)
        item = {
            "商品ID": product_id,
            "商品名称": product_name,
            "商品规格": spec,
            "有效订单数": int(len(group)),
            "商品件数": round(float(group["__商品数量"].sum()), 4),
            "商家实收": round(float(group["__商家实收"].sum()), 2),
            "匹配状态": "已匹配" if matched else "未匹配",
            "匹配方式": method,
            "成本工作表": matched["工作表"] if matched else "",
            "成本SKU名称": matched["成本SKU名称"] if matched else "",
            "单件总成本": matched["总成本"] if matched else None,
        }
        mapping.append(item)
        lookup[(product_id, spec)] = item

    details = []
    for index, (_, row) in enumerate(valid.iterrows(), start=1):
        product_id = clean_text(row.get(product_id_col, "")) if product_id_col else ""
        spec = clean_text(row[spec_col])
        item = lookup[(product_id, spec)]
        details.append(
            {
                "序号": index,
                "订单号": clean_text(row[order_number_col]),
                "商品ID": product_id,
                "订单时间": row["__时间"].strftime("%Y-%m-%d %H:%M:%S"),
                "订单状态": clean_text(row[status_col]),
                "售后状态": clean_text(row.get(aftersale_col, "")) if aftersale_col else "",
                "商品名称": clean_text(row.get(product_name_col, "")) if product_name_col else "",
                "商品规格": spec,
                "商品数量": round(float(row["__商品数量"]), 4),
                "商家实收": round(float(row["__商家实收"]), 2),
                "成本工作表": item["成本工作表"],
                "成本SKU名称": item["成本SKU名称"],
                "单件总成本": item["单件总成本"],
                "匹配方式": item["匹配方式"],
            }
        )

    excluded_rows = []
    for index, (_, row) in enumerate(excluded.iterrows(), start=1):
        excluded_rows.append(
            {
                "序号": index,
                "订单号": clean_text(row[order_number_col]),
                "商品ID": clean_text(row.get(product_id_col, "")) if product_id_col else "",
                "订单时间": row["__时间"].strftime("%Y-%m-%d %H:%M:%S"),
                "订单状态": clean_text(row[status_col]),
                "售后状态": clean_text(row.get(aftersale_col, "")) if aftersale_col else "",
                "商品名称": clean_text(row.get(product_name_col, "")) if product_name_col else "",
                "商品规格": clean_text(row[spec_col]),
                "商品数量": round(float(row["__商品数量"]), 4),
                "商家实收": round(float(row["__商家实收"]), 2),
                "剔除原因": clean_text(row["__剔除原因"]),
            }
        )

    unmatched = []
    seen = set()
    for item in mapping:
        if item["匹配状态"] == "已匹配":
            continue
        key = normalize_sku(item["商品规格"])
        if key in seen:
            continue
        seen.add(key)
        unmatched.append(
            {
                "商品ID": item["商品ID"],
                "商品名称": item["商品名称"],
                "商品规格": item["商品规格"],
                "有效订单数": item["有效订单数"],
                "商品件数": item["商品件数"],
                "商家实收": item["商家实收"],
                "未匹配原因": item["匹配方式"],
            }
        )
    unmatched.sort(key=lambda row: (row["商品规格"], row["商品ID"]))

    refund_count = sum(row["剔除原因"] == "退款/取消" for row in excluded_rows)
    processing_count = sum(row["剔除原因"] == "售后处理中" for row in excluded_rows)
    result = {
        "状态": "等待补成本" if unmatched else "完成",
        "参数": {
            "店铺名称": clean_text(store_name) or "拼多多店铺",
            "统计开始日期": str(pd.Timestamp(start_date).date()),
            "统计结束日期": str(pd.Timestamp(end_date).date()),
            "时间字段": time_field,
            "时间口径说明": "优先使用支付时间" if "支付" in time_field or "付款" in time_field else "订单文件无支付时间，使用订单成交时间",
            "推广总花费": round(float(ad_spend), 2),
            "订单文件": str(Path(order_path).resolve()),
            "订单数据来源": order_source,
            "成本文件": str(Path(cost_path).resolve()),
        },
        "数据概况": {
            "区间订单数": int(len(period)),
            "有效订单数": int(len(valid)),
            "退款取消数": int(refund_count),
            "售后处理中数": int(processing_count),
            "剔除订单数": int(len(excluded)),
            "唯一规格映射数": int(len(mapping)),
            "未匹配规格数": int(len(unmatched)),
        },
        "成本标准": catalog,
        "SKU映射": mapping,
        "订单明细": details,
        "剔除订单": excluded_rows,
        "未匹配SKU": unmatched,
    }
    if not unmatched:
        total_rows = [
            {
                "received": row["商家实收"],
                "quantity": row["商品数量"],
                "unit_cost": row["单件总成本"],
            }
            for row in details
        ]
        totals = calculate_totals(total_rows, ad_spend)
        result["正式汇总"] = {
            "商家实收": totals["received"],
            "商品总成本": totals["cost"],
            "推广前利润": totals["pre_ad_profit"],
            "推广总花费": totals["ad_spend"],
            "最终盈亏": totals["final_profit"],
            "净利润率": round(totals["final_profit"] / totals["received"], 8) if totals["received"] else None,
        }
    return result
