import time

from gta_banhammer.tables import BannedPlayer, Player
from gta_banhammer.middleware_lib import BanHammerMiddleware, STAND_ROOT


class BanHammerClientMiddleware(BanHammerMiddleware):
    def __init__(self):
        super().__init__()

    def get_local_banned_players(self):
        banned_players = set()
        with open(STAND_ROOT / "bans.txt", "r") as f:
            for line in f.readlines():
                scid, username = line.strip().split(";", 1)
                banned_players.add((int(scid), username))
        return banned_players

    def get_remote_banned_players(self):
        with self.Session() as session:
            return session.query(BannedPlayer.scid).all()

    def get_existing_players(self):
        with self.Session() as session:
            return session.query(Player.scid).all()

    def upload_banned_players(self):
        players_to_ban = self.get_local_banned_players()
        already_banned_players = self.get_remote_banned_players()
        existing_players = self.get_existing_players()
        with self.Session() as session:
            for scid, username in players_to_ban:
                if (scid,) not in existing_players:
                    session.add(Player(scid=scid, username=username))
                if (scid,) not in already_banned_players:
                    session.add(BannedPlayer(scid=scid))
                    print(f"Banned {username} ({scid})")
            session.commit()


if __name__ == "__main__":
    try:
        middleware = BanHammerClientMiddleware()
        while True:
            try:
                middleware.upload_banned_players()
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        breakpoint()
