import os
import time
import psutil
from pathlib import Path

from sqlalchemy import create_engine, Table, Column, Integer, MetaData
from sqlalchemy.orm import declarative_base


Base = declarative_base()

SERVER = os.getenv("GTAVM_SERVER", "192.168.122.1")
RUNGAME = Path(os.getenv("GTAVM_RUNGAME", R"F:\RSG\Grand Theft Auto V\PlayGTAV.exe"))
RUNMENU = Path(os.getenv("GTAVM_RUNMENU", R"C:\Users\GTAVM-B0T\Desktop\menu.exe"))


class BannedPlayer(Base):
    __tablename__ = "banned_players"
    id = Column(Integer, primary_key=True)
    scid = Column(Integer, unique=True)


STAND_ROOT = Path(os.getenv("APPDATA")) / "Stand"

DATABASE_URI = ...
engine = create_engine(DATABASE_URI)
metadata = MetaData()


Base.metadata.create_all(engine)

banned_players = Table(
    "banned_players", metadata, Column("scid", Integer, primary_key=True)
)


def upload_banned_players():
    global already_banned
    try:
        players_to_ban = {
            int(i) for i in (STAND_ROOT / "banfile_send.txt").read_text().splitlines()
        }
    except FileNotFoundError:
        players_to_ban = set()
    players_to_ban -= get_banned_players()
    with engine.connect() as conn:
        for player in players_to_ban:
            insert_stmt = banned_players.insert().values(scid=int(player))
            conn.execute(insert_stmt)
            print(f"Player with SCID {player} has been banned.")
        conn.commit()


def get_banned_players():
    with engine.connect() as conn:
        select_stmt = banned_players.select()
        result = conn.execute(select_stmt)
        return {row[0] for row in result}


def download_banned_players():
    with open(STAND_ROOT / "banfile_recv.txt", "w") as f:
        for scid in get_banned_players():
            f.write(f"{scid}\n")


def ensure_menu_running():
    if not any(p.name() == RUNMENU.name for p in psutil.process_iter(["name"])):
        print("Starting menu...")
        os.system(f'start "{RUNMENU}"')
        time.sleep(10)


def get_gta_process() -> psutil.Process | None:
    try:
        return next(p for p in psutil.process_iter(["name"]) if p.name() == "GTA5.exe")
    except StopIteration:
        return None


def ensure_gta_running():
    if gta_process := get_gta_process():
        if gta_process.status() == psutil.STATUS_RUNNING:
            return
        try:
            gta_process.kill()
        except psutil.AccessDenied:
            pass
    start_gta()


def start_gta():
    ensure_menu_running()
    print("Starting GTA V...")
    os.system(f'start "{RUNGAME}"')


if __name__ == "__main__":
    while True:
        # ensure_gta_running()
        try:
            upload_banned_players()
            download_banned_players()
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)
        else:
            time.sleep(1)
