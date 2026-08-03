"""
================================================================================
L — Liskov Substitution Principle (LSP)
================================================================================

DEFINITION
----------
Subtypes must be substitutable for their base types without breaking the
program's correctness.

If class B inherits from class A, then anywhere A is expected, B should work
without surprising the caller — same contract, same expectations.

WHY IT MATTERS (Interview talking points)
-----------------------------------------
1. Inheritance stays safe and predictable.
2. Polymorphism works correctly (callers don't need special-case checks).
3. Prevents "is-a" misuse — inheritance is about behavior, not just names.
4. Forces you to design meaningful base-class contracts.

KEY PHRASE TO REMEMBER
----------------------
"A child class must honor the parent's promises."

CLASSIC VIOLATION
-----------------
Rectangle / Square problem:
- Rectangle allows independent width and height.
- Square forces width == height.
- Code written for Rectangle breaks when given a Square.

HOW TO DETECT VIOLATIONS
------------------------
- Subclass raises NotImplementedError / UnsupportedOperation for parent methods
- Subclass strengthens preconditions (accepts fewer inputs)
- Subclass weakens postconditions (returns less than promised)
- Callers use isinstance() checks to special-case subclasses
- "is-a" by name, but not by behavior

RULES OF THUMB
--------------
1. Don't force subclasses to implement irrelevant methods.
2. Prefer composition over inheritance when "is-a" is shaky.
3. Keep method contracts consistent across the hierarchy.

REAL-WORLD ANALOGY
------------------
If a company hires a "Driver", any substitute driver must be able to drive.
Hiring someone who cannot drive breaks the contract — even if they are
labeled "Employee".

INTERVIEW QUICK ANSWERS
-----------------------
Q: What is LSP?
A: Objects of a superclass should be replaceable with objects of a subclass
   without breaking the application.

Q: How is LSP different from inheritance?
A: Inheritance is a language feature. LSP is a behavioral contract that
   inheritance must satisfy to be correct.

Q: What if a subclass can't support a parent method?
A: The hierarchy is wrong. Redesign the base type (smaller interface)
   or use composition instead of inheritance.

Q: Famous example?
A: Square inheriting from Rectangle, or Ostrich inheriting from Bird.fly().
"""

from abc import ABC, abstractmethod


# =============================================================================
# BAD EXAMPLE — Violates LSP (Bird / Ostrich)
# Caller assumes every Bird can fly. Ostrich breaks that assumption.
# =============================================================================

class BadBird:
    def fly(self) -> str:
        return "Flying..."


class BadSparrow(BadBird):
    def fly(self) -> str:
        return "Sparrow is flying"


class BadOstrich(BadBird):
    def fly(self) -> str:
        # Breaks the parent's contract — callers of BadBird.fly() will crash
        raise NotImplementedError("Ostrich cannot fly")


def make_bird_fly(bird: BadBird) -> None:
    print(bird.fly())  # Unsafe if bird is BadOstrich


# =============================================================================
# GOOD EXAMPLE — Follows LSP
# Split capabilities. Only flying birds expose fly().
# Substituting any FlyingBird is safe.
# =============================================================================

class Bird(ABC):
    @abstractmethod
    def move(self) -> str:
        ...


class FlyingBird(Bird):
    @abstractmethod
    def fly(self) -> str:
        ...

    def move(self) -> str:
        return self.fly()


class WalkingBird(Bird):
    @abstractmethod
    def walk(self) -> str:
        ...

    def move(self) -> str:
        return self.walk()


class Sparrow(FlyingBird):
    def fly(self) -> str:
        return "Sparrow is flying"


class Eagle(FlyingBird):
    def fly(self) -> str:
        return "Eagle is soaring"


class Ostrich(WalkingBird):
    def walk(self) -> str:
        return "Ostrich is running"


def start_migration(bird: FlyingBird) -> None:
    """Safe: only accepts birds that truly can fly."""
    print(bird.fly())


def start_journey(bird: Bird) -> None:
    """Safe: every Bird can move() somehow."""
    print(bird.move())


# =============================================================================
# ANOTHER CLASSIC: Rectangle / Square (commented for study)
# -----------------------------------------------------------------------------
# class Rectangle:
#     def __init__(self, w, h): self.w, self.h = w, h
#     def set_width(self, w): self.w = w
#     def set_height(self, h): self.h = h
#     def area(self): return self.w * self.h
#
# class Square(Rectangle):  # BAD — breaks set_width / set_height independence
#     def set_width(self, w): self.w = self.h = w
#     def set_height(self, h): self.w = self.h = h
#
# Fix: don't inherit Square from Rectangle. Share a Shape interface instead.
# =============================================================================


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("--- BAD (Ostrich breaks Bird.fly contract) ---")
    make_bird_fly(BadSparrow())
    try:
        make_bird_fly(BadOstrich())
    except NotImplementedError as exc:
        print(f"LSP violation caught: {exc}")

    print("\n--- GOOD (safe substitution) ---")
    start_migration(Sparrow())
    start_migration(Eagle())
    start_journey(Sparrow())
    start_journey(Ostrich())
