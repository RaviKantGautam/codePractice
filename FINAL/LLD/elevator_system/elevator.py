"""
Elevator car — owns position, state, and pending stop set.
Movement follows a LOOK-style algorithm (serve current direction, then reverse).
"""

from __future__ import annotations

from enums import Direction, ElevatorState


class Elevator:
    def __init__(self, elevator_id: int, min_floor: int = 1, max_floor: int = 32) -> None:
        if min_floor >= max_floor:
            raise ValueError("min_floor must be < max_floor")
        self.id = elevator_id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.current_floor = min_floor
        self.state = ElevatorState.IDLE
        self.direction = Direction.IDLE
        # Pending destination floors (cabin + assigned hall stops)
        self._stops: set[int] = set()
        self.door_open_ticks_remaining = 0

    # ------------------------------------------------------------------ API
    def add_stop(self, floor: int) -> None:
        self._validate_floor(floor)
        if floor == self.current_floor and self.state == ElevatorState.IDLE:
            self._open_door()
            return
        self._stops.add(floor)
        if self.state == ElevatorState.IDLE:
            self._choose_initial_direction(floor)

    def pending_stops(self) -> set[int]:
        return set(self._stops)

    def is_available(self) -> bool:
        return self.state != ElevatorState.MAINTENANCE

    def set_maintenance(self, enabled: bool) -> None:
        if enabled:
            self.state = ElevatorState.MAINTENANCE
            self.direction = Direction.IDLE
            self._stops.clear()
        else:
            self.state = ElevatorState.IDLE

    # ------------------------------------------------------------- simulation
    def step(self) -> None:
        """Advance one time unit (1 floor move or 1 door tick)."""
        if self.state == ElevatorState.MAINTENANCE:
            return

        if self.state == ElevatorState.DOOR_OPEN:
            self.door_open_ticks_remaining -= 1
            if self.door_open_ticks_remaining <= 0:
                self._after_door_close()
            return

        if not self._stops:
            self.state = ElevatorState.IDLE
            self.direction = Direction.IDLE
            return

        self._ensure_direction()
        if self.direction == Direction.UP:
            self.current_floor += 1
            self.state = ElevatorState.MOVING_UP
        elif self.direction == Direction.DOWN:
            self.current_floor -= 1
            self.state = ElevatorState.MOVING_DOWN

        self.current_floor = max(self.min_floor, min(self.max_floor, self.current_floor))

        if self.current_floor in self._stops:
            self._stops.remove(self.current_floor)
            self._open_door()

    # -------------------------------------------------------------- internals
    def _validate_floor(self, floor: int) -> None:
        if not self.min_floor <= floor <= self.max_floor:
            raise ValueError(
                f"Floor {floor} out of range [{self.min_floor}, {self.max_floor}]"
            )

    def _open_door(self) -> None:
        self.state = ElevatorState.DOOR_OPEN
        self.door_open_ticks_remaining = 2  # stay open for 2 ticks

    def _after_door_close(self) -> None:
        if not self._stops:
            self.state = ElevatorState.IDLE
            self.direction = Direction.IDLE
            return
        self._ensure_direction()
        self.state = (
            ElevatorState.MOVING_UP
            if self.direction == Direction.UP
            else ElevatorState.MOVING_DOWN
        )

    def _choose_initial_direction(self, target: int) -> None:
        if target > self.current_floor:
            self.direction = Direction.UP
            self.state = ElevatorState.MOVING_UP
        elif target < self.current_floor:
            self.direction = Direction.DOWN
            self.state = ElevatorState.MOVING_DOWN
        else:
            self._open_door()

    def _ensure_direction(self) -> None:
        """LOOK: continue in current direction if stops remain; else reverse."""
        ups = {f for f in self._stops if f > self.current_floor}
        downs = {f for f in self._stops if f < self.current_floor}

        if self.direction == Direction.UP:
            if ups:
                return
            if downs:
                self.direction = Direction.DOWN
                return
        elif self.direction == Direction.DOWN:
            if downs:
                return
            if ups:
                self.direction = Direction.UP
                return

        # Idle / unknown — pick nearest pending stop's direction
        if ups and not downs:
            self.direction = Direction.UP
        elif downs and not ups:
            self.direction = Direction.DOWN
        elif ups and downs:
            nearest_up = min(ups)
            nearest_down = max(downs)
            if abs(nearest_up - self.current_floor) <= abs(self.current_floor - nearest_down):
                self.direction = Direction.UP
            else:
                self.direction = Direction.DOWN

    def can_take_hall_request(self, floor: int, direction: Direction) -> bool:
        """Whether this car is a reasonable candidate for a hall call."""
        if not self.is_available():
            return False
        if self.state == ElevatorState.IDLE:
            return True
        # Already going up and request is above us wanting UP
        if self.direction == Direction.UP and direction == Direction.UP and floor >= self.current_floor:
            return True
        if self.direction == Direction.DOWN and direction == Direction.DOWN and floor <= self.current_floor:
            return True
        # Still allow assignment with penalty (handled in strategy cost)
        return True

    def estimate_cost(self, floor: int, direction: Direction) -> int:
        """Lower is better. Used by NearestElevatorStrategy."""
        if not self.is_available():
            return 10**9

        distance = abs(self.current_floor - floor)
        penalty = 0

        if self.state == ElevatorState.IDLE:
            return distance

        same_way = (
            (self.direction == Direction.UP and direction == Direction.UP and floor >= self.current_floor)
            or (
                self.direction == Direction.DOWN
                and direction == Direction.DOWN
                and floor <= self.current_floor
            )
        )
        if same_way:
            return distance  # preferential

        # Moving away or opposite — must finish current sweep first (rough penalty)
        penalty = 20 + len(self._stops) * 2
        return distance + penalty

    def __repr__(self) -> str:
        return (
            f"Elevator(id={self.id}, floor={self.current_floor}, "
            f"state={self.state.name}, dir={self.direction.name}, "
            f"stops={sorted(self._stops)})"
        )
