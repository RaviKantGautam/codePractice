"""
================================================================================
Chain of Responsibility
Category: Behavioral Design Pattern
Source: https://refactoring.guru/design-patterns/chain-of-responsibility
================================================================================

DEFINITION
----------
Chain of Responsibility is a behavioral design pattern that lets you pass
requests along a chain of handlers. Upon receiving a request, each handler
decides either to process it or to pass it to the next handler in the chain.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Decouples sender from receivers.
2. Dynamically rearrange / extend processing pipeline.
3. Each handler has a single responsibility.
4. Common in middleware, logging filters, event systems.

WHEN TO USE
-----------
- Multiple objects may handle a request, and the handler isn't known in advance.
- You want to issue a request to several objects without coupling to receivers.
- The set of handlers should be specified dynamically.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional


class Handler(ABC):
    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, request) -> Optional[str]:
        pass


class AbstractHandler(Handler):
    _next_handler: Handler = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, request: Any) -> str:
        if self._next_handler:
            return self._next_handler.handle(request)
        return None


class MonkeyHandler(AbstractHandler):
    def handle(self, request: Any) -> str:
        if request == "Banana":
            return f"Monkey: I'll eat the {request}"
        return super().handle(request)


class SquirrelHandler(AbstractHandler):
    def handle(self, request: Any) -> str:
        if request == "Nut":
            return f"Squirrel: I'll eat the {request}"
        return super().handle(request)


class DogHandler(AbstractHandler):
    def handle(self, request: Any) -> str:
        if request == "MeatBall":
            return f"Dog: I'll eat the {request}"
        return super().handle(request)


def client_code(handler: Handler) -> None:
    for food in ["Nut", "Banana", "Coffee"]:
        print(f"\nClient: Who wants a {food}?")
        result = handler.handle(food)
        if result:
            print(f"  {result}", end="")
        else:
            print(f"  {food} was left untouched.", end="")


if __name__ == "__main__":
    monkey = MonkeyHandler()
    squirrel = SquirrelHandler()
    dog = DogHandler()
    monkey.set_next(squirrel).set_next(dog)

    print("Chain: Monkey > Squirrel > Dog")
    client_code(monkey)
    print("\n")
    print("Subchain: Squirrel > Dog")
    client_code(squirrel)

