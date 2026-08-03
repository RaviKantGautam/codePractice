"""
Demo / interview walkthrough for the elevator LLD.

Building: 32 floors, 10 elevators.
"""

from controller import ElevatorController
from enums import Direction


def main() -> None:
    system = ElevatorController(num_elevators=10, min_floor=1, max_floor=32)

    print("=" * 60)
    print("Elevator LLD Demo — 10 elevators × 32 floors")
    print("=" * 60)

    # Scenario 1: Person on floor 5 wants to go up
    system.hall_call(floor=5, direction=Direction.UP)
    system.run(ticks=5)  # nearest elevator (likely #1 at floor 1) approaches

    # Passenger enters elevator #1 and selects floor 20
    system.cabin_call(elevator_id=1, floor=20)

    # Scenario 2: Concurrent hall calls on different floors
    system.hall_call(floor=30, direction=Direction.DOWN)
    system.hall_call(floor=12, direction=Direction.UP)
    system.hall_call(floor=3, direction=Direction.UP)

    # Let the system process movement
    system.run(ticks=40)

    # Scenario 3: Cabin call while moving
    # Pick an elevator that is not idle if possible
    busy = next((e for e in system.elevators if e.pending_stops()), system.elevators[0])
    try:
        system.cabin_call(elevator_id=busy.id, floor=8)
    except ValueError as exc:
        print("Cabin call skipped:", exc)

    system.run(ticks=25)

    print("\n" + "=" * 60)
    print("Final status")
    print("=" * 60)
    for line in system.status():
        print(line)


if __name__ == "__main__":
    main()
