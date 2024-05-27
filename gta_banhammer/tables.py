from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Player(Base):
    __tablename__ = "players"
    scid = Column(Integer, primary_key=True)
    username = Column(String)
    last_seen = Column(DateTime)
    role = Column(String)


class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True)
    scid = Column(Integer, ForeignKey("players.scid"))
    detection_type = Column(String)
    timestamp = Column(DateTime)


class BannedPlayer(Base):
    __tablename__ = "banned_players"
    scid = Column(Integer, ForeignKey("players.scid"), primary_key=True)
    ban_reason = Column(String)
    ban_timestamp = Column(DateTime)
