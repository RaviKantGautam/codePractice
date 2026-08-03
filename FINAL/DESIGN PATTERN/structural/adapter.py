"""
================================================================================
Adapter
Category: Structural Design Pattern
Source: https://refactoring.guru/design-patterns/adapter
================================================================================

DEFINITION
----------
Adapter is a structural design pattern that allows objects with incompatible
interfaces to collaborate.

The Adapter acts as a wrapper: it catches calls for one object and transforms
them into a format and interface the second object understands.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Integrates legacy / third-party code without rewriting it.
2. Separates conversion logic from business logic.
3. Lets classes work together that couldn't otherwise due to interface mismatch.
4. Very common in real systems (API wrappers, DB drivers, UI kits).

WHEN TO USE
-----------
- You want to use an existing class whose interface doesn't match yours.
- You need to reuse legacy code with a modern interface.
- You want to create a reusable class that cooperates with unrelated classes.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

class Target:
    """Domain-specific interface used by the client code."""

    def request(self) -> str:
        return "Target: The default target's behavior."


class Adaptee:
    """Useful behavior, but incompatible interface."""

    def specific_request(self) -> str:
        return ".eetpadA eht fo roivaheb laicepS"


class Adapter(Target):
    """Makes Adaptee compatible with Target via composition."""

    def __init__(self, adaptee: Adaptee) -> None:
        self.adaptee = adaptee

    def request(self) -> str:
        return f"Adapter: (TRANSLATED) {self.adaptee.specific_request()[::-1]}"


def client_code(target: Target) -> None:
    print(target.request(), end="")


if __name__ == "__main__":
    print("Client: I can work just fine with the Target objects:")
    client_code(Target())
    print("\n")

    adaptee = Adaptee()
    print("Client: The Adaptee class has a weird interface.")
    print(f"Adaptee: {adaptee.specific_request()}", end="\n\n")

    print("Client: But I can work with it via the Adapter:")
    client_code(Adapter(adaptee))

