import importlib
import json
import sys


MINIMUM_PYTHON = (3, 10)
REQUIRED_MODULES = ("pandas", "openpyxl", "xlrd")


def check_environment():
    missing = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    python_ok = sys.version_info >= MINIMUM_PYTHON
    return {
        "状态": "通过" if python_ok and not missing else "未通过",
        "Python版本": ".".join(map(str, sys.version_info[:3])),
        "Python版本符合要求": python_ok,
        "缺少依赖": missing,
        "安装命令": f'"{sys.executable}" -m pip install -r requirements.txt',
    }


def main():
    result = check_environment()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["状态"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
