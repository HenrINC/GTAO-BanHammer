import enum


class RoleEnum(enum.Enum):
    USER = 0
    MODERATOR = 1000
    ADMIN = 2000
    OWNER = 3000


class DetectionType(enum.Enum):
    OTR_TOO_LONG = enum.auto()
    DEAD_TOO_LONG = enum.auto()

    GM_KILL = enum.auto()

    BOT_GRIEF = enum.auto()
    BOT_KICK = enum.auto()
    BOT_CRASH = enum.auto()
