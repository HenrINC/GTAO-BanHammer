import time
from pathlib import Path

from gta_banhammer.enums import RoleEnum
from gta_banhammer.tables import Player, BannedPlayer, Detection
from gta_banhammer.middleware_lib import BanHammerMiddleware, STAND_ROOT
from gta_banhammer.stand import Stand
from gta_banhammer.gta import GTA


class BanHammerServerMiddleware(BanHammerMiddleware):
    def __init__(self):
        super().__init__()

        self._stand: Stand = None
        self._gta: GTA = None

    @property
    def stand(self):
        if self._stand is None:
            self.init_stand()
        return self._stand

    def init_stand(self):
        self.gta.ensure_running()
        self.gta.ensure_stable()
        self._stand = Stand(
            self.gta.process,
            self.gta.pm,
            dll_folder=STAND_ROOT / "Bin",
            injector_path=Path(self.config["injector"]["binaries_path"]),
        )

    def init_gta(self):
        gta_path = self.config["gta"]["binaries_folder"]
        self._gta = GTA(gta_path)

    @property
    def gta(self):
        if self._gta is None:
            self.init_gta()
        return self._gta

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
            middleware.gta.ensure_running()
            middleware.stand.ensure_running()
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)
        else:
            time.sleep(1)
