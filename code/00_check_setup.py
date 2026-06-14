"""
00_check_setup.py
Run this first. It checks your Python version, reports which required
packages are installed, makes sure the folder structure exists, and
confirms config.py loads. No internet needed.

Usage, from the project root:
    python code/00_check_setup.py
"""

import sys
from pathlib import Path

REQUIRED = [
    "pandas", "numpy", "matplotlib", "statsmodels",
    "arch", "pandas_datareader", "openpyxl", "scipy",
]


def check_python():
    print(f"Python {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("  warning: Python 3.10 or newer is recommended")
    print()


def check_packages():
    print("Packages")
    missing = []
    for name in REQUIRED:
        try:
            mod = __import__(name)
            version = getattr(mod, "__version__", "installed")
            print(f"  ok       {name:18s} {version}")
        except ImportError:
            print(f"  MISSING  {name}")
            missing.append(name)
    print()
    if missing:
        print("Install what is missing with:")
        print("  pip install -r requirements.txt")
        print()
    return missing


def check_folders():
    print("Folders")
    root = Path(__file__).resolve().parent.parent
    for sub in ["data/raw", "data/processed", "figures", "tables", "output"]:
        p = root / sub
        p.mkdir(parents=True, exist_ok=True)
        print(f"  ok       {sub}")
    print()


def check_config():
    print("Config")
    try:
        import config
        print("  ok       config.py loaded")
        print(f"  cutoff   {config.DATA_CUTOFF}")
        print(f"  episodes {len(config.TRIGGERS)}")
        if config.EIA_API_KEY:
            print("  ok       EIA_API_KEY is set")
        else:
            print("  MISSING  EIA_API_KEY (oil prices come from EIA). Get a free key at")
            print("           https://www.eia.gov/opendata/register.php then run:")
            print("           export EIA_API_KEY=your_key_here")
    except Exception as e:
        print(f"  problem loading config.py: {e}")
    print()


if __name__ == "__main__":
    # make config.py (in the same folder) importable
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    check_python()
    missing = check_packages()
    check_folders()
    check_config()
    if not missing:
        print("Setup looks good.")
        print("Next: download the GPR files into data/raw, write their filenames")
        print("into config.py, then run the Phase 1 to 2 data script.")
    else:
        print("Install the missing packages, then run this again.")
