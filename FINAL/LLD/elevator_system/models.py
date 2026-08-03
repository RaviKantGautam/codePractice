"""Request models for hall and cabin calls."""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
import time

from enums import Direction, RequestType

_id_counter = itertools.count(1)


@dataclass(order=False)
class Request:
    floor: int
    direction: Direction
    request_type: RequestType
    id: int = field(default_factory=lambda: next(_id_counter))
    created_at: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return (
            f"Request(id={self.id}, floor={self.floor}, "
            f"dir={self.direction.name}, type={self.request_type.name})"
        )
