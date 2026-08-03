# LLD: Elevator System (Interview)

## Problem Statement

Design a low-level elevator control system for a building with:

| Parameter | Value |
|-----------|-------|
| Floors | **32** (floors `1` … `32`) |
| Elevators | **10** |

Support:
- Hall calls (external): user on a floor presses **UP** or **DOWN**
- Cabin calls (internal): passenger selects destination floor inside an elevator
- Efficient assignment of hall calls to one of the 10 elevators
- Safe movement (serve stops in travel direction — SCAN / LOOK style)

---

## Functional Requirements

1. Request an elevator from any floor in a direction (UP/DOWN).
2. Select destination floors inside a moving/idle elevator.
3. Elevator opens doors at stop floors, then continues.
4. Multiple pending requests per elevator.
5. System picks a suitable elevator for each hall call.
6. Idle elevators park / wait for next assignment.

## Non-Functional (interview talking points)

- Extensible dispatch strategy (swap algorithms without rewriting elevators)
- Thread-safety note for real systems (here: single-threaded simulation)
- Clear separation of concerns (SOLID)
- Observable state for monitoring / UI

---

## High-Level Components

```
┌─────────────────────────────────────────────┐
│              ElevatorController             │  Facade / orchestrator
│         (BuildingElevatorSystem)            │
└───────────────┬─────────────┬───────────────┘
                │             │
                ▼             ▼
      ┌─────────────┐   ┌────────────────┐
      │  Elevator×10│   │ DispatchStrategy│  Strategy pattern
      └──────┬──────┘   │ (Nearest/SCAN)  │
             │          └────────────────┘
             ▼
      ┌─────────────┐
      │ StopRequests│  pending floors + direction
      └─────────────┘
```

---

## Core Classes

| Class | Responsibility |
|-------|----------------|
| `Direction` / `ElevatorState` | Enums for movement & lifecycle |
| `Request` | Hall or cabin request (floor, direction, type) |
| `Elevator` | Current floor, state, pending stops, step simulation |
| `DispatchStrategy` | Chooses which elevator handles a hall call |
| `NearestElevatorStrategy` | Cost-based assignment (default) |
| `ElevatorController` | Public API: hall call, cabin call, tick/step |

---

## Design Patterns Used

1. **Strategy** — pluggable elevator dispatch (`NearestElevatorStrategy`)
2. **State** (lightweight via enum + transitions) — IDLE / MOVING_UP / MOVING_DOWN / DOOR_OPEN
3. **Facade** — `ElevatorController` is the single entry for clients
4. **Single Responsibility** — Elevator moves; Strategy assigns; Controller coordinates

---

## Dispatch Algorithm (Nearest cost)

For each idle/available elevator, estimate cost:

```
cost = |elevator.floor - request.floor|
```

Penalties:
- Elevator moving **away** from request → higher cost
- Elevator in opposite direction and cannot pick soon → skip or penalize
- Prefer elevator already going toward the floor (LOOK/SCAN friendly)

Assign hall call to **minimum cost** elevator.

---

## Elevator Movement (LOOK / SCAN idea)

While moving UP:
- Serve all pending stops `>= current` in ascending order
- When none remain above, reverse if downs pending, else IDLE

While moving DOWN: mirror logic.

---

## Interview Extension Points

- Weight / capacity limits
- VIP / express elevators
- Peak-hour zoning (elevators dedicated to floor ranges)
- Door obstruction / emergency stop
- Multi-threaded motor simulation + concurrent requests
- Persistence of pending requests on crash

---

## How to Run

```bash
python3 -m FINAL.LLD.elevator_system.demo
# or from this folder:
cd FINAL/LLD/elevator_system && python3 demo.py
```

---

## Sample Interview Flow (how to explain)

1. Clarify floors, elevators, hall vs cabin buttons, goals (wait time vs fairness)
2. List entities and APIs
3. Draw class diagram (above)
4. Explain dispatch strategy + movement algorithm
5. Walk through a request lifecycle with an example
6. Mention concurrency, failure modes, and extensions
'''

