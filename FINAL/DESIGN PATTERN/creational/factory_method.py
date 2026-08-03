"""
================================================================================
Factory Method
Category: Creational Design Pattern
Source: https://refactoring.guru/design-patterns/factory-method
================================================================================

DEFINITION
----------
Factory Method is a creational design pattern that provides an interface for
creating objects in a superclass, but allows subclasses to alter the type of
objects that will be created.

Instead of calling a constructor directly, you call a factory method. Subclasses
override that method to produce different concrete products.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Decouples client code from concrete classes.
2. Makes it easy to introduce new product types without changing existing creators.
3. Supports Open/Closed Principle — extend by adding subclasses.
4. Centralizes object-creation logic.

WHEN TO USE
-----------
- You don't know beforehand the exact types of objects your code should work with.
- You want to give subclasses a way to extend/change object creation.
- You want to reuse existing creation logic across related products.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from __future__ import annotations
from abc import ABC, abstractmethod


class Creator(ABC):
    """
    The Creator class declares the factory method that is supposed to return an
    object of a Product class. The Creator's subclasses usually provide the
    implementation of this method.
    """

    @abstractmethod
    def factory_method(self):
        pass

    def some_operation(self) -> str:
        # Call the factory method to create a Product object.
        product = self.factory_method()
        # Now, use the product.
        result = f"Creator: The same creator's code has just worked with {product.operation()}"
        return result


class ConcreteCreator1(Creator):
    def factory_method(self) -> Product:
        return ConcreteProduct1()


class ConcreteCreator2(Creator):
    def factory_method(self) -> Product:
        return ConcreteProduct2()


class Product(ABC):
    @abstractmethod
    def operation(self) -> str:
        pass


class ConcreteProduct1(Product):
    def operation(self) -> str:
        return "{Result of the ConcreteProduct1}"


class ConcreteProduct2(Product):
    def operation(self) -> str:
        return "{Result of the ConcreteProduct2}"


def client_code(creator: Creator) -> None:
    print(
        f"Client: I'm not aware of the creator's class, but it still works.\n"
        f"{creator.some_operation()}",
        end="",
    )


if __name__ == "__main__":
    print("App: Launched with the ConcreteCreator1.")
    client_code(ConcreteCreator1())
    print("\n")

    print("App: Launched with the ConcreteCreator2.")
    client_code(ConcreteCreator2())

