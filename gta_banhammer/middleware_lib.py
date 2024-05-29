import os
import json
from pathlib import Path

import psutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gta_banhammer.tables import Base

STAND_ROOT = Path(os.getenv("APPDATA")) / "Stand"


class BanHammerMiddleware:
    CONFIG_PATH = STAND_ROOT / "config.json"

    def __init__(self) -> None:
        with open(STAND_ROOT / "config.json", "r") as f:
            self.config = json.load(f)

        self.engine = create_engine(self.config["database"]["uri"])
        self.Session = sessionmaker(bind=self.engine)

        Base.metadata.create_all(self.engine)


if __name__ == "__main__":
    BanHammerMiddleware()
