"""
================================================================================
Command
Category: Behavioral Design Pattern
Source: https://refactoring.guru/design-patterns/command
================================================================================

DEFINITION
----------
Command is a behavioral design pattern that turns a request into a stand-alone
object that contains all information about the request. This transformation
lets you parameterize methods with different requests, delay or queue a
request's execution, and support undoable operations.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Decouples invoker from receiver.
2. Enables undo/redo, macros, and queuing.
3. Requests become first-class objects (serialize, log, schedule).
4. Open/Closed — add new commands without changing invokers.

WHEN TO USE
-----------
- You want to parameterize objects with operations.
- You need to queue, schedule, or remotely execute operations.
- You need undo/redo or transactional operations.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass


class SimpleCommand(Command):
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def execute(self) -> None:
        print(f"SimpleCommand: See, I can do simple things like printing"
              f"({self._payload})")


class ComplexCommand(Command):
    def __init__(self, receiver: Receiver, a: str, b: str) -> None:
        self._receiver = receiver
        self._a = a
        self._b = b

    def execute(self) -> None:
        print("ComplexCommand: Complex stuff should be done by a receiver object", end="")
        self._receiver.do_something(self._a)
        self._receiver.do_something_else(self._b)


class Receiver:
    def do_something(self, a: str) -> None:
        print(f"\nReceiver: Working on ({a}.)", end="")

    def do_something_else(self, b: str) -> None:
        print(f"\nReceiver: Also working on ({b}.)", end="")


class Invoker:
    _on_start = None
    _on_finish = None

    def set_on_start(self, command: Command) -> None:
        self._on_start = command

    def set_on_finish(self, command: Command) -> None:
        self._on_finish = command

    def do_something_important(self) -> None:
        print("Invoker: Does anybody want something done before I begin?")
        if isinstance(self._on_start, Command):
            self._on_start.execute()

        print("Invoker: ...doing something really important...")

        print("Invoker: Does anybody want something done after I finish?")
        if isinstance(self._on_finish, Command):
            self._on_finish.execute()


if __name__ == "__main__":
    invoker = Invoker()
    invoker.set_on_start(SimpleCommand("Say Hi!"))
    receiver = Receiver()
    invoker.set_on_finish(ComplexCommand(receiver, "Send email", "Save report"))
    invoker.do_something_important()

