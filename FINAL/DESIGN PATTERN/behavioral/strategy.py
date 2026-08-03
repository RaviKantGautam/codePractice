"""
================================================================================
Strategy
Category: Behavioral Design Pattern
Source: https://refactoring.guru/design-patterns/strategy
================================================================================

DEFINITION
----------
Strategy is a behavioral design pattern that lets you define a family of
algorithms, put each of them into a separate class, and make their objects
interchangeable.

The context holds a strategy reference and delegates the work to it. Strategies
can be swapped at runtime.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Swaps algorithms without changing the context class.
2. Isolates algorithm implementation details.
3. Replaces inheritance with composition for behavior variation.
4. Strongly related to Open/Closed Principle.

WHEN TO USE
-----------
- You need different variants of an algorithm and want to switch them.
- You have many similar classes differing only in behavior.
- A class has a massive conditional that selects algorithm variants.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


class Context:
    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def do_some_business_logic(self) -> None:
        print("Context: Sorting data using the strategy (not sure how it'll do it)")
        result = self._strategy.do_algorithm(["a", "b", "c", "d", "e"])
        print(",".join(result))


class Strategy(ABC):
    @abstractmethod
    def do_algorithm(self, data: List):
        pass


class ConcreteStrategyA(Strategy):
    def do_algorithm(self, data: List) -> List:
        return sorted(data)


class ConcreteStrategyB(Strategy):
    def do_algorithm(self, data: List) -> List:
        return list(reversed(sorted(data)))


if __name__ == "__main__":
    context = Context(ConcreteStrategyA())
    print("Client: Strategy is set to normal sorting.")
    context.do_some_business_logic()
    print()

    print("Client: Strategy is set to reverse sorting.")
    context.strategy = ConcreteStrategyB()
    context.do_some_business_logic()

