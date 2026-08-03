"""
================================================================================
Iterator
Category: Behavioral Design Pattern
Source: https://refactoring.guru/design-patterns/iterator
================================================================================

DEFINITION
----------
Iterator is a behavioral design pattern that lets you traverse elements of a
collection without exposing its underlying representation (list, stack, tree,
etc.).

It separates traversal algorithms from collection data structures.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Hides internal structure of collections.
2. Supports multiple simultaneous traversals.
3. Enables uniform iteration API across different structures.
4. Python's iterator protocol (`__iter__` / `__next__`) is this pattern built-in.

WHEN TO USE
-----------
- Complex data structures need traversal without leaking internals.
- You want a uniform way to traverse different collections.
- You need multiple traversal algorithms for the same collection.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from collections.abc import Iterable, Iterator
from typing import Any


class AlphabeticalOrderIterator(Iterator):
    _position: int = None
    _reverse: bool = False

    def __init__(self, collection: WordsCollection, reverse: bool = False) -> None:
        self._collection = collection
        self._reverse = reverse
        self._position = -1 if reverse else 0

    def __next__(self) -> Any:
        try:
            value = self._collection[self._position]
            self._position += -1 if self._reverse else 1
        except IndexError:
            raise StopIteration()
        return value


class WordsCollection(Iterable):
    def __init__(self, collection: list[Any] | None = None) -> None:
        self._collection = collection or []

    def __getitem__(self, index: int) -> Any:
        return self._collection[index]

    def __iter__(self) -> AlphabeticalOrderIterator:
        return AlphabeticalOrderIterator(self)

    def get_reverse_iterator(self) -> AlphabeticalOrderIterator:
        return AlphabeticalOrderIterator(self, True)

    def add_item(self, item: Any) -> None:
        self._collection.append(item)


if __name__ == "__main__":
    collection = WordsCollection()
    collection.add_item("First")
    collection.add_item("Second")
    collection.add_item("Third")

    print("Straight traversal:")
    print("\n".join(collection))
    print("")

    print("Reverse traversal:")
    print("\n".join(collection.get_reverse_iterator()), end="")

