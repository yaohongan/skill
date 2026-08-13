import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


INCLUDED_FILES = (
    "SKILL.md",
    "requirements.txt",
    "agents/openai.yaml",
    "references/field-mapping.md",
    "scripts/build_profit_report.py",
    "scripts/check_environment.py",
    "scripts/prepare_profit_data.py",
    "scripts/profit_core.py",
)


def build_package(skill_root, output_path):
    root = Path(skill_root).resolve()
    output = Path(output_path).resolve()
    missing = [relative for relative in INCLUDED_FILES if not (root / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"技能文件不完整：{', '.join(missing)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for relative in INCLUDED_FILES:
            archive.write(root / relative, arcname=relative)
    return output


def build_parser():
    parser = argparse.ArgumentParser(description="生成可上传到WorkBuddy的技能ZIP")
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", required=True)
    return parser


def main():
    args = build_parser().parse_args()
    output = build_package(args.skill_root, args.output)
    print(f"WorkBuddy技能包已生成：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
