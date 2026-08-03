"""
================================================================================
Observer
Category: Behavioral Design Pattern
Source: https://refactoring.guru/design-patterns/observer
================================================================================

DEFINITION
----------
Observer is a behavioral design pattern that lets you define a subscription
mechanism to notify multiple objects about any events that happen to the
object they're observing.

Subjects notify observers; observers can subscribe/unsubscribe dynamically.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Establishes a one-to-many notification relationship.
2. Loose coupling between subject and observers.
3. Supports event-driven architectures and GUI frameworks.
4. Observers can be added/removed at runtime.

WHEN TO USE
-----------
- Changes to one object require changing others, and you don't know how many.
- An object should notify others without making assumptions about who they are.
- You need a pub/sub or event system.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC, abstractmethod
from random import randrange
from typing import List


class Subject(ABC):
    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def notify(self) -> None:
        pass


class ConcreteSubject(Subject):
    _state: int = None
    _observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    def some_business_logic(self) -> None:
        print("\nSubject: I'm doing something important.")
        self._state = randrange(0, 10)
        print(f"Subject: My state has just changed to: {self._state}")
        self.notify()


class Observer(ABC):
    @abstractmethod
    def update(self, subject: Subject) -> None:
        pass


class ConcreteObserverA(Observer):
    def update(self, subject: Subject) -> None:
        if subject._state < 3:
            print("ConcreteObserverA: Reacted to the event")


class ConcreteObserverB(Observer):
    def update(self, subject: Subject) -> None:
        if subject._state == 0 or subject._state >= 2:
            print("ConcreteObserverB: Reacted to the event")


if __name__ == "__main__":
    subject = ConcreteSubject()
    observer_a = ConcreteObserverA()
    subject.attach(observer_a)
    observer_b = ConcreteObserverB()
    subject.attach(observer_b)

    subject.some_business_logic()
    subject.some_business_logic()
    subject.detach(observer_a)
    subject.some_business_logic()

