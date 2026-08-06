import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from analyze_profit import analyze_profit  # noqa: E402


class AnalyzeProfitTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_costs(self, rows):
        path = self.root / "成本表.xlsx"
        pd.DataFrame(rows).to_excel(path, index=False)
        return path

    def write_orders(self, rows, suffix=".csv"):
        path = self.root / f"订单{suffix}"
        frame = pd.DataFrame(rows)
        if suffix == ".csv":
            frame.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            frame.to_excel(path, index=False)
        return path

    def test_quantity_date_status_and_unmatched_temporary_result(self):
        costs = self.write_costs([
            {"商品id": "1001", "总成本": 10},
            {"商品id": "1001", "总成本": 10},
        ])
        orders = self.write_orders([
            self.order("A", "1001", "2026-07-01 00:00:00", 30, 2),
            self.order("B", "1001", "2026-07-30 23:59:59", 18, 1),
            self.order("C", "1001", "2026-07-31 00:00:00", 99, 1),
            self.order("D", "1001", "2026-07-15 12:00:00", 20, 1, order_status="已退款"),
            self.order("E", "1001", "2026-07-15 12:00:00", 20, 1, after_sale="退款成功"),
            self.order("F", "9999", "2026-07-10 12:00:00", 25, 1),
        ])

        result = analyze_profit(
            cost_path=costs,
            order_path=orders,
            start_date="2026-07-01",
            end_date="2026-07-30",
            ad_spend=12,
            shop_name="测试店铺",
        )

        self.assertEqual(result["valid_rows"], 3)
        self.assertEqual(result["matched_valid_rows"], 2)
        self.assertEqual(result["valid_qty"], 3)
        self.assertEqual(result["merchant_received"], 48)
        self.assertEqual(result["product_cost"], 30)
        self.assertEqual(result["gross_profit"], 18)
        self.assertEqual(result["net_profit_after_ads"], 6)
        self.assertEqual(result["excluded_status_rows"], 2)
        self.assertEqual(result["outside_date_rows"], 1)
        self.assertEqual(result["unmatched_rows"], 1)
        self.assertEqual(result["unmatched_qty"], 1)
        self.assertEqual(result["unmatched_received"], 25)
        self.assertTrue(result["is_temporary"])
        self.assertEqual(result["cost_duplicate_same_ids"], ["1001"])

    def test_conflicting_duplicate_costs_raise_clear_error(self):
        costs = self.write_costs([
            {"商品ID": "1001", "总成本": 10},
            {"商品ID": "1001", "总成本": 11},
        ])
        orders = self.write_orders([self.order("A", "1001", "2026-07-05", 20, 1)])

        with self.assertRaisesRegex(ValueError, "成本冲突.*1001"):
            analyze_profit(costs, orders, "2026-07-01", "2026-07-30", 0, "测试店铺")

    def test_accepts_excel_orders_and_json_serializable_result(self):
        costs = self.write_costs([{"商品Id": 1001, "总成本": 10}])
        orders = self.write_orders(
            [self.order("A", "1001.0", "2026-07-05", 20, 1)], suffix=".xlsx"
        )

        result = analyze_profit(costs, orders, "2026-07-01", "2026-07-30", 3.5, "测试店铺")

        self.assertEqual(result["net_profit_after_ads"], 6.5)
        json.dumps(result, ensure_ascii=False)

    @staticmethod
    def order(order_id, product_id, date, received, quantity, order_status="已收货", after_sale="无售后或售后取消"):
        return {
            "商品": f"商品{product_id}",
            "订单号": order_id,
            "订单状态": order_status,
            "商家实收金额(元)": received,
            "商品数量(件)": quantity,
            "订单成交时间": date,
            "商品id": product_id,
            "商品规格": "默认",
            "售后状态": after_sale,
        }


if __name__ == "__main__":
    unittest.main()
