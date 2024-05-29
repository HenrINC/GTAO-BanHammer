import time
import struct
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
    PRESENCE_DATA_PATTERN = "48 8B 0D ?? ?? ?? ?? 44 8B 4B 60"
    PRESENCE_DATA_MASK = "xxx????xxx"
    WORLD_PATTERN = "48 8B 0D ?? ?? ?? ?? 48 8B 01 FF 90 ?? ?? ?? ?? 48 8B 0D"
    WORLD_MASK = "xxx????xxxxx????xxx"

    def __init__(self, game_folder) -> None:
        self.game_folder: Path = Path(game_folder)
        self.executable_path: Path = self.game_folder / "GTA5.exe"
        self.start_script_path: Path = self.game_folder / "PlayGTAV.exe"
        self.stand_instance: ...
        self.proces: Optional[psutil.Process] = None
        self.pm: Optional[pymem.Pymem] = None
        self.module: Optional[pymem.process.Module] = None
        self.module_base: Optional[int] = None
        self.module_size: Optional[int] = None

    @property
    def is_in_game(self):
        """
        Uses Pymem to analyse the games memory and check if the player is in game.
        """
        if not (self.is_running and self.pm):
            return False

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

    def get_presence_data(self):
        """
        Gets the presence data of the player.
        Currently returns the address, may return an actual object in the future.
        """
        self.ensure_running()
        address = self.pattern_scan(self.PRESENCE_DATA_PATTERN, self.PRESENCE_DATA_MASK)
        if address:

            ajusted_address = address + 3
            offset = self.pm.read_int(ajusted_address)
            presence_data_address = ajusted_address + offset + 4
            return presence_data_address
        return None

    def _get_world_address(self):
        """
        Gets the world address.
        """
        self.ensure_running()
        return self.pattern_scan(self.WORLD_PATTERN, self.WORLD_MASK)

    def _get_user_net_player_address(self):
        """
        Gets the user net player address.
        """
        self.ensure_running()
        return self._get_world_address() + 0x8

    def get_user_net_player(self):
        """
        Gets the user net player.
        Seems to return nonsense
        """
        self.ensure_running()
        address = self._get_user_net_player_address()
        raw_data = self.pm.read_bytes(address, 0x0CB8)
        player_info_dict = {}
        player_info_dict["m_InternalIP"] = struct.unpack_from("I", raw_data, 0x0034)[0]
        player_info_dict["m_InternalPort"] = struct.unpack_from("H", raw_data, 0x0038)[
            0
        ]
        player_info_dict["m_RelayIP"] = struct.unpack_from("I", raw_data, 0x003C)[0]
        player_info_dict["m_RelayPort"] = struct.unpack_from("H", raw_data, 0x0040)[0]
        player_info_dict["m_ExternalIP"] = struct.unpack_from("I", raw_data, 0x0044)[0]
        player_info_dict["m_ExternalPort"] = struct.unpack_from("H", raw_data, 0x0048)[
            0
        ]
        player_info_dict["iRockstarID"] = struct.unpack_from("I", raw_data, 0x0068)[0]
        player_info_dict["m_Name"] = (
            raw_data[0x007C : 0x007C + 20]
            .decode("utf-8", errors="ignore")
            .strip("\x00")
        )
        player_info_dict["fSwimSpeed"] = struct.unpack_from("f", raw_data, 0x0148)[0]
        player_info_dict["fWalkSpeed"] = struct.unpack_from("f", raw_data, 0x014C)[0]
        player_info_dict["fStealthWalkSpeed"] = struct.unpack_from(
            "f", raw_data, 0x0168
        )[0]
        player_info_dict["m_EntityPtr"] = struct.unpack_from("Q", raw_data, 0x01C8)[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["iFrameFlags"] = struct.unpack_from("I", raw_data, 0x01F8)[0]
        player_info_dict["ioConstantLightEffectPtr"] = struct.unpack_from(
            "Q", raw_data, 0x0240
        )[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["fwWantedLightEffectPtr"] = struct.unpack_from(
            "Q", raw_data, 0x0258
        )[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["pCPlayerPedTargeting"] = struct.unpack_from(
            "Q", raw_data, 0x0280
        )[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["m_EntityPtr2"] = struct.unpack_from("Q", raw_data, 0x0288)[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["bIsWanted"] = struct.unpack_from("?", raw_data, 0x0810)[0]
        player_info_dict["iFakeWantedLevel"] = struct.unpack_from(
            "I", raw_data, 0x0844
        )[0]
        player_info_dict["iWantedLevel"] = struct.unpack_from("I", raw_data, 0x0848)[0]
        player_info_dict["pCWantedIncident"] = struct.unpack_from(
            "Q", raw_data, 0x0858
        )[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["pCTacticalAnalysis"] = struct.unpack_from(
            "Q", raw_data, 0x0B88
        )[
            0
        ]  # Assuming 64-bit pointer
        player_info_dict["fStamina"] = struct.unpack_from("f", raw_data, 0x0CB0)[0]
        player_info_dict["fMaxStamina"] = struct.unpack_from("f", raw_data, 0x0CB4)[0]
        return player_info_dict

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
    import ctypes, sys, traceback

    # if not ctypes.windll.shell32.IsUserAnAdmin():
    #     # Re-launch the script with admin rights
    #     ctypes.windll.shell32.ShellExecuteW(
    #         None,
    #         "runas",
    #         sys.executable,
    #         "gta.py",
    #         str(Path(__file__).parent),
    #         1,
    #     )
    #     sys.exit()

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
