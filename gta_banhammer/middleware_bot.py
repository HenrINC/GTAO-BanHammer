import time
import ctypes
from typing import Optional

import psutil
from pywinauto.application import Application, WindowSpecification

from gta_banhammer.tables import Player, BannedPlayer, Detection
from gta_banhammer.enums import RoleEnum
from gta_banhammer.middleware_lib import BanHammerMiddleware, STAND_ROOT


class BanHammerServerMiddleware(BanHammerMiddleware):
    def __init__(self):
        super().__init__()
        self.stand_path: Optional[str] = None
        self.stand_app: Optional[Application] = None
        self.stand_window: Optional[WindowSpecification] = None

        self.gta_process: Optional[psutil.Process] = None

    def init_stand(self):
        self.stand_path = self.config["stand"]["executable_path"]

        try:
            stand_process = self.get_process_by_executable_path(self.stand_path)
            print("Attach to existing Stand instance.")
            self.stand_app = Application().connect(process=stand_process.pid)
        except RuntimeError:
            print("Start new Stand instance and attaching to it.")
            time.sleep(1)
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", self.stand_path, None, None, 1
            )
            self.init_stand()

        start_time = time.time()

        while (
            window_number := len(
                [window for window in self.stand_app.windows() if window.is_visible()]
            )
        ) != 1:
            time.sleep(0.1)
            if time.time() - start_time > 10:
                if window_number > 1:
                    raise RuntimeError("More than one window is visible")
                raise RuntimeError("No visible windows")
        print("Stand ready.")
        self.stand_window = self.stand_app.top_window()

    def ensure_stand_running(self):
        if self.stand_app is None or not self.stand_app.is_process_running():
            self.init_stand()

    def run_gta_from_stand(self):
        self.ensure_stand_running()
        run_buttons = [
            control
            for control in self.stand_window.children()
            if control.is_visible()
            and control.control_type() == "System.Windows.Forms.Button"
            and control.texts()[0] == "Launch"
        ]
        if len_run_buttons := len(run_buttons) != 1:
            if len_run_buttons > 1:
                raise RuntimeError("More than one run button found")
            raise RuntimeError("No run button found")
        print(f"Found button with name {''.join(run_buttons[0].texts())}")
        self.stand_window.set_focus()
        time.sleep(3)
        run_buttons[0].click()
        time.sleep(3)

    def init_gta(self):
        gta_path = self.config["gta"]["executable_path"]

        try:
            self.gta_process = self.get_process_by_executable_path(gta_path)
            return
        except RuntimeError:
            pass

        print(f"Starting GTA from with stand")
        self.run_gta_from_stand()

        start_time = time.time()

        while True:
            try:
                process = self.get_process_by_executable_path(gta_path)
                self.gta_process = process
                break
            except RuntimeError:
                if time.time() - start_time > 60:
                    raise RuntimeError("No GTA process found")
                time.sleep(1)

    def ensure_gta_runnung(self):
        if self.gta_process is None or not self.gta_process.is_running():
            self.init_gta()

    def get_banned_players(self):
        with self.Session() as session:
            return session.query(BannedPlayer.scid).all()

    def get_admin_players(self):
        with self.Session() as session:
            return (
                session.query(Player.scid)
                .filter(Player.role == RoleEnum.ADMIN.value)
                .all()
            )

    def download_banned_players(self):
        with open(STAND_ROOT / "bans.txt", "w") as f:
            for (scid,) in self.get_banned_players():
                f.write(f"{scid}\n")

    def download_admin_players(self):
        with open(STAND_ROOT / "admins.txt", "w") as f:
            for scid in self.get_admin_players():
                f.write(f"{scid}\n")

    def upload_detections(self):
        with open(STAND_ROOT / "detections.txt", "r") as f:
            for line in f:
                scid, detection_type = line.strip().split()
                self.session.add(Detection(scid=scid, detection_type=detection_type))
        self.session.commit()


if __name__ == "__main__":
    middleware = BanHammerServerMiddleware()

    while True:
        try:
            # middleware.ensure_gta_runnung()
            middleware.download_banned_players()
            # middleware.download_admin_players()
            # middleware.upload_detections()
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)
        else:
            time.sleep(1)
