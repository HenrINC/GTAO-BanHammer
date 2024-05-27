from pathlib import Path

from pprint import pprint
import psutil

import time


def get_process_by_executable_path(path: str) -> psutil.Process:
    path = path.lower().replace("/", "\\")
    for proc in psutil.process_iter(["exe"]):
        if (
            proc_path := proc.info["exe"]
        ) is not None and proc_path.lower() == path.lower():
            return proc
    raise RuntimeError("No process found")


while True:
    process = get_process_by_executable_path("J:/Epic/GTAV/GTA5.exe")
    pprint(
        [
            mmap
            for mmap in process.memory_maps()
            if Path(mmap.path).parent
            == Path(R"C:\Users\henri\AppData\Roaming\Stand\Bin\Temp")
        ]
    )
    time.sleep(1)
