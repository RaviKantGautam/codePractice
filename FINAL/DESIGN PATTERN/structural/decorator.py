"""
================================================================================
Decorator
Category: Structural Design Pattern
Source: https://refactoring.guru/design-patterns/decorator
================================================================================

DEFINITION
----------
Decorator is a structural design pattern that lets you attach new behaviors to
objects by placing them inside wrapper objects that contain the behaviors.

Both the target and decorators share the same interface, so you can stack
wrappers and accumulate behavior dynamically.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Add responsibilities at runtime without subclass explosion.
2. Compose behaviors by stacking decorators.
3. Keeps single-responsibility — each decorator does one enhancement.
4. Very natural in Python (and related to Python's function decorators).

WHEN TO USE
-----------
- You need to add optional behaviors to objects dynamically.
- Extending via inheritance is impractical or impossible.
- Responsibilities can be withdrawn as well as added.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

class Component:
    def operation(self) -> str:
        pass


class ConcreteComponent(Component):
    def operation(self) -> str:
        return "ConcreteComponent"


class Decorator(Component):
    _component: Component = None

    def __init__(self, component: Component) -> None:
        self._component = component

    @property
    def component(self) -> Component:
        return self._component

    def operation(self) -> str:
        return self._component.operation()


class ConcreteDecoratorA(Decorator):
    def operation(self) -> str:
        return f"ConcreteDecoratorA({self.component.operation()})"


class ConcreteDecoratorB(Decorator):
    def operation(self) -> str:
        return f"ConcreteDecoratorB({self.component.operation()})"


def client_code(component: Component) -> None:
    print(f"RESULT: {component.operation()}", end="")


if __name__ == "__main__":
    simple = ConcreteComponent()
    print("Client: I've got a simple component:")
    client_code(simple)
    print("\n")

    decorator1 = ConcreteDecoratorA(simple)
    decorator2 = ConcreteDecoratorB(decorator1)
    print("Client: Now I've got a decorated component:")
    client_code(decorator2)

