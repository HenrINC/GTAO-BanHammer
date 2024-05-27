import sys
import ctypes

from pathlib import Path


python_exe = sys.executable
script_path = Path(__file__).parent / "gta_banhammer" / "middleware_bot.py"
directory = script_path.parent

ctypes.windll.shell32.ShellExecuteW(
    None,
    "runas",
    python_exe,
    str(script_path),
    str(directory),
    1,
)
