"""
================================================================================
Composite
Category: Structural Design Pattern
Source: https://refactoring.guru/design-patterns/composite
================================================================================

DEFINITION
----------
Composite is a structural design pattern that lets you compose objects into
tree structures and then work with these structures as if they were individual
objects.

Clients treat both simple (leaf) and complex (composite) elements uniformly
through a common component interface.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Models part-whole hierarchies (UI trees, file systems, org charts).
2. Clients can ignore differences between leaf and composite objects.
3. Easy to add new component types.
4. Simplifies recursive operations over trees.

WHEN TO USE
-----------
- You need to represent tree-like object structures.
- Clients should treat individual and composed objects the same way.
- You want recursive operations (draw, calculate total, etc.).

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


class Component(ABC):
    @property
    def parent(self) -> Component:
        return self._parent

    @parent.setter
    def parent(self, parent: Component):
        self._parent = parent

    def add(self, component: Component) -> None:
        pass

    def remove(self, component: Component) -> None:
        pass

    def is_composite(self) -> bool:
        return False

    @abstractmethod
    def operation(self) -> str:
        pass


class Leaf(Component):
    def operation(self) -> str:
        return "Leaf"


class Composite(Component):
    def __init__(self) -> None:
        self._children: List[Component] = []

    def add(self, component: Component) -> None:
        self._children.append(component)
        component.parent = self

    def remove(self, component: Component) -> None:
        self._children.remove(component)
        component.parent = None

    def is_composite(self) -> bool:
        return True

    def operation(self) -> str:
        results = []
        for child in self._children:
            results.append(child.operation())
        return f"Branch({'+'.join(results)})"


def client_code(component: Component) -> None:
    print(f"RESULT: {component.operation()}", end="")


if __name__ == "__main__":
    simple = Leaf()
    print("Client: I've got a simple component:")
    client_code(simple)
    print("\n")

    tree = Composite()
    branch1 = Composite()
    branch1.add(Leaf())
    branch1.add(Leaf())
    branch2 = Composite()
    branch2.add(Leaf())
    tree.add(branch1)
    tree.add(branch2)
    print("Client: Now I've got a composite tree:")
    client_code(tree)

