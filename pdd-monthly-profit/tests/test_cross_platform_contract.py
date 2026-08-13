import unittest
import importlib.util
import tempfile
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent


class CrossPlatformContractTests(unittest.TestCase):
    def test_skill_has_only_portable_runtime_dependencies(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for value in ["artifact-tool", "Windows Junction", "codex_app__", "build_profit_report.mjs"]:
            self.assertNotIn(value, skill)
        self.assertIn("build_profit_report.py", skill)
        self.assertIn("check_environment.py", skill)

    def test_installation_docs_cover_all_clients_and_operating_systems(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for value in ["Windows", "macOS", "Codex", "Claude Code", "WorkBuddy"]:
            self.assertIn(value, readme)

    def test_portable_files_exist(self):
        for relative in ["requirements.txt", "scripts/build_profit_report.py", "scripts/check_environment.py", "scripts/package_workbuddy_skill.py"]:
            self.assertTrue((SKILL_ROOT / relative).is_file(), relative)

    def test_workbuddy_package_has_skill_at_zip_root(self):
        script = SKILL_ROOT / "scripts" / "package_workbuddy_skill.py"
        spec = importlib.util.spec_from_file_location("package_workbuddy_skill", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pdd-monthly-profit.zip"
            module.build_package(SKILL_ROOT, output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
            self.assertIn("SKILL.md", names)
            self.assertIn("requirements.txt", names)
            self.assertIn("scripts/profit_core.py", names)
            self.assertFalse(any("__pycache__" in name or name.startswith("tests/") for name in names))

    def test_ci_covers_windows_macos_and_linux(self):
        source = (REPO_ROOT / ".github" / "workflows" / "pdd-monthly-profit.yml").read_text(encoding="utf-8")
        for runner in ["windows-latest", "macos-latest", "ubuntu-latest"]:
            self.assertIn(runner, source)


if __name__ == "__main__":
    unittest.main()
