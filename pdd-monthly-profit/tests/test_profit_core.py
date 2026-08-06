import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from profit_core import (  # noqa: E402
    calculate_totals,
    choose_time_field,
    clean_text,
    is_excluded,
    normalize_sku,
)


class ProfitCoreTests(unittest.TestCase):
    def test_prefers_payment_time(self):
        self.assertEqual(
            choose_time_field(["支付时间", "订单成交时间"]),
            "支付时间",
        )

    def test_falls_back_to_order_time(self):
        self.assertEqual(choose_time_field(["订单成交时间"]), "订单成交时间")

    def test_rejects_missing_time_field(self):
        with self.assertRaisesRegex(ValueError, "支付时间.*订单成交时间"):
            choose_time_field(["订单号", "商品规格"])

    def test_excludes_refund_cancel_and_processing(self):
        self.assertTrue(is_excluded("未发货退款成功", ""))
        self.assertTrue(is_excluded("交易关闭", ""))
        self.assertTrue(is_excluded("已收货", "售后处理中"))
        self.assertFalse(is_excluded("已收货", "无售后或售后取消"))

    def test_normalization_only_changes_safe_punctuation(self):
        self.assertEqual(
            normalize_sku(" 1袋装（刘家）精品原味南瓜子 "),
            normalize_sku("1袋装(刘家)精品原味南瓜子"),
        )
        self.assertNotEqual(
            normalize_sku("原味南瓜子300g"),
            normalize_sku("原味南瓜子350g"),
        )

    def test_accounting_formula(self):
        totals = calculate_totals(
            [{"received": 50.0, "quantity": 2, "unit_cost": 10.0}],
            18.0,
        )
        self.assertEqual(
            totals,
            {
                "received": 50.0,
                "cost": 20.0,
                "pre_ad_profit": 30.0,
                "ad_spend": 18.0,
                "final_profit": 12.0,
            },
        )

    def test_nan_is_treated_as_blank(self):
        self.assertEqual(clean_text(float("nan")), "")


if __name__ == "__main__":
    unittest.main()
