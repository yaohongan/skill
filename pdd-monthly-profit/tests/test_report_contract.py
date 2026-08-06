import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUILDER = SKILL_ROOT / "scripts" / "build_profit_report.mjs"


class ReportContractTests(unittest.TestCase):
    def test_builder_contains_all_required_chinese_sheets(self):
        source = BUILDER.read_text(encoding="utf-8")
        for sheet in [
            "客户汇报",
            "SKU汇总",
            "订单明细",
            "成本标准",
            "剔除订单",
            "未匹配SKU",
            "参数与来源",
            "核对检查",
        ]:
            self.assertIn(f'worksheets.add("{sheet}")', source)

    def test_builder_shows_ad_spend_as_a_separate_deduction(self):
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn("减：推广总花费", source)
        self.assertIn("#REF!|#DIV/0!|#VALUE!|#NAME", source)


if __name__ == "__main__":
    unittest.main()
