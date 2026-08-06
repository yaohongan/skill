import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_skill_is_chinese_discoverable_and_contains_accounting_guardrails(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", text)
        self.assertRegex(text, r"description:\s*Use when")
        self.assertGreater(len(re.findall(r"[\u4e00-\u9fff]", text)), 250)
        for phrase in ["投流截图", "总花费", "商家实收金额", "商品数量", "退款", "退货", "未匹配", "暂算", "成本冲突", "客户核对版"]:
            self.assertIn(phrase, text)
        self.assertIn("scripts/analyze_profit.py", text)
        self.assertIn("scripts/build_report.mjs", text)
        self.assertIn("references/字段与口径.md", text)

    def test_reference_exists_and_documents_required_fields(self):
        reference = (SKILL_DIR / "references" / "字段与口径.md").read_text(encoding="utf-8")
        for phrase in ["商品id", "总成本", "订单状态", "售后状态", "订单成交时间", "商家实收金额(元)", "商品数量(件)"]:
            self.assertIn(phrase, reference)


if __name__ == "__main__":
    unittest.main()
