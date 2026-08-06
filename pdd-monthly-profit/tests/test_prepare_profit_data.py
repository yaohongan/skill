import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from profit_core import prepare_report_data  # noqa: E402


class PrepareProfitDataTests(unittest.TestCase):
    def make_files(self, directory, order_spec):
        order_path = directory / "订单.csv"
        cost_path = directory / "成本.xlsx"
        pd.DataFrame(
            [
                {
                    "商品": "测试南瓜子",
                    "订单号": "A1",
                    "订单状态": "已收货",
                    "商家实收金额(元)": "20",
                    "商品数量(件)": "1",
                    "商品id": "123456789012345678",
                    "商品规格": order_spec,
                    "售后状态": "无售后或售后取消",
                    "支付时间": "2026-07-05 12:00:00",
                },
                {
                    "商品": "测试南瓜子",
                    "订单号": "A2",
                    "订单状态": "未发货退款成功",
                    "商家实收金额(元)": "20",
                    "商品数量(件)": "1",
                    "商品id": "123456789012345678",
                    "商品规格": order_spec,
                    "售后状态": "退款成功",
                    "支付时间": "2026-07-06 12:00:00",
                },
            ]
        ).to_csv(order_path, index=False, encoding="utf-8-sig")
        with pd.ExcelWriter(cost_path) as writer:
            pd.DataFrame(
                [
                    {
                        "口味": "原味",
                        "sku名称": "原味南瓜子300g",
                        "重量": "300g",
                        "总成本": 9.8,
                    }
                ]
            ).to_excel(writer, sheet_name="300克链接", index=False)
        return order_path, cost_path

    def test_complete_data_has_reconciled_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            order_path, cost_path = self.make_files(Path(tmp), "原味南瓜子300g")
            result = prepare_report_data(
                order_path,
                cost_path,
                "2026-07-01",
                "2026-07-30",
                10,
                "测试店铺",
            )
        self.assertEqual(result["状态"], "完成")
        self.assertEqual(result["数据概况"]["有效订单数"], 1)
        self.assertEqual(result["数据概况"]["剔除订单数"], 1)
        totals = result["正式汇总"]
        self.assertEqual(totals["商家实收"], 20.0)
        self.assertEqual(totals["商品总成本"], 9.8)
        self.assertEqual(totals["推广前利润"], 10.2)
        self.assertEqual(totals["推广总花费"], 10.0)
        self.assertEqual(totals["最终盈亏"], 0.2)

    def test_unmatched_sku_pauses_formal_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            order_path, cost_path = self.make_files(Path(tmp), "原味南瓜子350g")
            result = prepare_report_data(
                order_path,
                cost_path,
                "2026-07-01",
                "2026-07-30",
                10,
                "测试店铺",
            )
        self.assertEqual(result["状态"], "等待补成本")
        self.assertNotIn("正式汇总", result)
        self.assertEqual(len(result["未匹配SKU"]), 1)
        self.assertEqual(result["未匹配SKU"][0]["商品规格"], "原味南瓜子350g")


if __name__ == "__main__":
    unittest.main()
