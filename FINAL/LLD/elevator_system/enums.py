"""Shared enums for the elevator LLD."""

from enum import Enum, auto


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    IDLE = auto()  # no preferred direction (cabin / parked)


class ElevatorState(Enum):
    IDLE = auto()
    MOVING_UP = auto()
    MOVING_DOWN = auto()
    DOOR_OPEN = auto()
    MAINTENANCE = auto()


class RequestType(Enum):
    HALL = auto()   # external call from a floor
    CABIN = auto()  # internal destination selection
