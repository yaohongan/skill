import sys
import unittest
from pathlib import Path

import pandas as pd


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from profit_core import (  # noqa: E402
    build_cost_catalog,
    choose_cost,
    parse_weight_grams,
)


class CostMatchingTests(unittest.TestCase):
    def test_parses_common_weight_units(self):
        self.assertEqual(parse_weight_grams("原味南瓜子350g"), 350)
        self.assertEqual(parse_weight_grams("原味南瓜子5kg"), 5000)
        self.assertEqual(parse_weight_grams("原味+陈皮各400克"), 800)
        self.assertEqual(parse_weight_grams("原味+陈皮各1袋共800g"), 800)

    def test_builds_catalog_from_every_sheet(self):
        frames = {
            "300克链接": pd.DataFrame(
                [{"口味": "原味瓜子", "sku名称": "原味南瓜子300g", "重量": "300g", "成本": 7, "运费": 2.8, "总成本": 9.8}]
            ),
            "西瓜子": pd.DataFrame(
                [{"口味": "奶油", "sku名称": "奶油西瓜子250g", "重量": "250g", "成本": 5, "运费": 2.8, "总成本": 7.8}]
            ),
        }
        catalog = build_cost_catalog(frames)
        self.assertEqual({row["工作表"] for row in catalog}, {"300克链接", "西瓜子"})

    def test_exact_normalized_name_wins(self):
        catalog = build_cost_catalog(
            {
                "300克链接": pd.DataFrame(
                    [{"口味": "原味", "sku名称": "1袋装（刘家）精品原味南瓜子300g", "重量": "300g", "总成本": 9.8}]
                )
            }
        )
        matched, method = choose_cost("1袋装(刘家)精品原味南瓜子300g", "", catalog)
        self.assertEqual(matched["总成本"], 9.8)
        self.assertEqual(method, "SKU名称标准化精确匹配")

    def test_unique_category_flavor_weight_can_match(self):
        catalog = build_cost_catalog(
            {
                "350克链接": pd.DataFrame(
                    [{"口味": "原味", "sku名称": "【加量款】原味南瓜子350g", "重量": "350g", "总成本": 10.8}]
                )
            }
        )
        matched, method = choose_cost("1袋装（刘家）精品原味南瓜子350g", "", catalog)
        self.assertEqual(matched["总成本"], 10.8)
        self.assertEqual(method, "品类+口味+克重唯一匹配")

    def test_ignores_platform_parent_weight_prefix(self):
        catalog = build_cost_catalog(
            {
                "350克链接": pd.DataFrame(
                    [
                        {"口味": "原味", "sku名称": "【加量畅享】原味南瓜子 1 袋 350g", "重量": "350g", "总成本": 10.8},
                        {"口味": "陈皮", "sku名称": "【加量畅享】陈皮南瓜子 1 袋 350g", "重量": "350g", "总成本": 11.5},
                    ]
                )
            }
        )
        matched, method = choose_cost(
            "400g,【加量畅享】原味南瓜子 1 袋 350g",
            "原味陈皮味可选南瓜子",
            catalog,
        )
        self.assertEqual(matched["总成本"], 10.8)
        self.assertEqual(method, "SKU名称标准化精确匹配")

    def test_ambiguous_cost_does_not_guess(self):
        catalog = build_cost_catalog(
            {
                "综合链接": pd.DataFrame(
                    [
                        {"口味": "原味", "sku名称": "原味南瓜子300g款A", "重量": "300g", "总成本": 9.8},
                        {"口味": "原味", "sku名称": "原味南瓜子300g款B", "重量": "300g", "总成本": 10.8},
                    ]
                )
            }
        )
        matched, method = choose_cost("原味南瓜子300g普通款", "", catalog)
        self.assertIsNone(matched)
        self.assertEqual(method, "候选成本冲突")

    def test_high_confidence_marketing_label_breaks_tie(self):
        catalog = build_cost_catalog(
            {
                "综合链接": pd.DataFrame(
                    [
                        {"口味": "陈皮", "sku名称": "【两袋更省】陈皮南瓜子 共 800g", "重量": "800g", "总成本": 22.1},
                        {"口味": "陈皮", "sku名称": "【口碑两袋】陈皮南瓜子 共 800g", "重量": "800g", "总成本": 20.7},
                    ]
                )
            }
        )
        matched, method = choose_cost("【口碑复购】陈皮南瓜子 2 袋共 800g", "", catalog)
        self.assertEqual(matched["总成本"], 20.7)
        self.assertEqual(method, "品类+口味+克重+名称高置信匹配")


if __name__ == "__main__":
    unittest.main()
