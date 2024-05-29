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

        self.gta_process: Optional[psutil.Process] = None

    def init_stand(self): ...

    def ensure_stand_running(self): ...

    def run_gta_stand(self): ...

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
            middleware.ensure_gta_runnung()
            middleware.ensure_stand_running()
            # middleware.download_banned_players()
            # middleware.download_admin_players()
            # middleware.upload_detections()
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)
        else:
            time.sleep(1)
