"""
Dispatch strategies — Strategy pattern.

Swap algorithms without changing Elevator or Controller code (OCP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from elevator import Elevator
from enums import Direction


class DispatchStrategy(ABC):
    @abstractmethod
    def select_elevator(
        self,
        elevators: list[Elevator],
        floor: int,
        direction: Direction,
    ) -> Elevator | None:
        ...


class NearestElevatorStrategy(DispatchStrategy):
    """
    Assign hall call to the elevator with the lowest estimate_cost().

    Cost prefers:
    1. Idle cars close to the floor
    2. Cars already traveling toward the caller in the same direction
    3. Otherwise penalize cars that must reverse / finish a sweep
    """

    def select_elevator(
        self,
        elevators: list[Elevator],
        floor: int,
        direction: Direction,
    ) -> Elevator | None:
        candidates = [e for e in elevators if e.is_available()]
        if not candidates:
            return None
        return min(candidates, key=lambda e: e.estimate_cost(floor, direction))


class LoadBalancedStrategy(DispatchStrategy):
    """
    Prefer elevators with fewer pending stops (fairness under load),
    then fall back to distance.
    """

    def select_elevator(
        self,
        elevators: list[Elevator],
        floor: int,
        direction: Direction,
    ) -> Elevator | None:
        candidates = [e for e in elevators if e.is_available()]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda e: (len(e.pending_stops()), e.estimate_cost(floor, direction)),
        )
