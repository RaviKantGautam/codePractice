"""
================================================================================
Facade
Category: Structural Design Pattern
Source: https://refactoring.guru/design-patterns/facade
================================================================================

DEFINITION
----------
Facade is a structural design pattern that provides a simplified interface to
a library, a framework, or any other complex set of classes.

It decreases overall complexity for clients and gathers unwanted dependencies
in one place.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Hides complexity of subsystems behind a clean API.
2. Reduces coupling between clients and subsystem classes.
3. Makes libraries/frameworks easier to use.
4. Can layer multiple facades for different client needs.

WHEN TO USE
-----------
- You need a simple interface to a complex subsystem.
- There are many dependencies between clients and subsystem classes.
- You want to layer your subsystems.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations


class Facade:
    def __init__(self, subsystem1: Subsystem1, subsystem2: Subsystem2) -> None:
        self._subsystem1 = subsystem1 or Subsystem1()
        self._subsystem2 = subsystem2 or Subsystem2()

    def operation(self) -> str:
        results = []
        results.append("Facade initializes subsystems:")
        results.append(self._subsystem1.operation1())
        results.append(self._subsystem2.operation1())
        results.append("Facade orders subsystems to perform the action:")
        results.append(self._subsystem1.operation_n())
        results.append(self._subsystem2.operation_z())
        return "\n".join(results)


class Subsystem1:
    def operation1(self) -> str:
        return "Subsystem1: Ready!"

    def operation_n(self) -> str:
        return "Subsystem1: Go!"


class Subsystem2:
    def operation1(self) -> str:
        return "Subsystem2: Get ready!"

    def operation_z(self) -> str:
        return "Subsystem2: Fire!"


def client_code(facade: Facade) -> None:
    print(facade.operation(), end="")


if __name__ == "__main__":
    facade = Facade(Subsystem1(), Subsystem2())
    client_code(facade)

