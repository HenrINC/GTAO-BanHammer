import time
import subprocess
from pathlib import Path
from typing import Optional

import re
import pymem
import psutil


def get_process_by_executable_path(path: str) -> psutil.Process:
    path = str(path).lower().replace("/", "\\")
    for proc in psutil.process_iter(["exe"]):
        if (
            proc_path := proc.info["exe"]
        ) is not None and proc_path.lower() == path.lower():
            return proc
    raise RuntimeError("No process found")


class GTA:
    """
    Comprhesive wrapper around the GTA process.
    Used to monitor the game and interact with it.

    Thanks to https://github.com/YimMenu/ for the memory patterns.
    """

    GAME_STATE_PATTERN = "83 3D ?? ?? ?? ?? ?? 75 17 8B 43 20 25"
    GAME_STATE_MASK = "xx?????xxxxx"
    IS_SESSION_STARTED_PATTERN = "40 38 35 ?? ?? ?? ?? 75 0E 4C 8B C3 49 8B D7 49 8B CE"
    IS_SESSION_STARTED_MASK = "xxx????xxxxxxxxxxx"

    def __init__(self, game_folder) -> None:
        self.game_folder: Path = Path(game_folder)
        self.executable_path: Path = self.game_folder / "GTA5.exe"
        self.start_script_path: Path = self.game_folder / "PlayGTAV.exe"
        self.stand_instance: ...
        self.process: Optional[psutil.Process] = None
        self.pm: Optional[pymem.Pymem] = None
        self.module: Optional[pymem.process.Module] = None
        self.module_base: Optional[int] = None
        self.module_size: Optional[int] = None

    @property
    def is_running(self):
        """
        Checks if the game is running.
        """
        if not self.process:
            return False
        return self.process.is_running()

    @property
    def needs_restart(self):
        """
        Checks if the game is in a specific state that requires a restart,
        will return False if not running.

        """
        if not self.is_running:
            return False
        return self.process.status() != psutil.STATUS_RUNNING

    @property
    def is_stable(self):
        """
        Checks if the game is in a stable state.
        """
        self.ensure_running()
        return self.get_game_state() == 0 and self.is_session_started

    def ensure_stable(self):
        """
        Ensures that the game is in a stable state.
        """
        while not self.is_stable:
            if self.needs_restart:
                self.stop()
                self.start()
            time.sleep(0.1)

    def attach_or_start(self):
        """
        Attaches to the GTA process if it is running, otherwise starts it.
        """
        try:
            self.attach()
        except RuntimeError:
            self.start()

    def attach(self):
        """
        Attaches to the GTA process.
        """
        if self.needs_restart:
            raise RuntimeError("Game needs restart")
        self.process = get_process_by_executable_path(self.executable_path)
        self.pm = pymem.Pymem()
        self.pm.open_process_from_id(self.process.pid)
        self.module = pymem.process.module_from_name(
            self.pm.process_handle, self.executable_path.name
        )
        self.module_base = self.module.lpBaseOfDll
        self.module_size = self.module.SizeOfImage

    def start(self):
        """
        Starts the GTA process. And attaches to it.
        """
        if self.needs_restart:
            self.stop()
        subprocess.Popen([self.start_script_path], cwd=self.game_folder)
        start = time.time()
        # If you're not using the R* launcher, the game launchging process took up to 2 mins in testing
        while start + 120 > time.time():
            try:
                self.attach()
                break
            except RuntimeError:
                pass

    def stop(self):
        """
        Stops the GTA process.
        """
        self.process.terminate()

    def ensure_running(self):
        """
        Ensures that the game is running.
        """
        if not self.is_running:
            self.attach_or_start()

    def pattern_scan(self, pattern: str, mask: str) -> Optional[int]:
        """
        Scans the memory for the given pattern and mask.
        """
        module_bytes = self.pm.read_bytes(self.module_base, self.module_size)
        mask_pattern = "".join(
            [
                "." if m == "?" else "\\x%02x" % int(b, 16)
                for b, m in zip(pattern.split(), mask)
            ]
        )

        match = re.search(mask_pattern.encode(), module_bytes)
        if match:
            return self.module_base + match.start()
        return None

    def get_game_state(self):
        """
        Gets the session status of the game.
        """
        self.ensure_running()
        address = self.pattern_scan(self.GAME_STATE_PATTERN, self.GAME_STATE_MASK)
        if address:
            adjusted_address = address + 2
            offset = self.pm.read_int(adjusted_address)
            offested_address = adjusted_address + offset + 4
            game_state_address = offested_address + 1
            return self.pm.read_int(game_state_address)
        return None

    @property
    def is_session_started(self) -> bool:
        """
        Checks if the session has started by scanning the memory.
        """
        self.ensure_running()
        address = self.pattern_scan(
            self.IS_SESSION_STARTED_PATTERN, self.IS_SESSION_STARTED_MASK
        )
        if address:
            adjusted_address = address + 3
            offset = self.pm.read_int(adjusted_address)
            session_started_address = adjusted_address + offset + 4
            return self.pm.read_bool(session_started_address)
        return False


if __name__ == "__main__":
    import traceback

    try:
        gta = GTA("J:/Epic/GTAV/")
        gta.attach_or_start()
        while True:
            print("Game status", gta.get_game_state())
            print("Is session loaded", gta.is_session_started)
            time.sleep(1)
    except Exception as e:
        traceback.print_exc()
        breakpoint()
