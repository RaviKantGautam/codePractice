"""
================================================================================
Mediator
Category: Behavioral Design Pattern
Source: https://refactoring.guru/design-patterns/mediator
================================================================================

DEFINITION
----------
Mediator is a behavioral design pattern that lets you reduce chaotic
dependencies between objects. The pattern restricts direct communications
between objects and forces them to collaborate only via a mediator object.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Reduces coupling between components (colleagues).
2. Centralizes complex interaction logic.
3. Components become reusable independently.
4. Common in UI dialogs, chat rooms, air traffic control analogies.

WHEN TO USE
-----------
- Objects communicate in complex, hard-to-understand ways.
- Reusing a component is difficult because it depends on many others.
- You want to centralize multi-object workflows.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC


class Mediator(ABC):
    def notify(self, sender: object, event: str) -> None:
        pass


class ConcreteMediator(Mediator):
    def __init__(self, component1: Component1, component2: Component2) -> None:
        self._component1 = component1
        self._component1.mediator = self
        self._component2 = component2
        self._component2.mediator = self

    def notify(self, sender: object, event: str) -> None:
        if event == "A":
            print("Mediator reacts on A and triggers following operations:")
            self._component2.do_c()
        elif event == "D":
            print("Mediator reacts on D and triggers following operations:")
            self._component1.do_b()
            self._component2.do_c()


class BaseComponent:
    def __init__(self, mediator: Mediator = None) -> None:
        self._mediator = mediator

    @property
    def mediator(self) -> Mediator:
        return self._mediator

    @mediator.setter
    def mediator(self, mediator: Mediator) -> None:
        self._mediator = mediator


class Component1(BaseComponent):
    def do_a(self) -> None:
        print("Component 1 does A.")
        self.mediator.notify(self, "A")

    def do_b(self) -> None:
        print("Component 1 does B.")
        self.mediator.notify(self, "B")


class Component2(BaseComponent):
    def do_c(self) -> None:
        print("Component 2 does C.")
        self.mediator.notify(self, "C")

    def do_d(self) -> None:
        print("Component 2 does D.")
        self.mediator.notify(self, "D")


if __name__ == "__main__":
    c1 = Component1()
    c2 = Component2()
    mediator = ConcreteMediator(c1, c2)

    print("Client triggers operation A.")
    c1.do_a()
    print("\n", end="")
    print("Client triggers operation D.")
    c2.do_d()

