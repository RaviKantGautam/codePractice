"""
================================================================================
Bridge
Category: Structural Design Pattern
Source: https://refactoring.guru/design-patterns/bridge
================================================================================

DEFINITION
----------
Bridge is a structural design pattern that lets you split a large class or a
set of closely related classes into two separate hierarchies — abstraction and
implementation — which can be developed independently of each other.

It prefers composition over inheritance to avoid an explosion of subclasses
when combining dimensions (e.g., Shape x Color).

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Separates abstraction from implementation so both can vary independently.
2. Avoids combinatorial subclass explosion.
3. Improves platform independence (swap implementations at runtime).
4. Hides implementation details from clients.

WHEN TO USE
-----------
- You want to divide a monolithic class with several variants of functionality.
- You need to extend a class in orthogonal dimensions (UI theme x OS).
- You want to switch implementations at runtime.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC, abstractmethod


class Implementation(ABC):
    @abstractmethod
    def operation_implementation(self) -> str:
        pass


class ConcreteImplementationA(Implementation):
    def operation_implementation(self) -> str:
        return "ConcreteImplementationA: Here's the result on platform A."


class ConcreteImplementationB(Implementation):
    def operation_implementation(self) -> str:
        return "ConcreteImplementationB: Here's the result on platform B."


class Abstraction:
    def __init__(self, implementation: Implementation) -> None:
        self.implementation = implementation

    def operation(self) -> str:
        return (
            f"Abstraction: Base operation with:\n"
            f"{self.implementation.operation_implementation()}"
        )


class ExtendedAbstraction(Abstraction):
    def operation(self) -> str:
        return (
            f"ExtendedAbstraction: Extended operation with:\n"
            f"{self.implementation.operation_implementation()}"
        )


def client_code(abstraction: Abstraction) -> None:
    print(abstraction.operation(), end="")


if __name__ == "__main__":
    implementation = ConcreteImplementationA()
    abstraction = Abstraction(implementation)
    client_code(abstraction)
    print("\n")

    implementation = ConcreteImplementationB()
    abstraction = ExtendedAbstraction(implementation)
    client_code(abstraction)

