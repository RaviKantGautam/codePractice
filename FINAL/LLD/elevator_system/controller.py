"""
ElevatorController — Facade for the building elevator system.

Public API used by panels / simulation:
  - hall_call(floor, direction)
  - cabin_call(elevator_id, floor)
  - step() / run(ticks)
  - status()
"""

from __future__ import annotations

from elevator import Elevator
from enums import Direction, RequestType
from models import Request
from scheduler import DispatchStrategy, NearestElevatorStrategy


class ElevatorController:
    def __init__(
        self,
        num_elevators: int = 10,
        min_floor: int = 1,
        max_floor: int = 32,
        strategy: DispatchStrategy | None = None,
    ) -> None:
        if num_elevators < 1:
            raise ValueError("Need at least 1 elevator")
        if max_floor <= min_floor:
            raise ValueError("max_floor must be > min_floor")

        self.min_floor = min_floor
        self.max_floor = max_floor
        self.strategy = strategy or NearestElevatorStrategy()
        self.elevators: list[Elevator] = [
            Elevator(elevator_id=i + 1, min_floor=min_floor, max_floor=max_floor)
            for i in range(num_elevators)
        ]
        self._request_log: list[Request] = []
        self.tick = 0

    # ----------------------------------------------------------------- API
    def hall_call(self, floor: int, direction: Direction) -> Request:
        """External call from a floor panel (UP / DOWN)."""
        self._validate_floor(floor)
        if direction not in (Direction.UP, Direction.DOWN):
            raise ValueError("Hall call direction must be UP or DOWN")
        if floor == self.max_floor and direction == Direction.UP:
            raise ValueError("Cannot call UP from top floor")
        if floor == self.min_floor and direction == Direction.DOWN:
            raise ValueError("Cannot call DOWN from bottom floor")

        request = Request(floor=floor, direction=direction, request_type=RequestType.HALL)
        elevator = self.strategy.select_elevator(self.elevators, floor, direction)
        if elevator is None:
            raise RuntimeError("No elevator available (all in maintenance?)")

        elevator.add_stop(floor)
        self._request_log.append(request)
        print(
            f"[t={self.tick}] HALL {direction.name} @ F{floor} "
            f"→ assigned Elevator#{elevator.id} (at F{elevator.current_floor})"
        )
        return request

    def cabin_call(self, elevator_id: int, floor: int) -> Request:
        """Internal destination button inside a specific elevator."""
        self._validate_floor(floor)
        elevator = self._get_elevator(elevator_id)
        request = Request(
            floor=floor,
            direction=Direction.IDLE,
            request_type=RequestType.CABIN,
        )
        elevator.add_stop(floor)
        self._request_log.append(request)
        print(
            f"[t={self.tick}] CABIN Elevator#{elevator_id} → F{floor} "
            f"(now at F{elevator.current_floor})"
        )
        return request

    def step(self) -> None:
        """Advance simulation by one tick for all elevators."""
        self.tick += 1
        for elevator in self.elevators:
            prev = (elevator.current_floor, elevator.state)
            elevator.step()
            if (elevator.current_floor, elevator.state) != prev:
                print(f"[t={self.tick}] {elevator}")

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.step()

    def status(self) -> list[str]:
        return [repr(e) for e in self.elevators]

    def set_maintenance(self, elevator_id: int, enabled: bool = True) -> None:
        self._get_elevator(elevator_id).set_maintenance(enabled)
        print(f"[t={self.tick}] Elevator#{elevator_id} maintenance={enabled}")

    # -------------------------------------------------------------- helpers
    def _validate_floor(self, floor: int) -> None:
        if not self.min_floor <= floor <= self.max_floor:
            raise ValueError(
                f"Floor {floor} out of range [{self.min_floor}, {self.max_floor}]"
            )

    def _get_elevator(self, elevator_id: int) -> Elevator:
        for elevator in self.elevators:
            if elevator.id == elevator_id:
                return elevator
        raise KeyError(f"Unknown elevator id: {elevator_id}")
