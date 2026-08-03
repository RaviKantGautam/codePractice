"""
================================================================================
O — Open/Closed Principle (OCP)
================================================================================

DEFINITION
----------
Software entities (classes, modules, functions) should be OPEN for extension
but CLOSED for modification.

Meaning:
- OPEN for extension  → you can add new behavior
- CLOSED for modification → you should NOT keep editing existing working code

WHY IT MATTERS (Interview talking points)
-----------------------------------------
1. Reduces risk — stable code stays untouched when adding features.
2. Supports growth — new payment methods / shapes / report formats plug in cleanly.
3. Encourages polymorphism and abstraction over if/elif ladders.
4. Makes the system more maintainable and testable.

KEY PHRASE TO REMEMBER
----------------------
"Add new code to add new behavior — don't rewrite old code."

HOW TO DETECT VIOLATIONS
------------------------
- Long if/elif/else or switch/match chains for types
- Every new feature requires editing a central "god" class
- Existing unit tests break whenever you add a new case

HOW TO FOLLOW OCP
-----------------
- Depend on abstractions (interfaces / base classes / protocols)
- Use strategy, plugin, or factory patterns
- New behavior = new class implementing the same interface

REAL-WORLD ANALOGY
------------------
A power strip has sockets. You plug in new devices (extension)
without rewiring the strip itself (no modification).

INTERVIEW QUICK ANSWERS
-----------------------
Q: What is OCP?
A: Open for extension, closed for modification.

Q: How do you achieve OCP in practice?
A: Program to interfaces; add new implementations instead of editing old ones.

Q: Does OCP mean never change any file?
A: No. Bug fixes and intentional redesigns are fine. OCP targets avoiding
   repeated edits to stable logic every time a NEW variant is added.

Q: Common violation?
A: Growing if-elif chains inside DiscountCalculator / PaymentProcessor / etc.
"""

from abc import ABC, abstractmethod


# =============================================================================
# BAD EXAMPLE — Violates OCP
# Every new discount type forces you to MODIFY DiscountCalculator.
# =============================================================================

class BadDiscountCalculator:
    def calculate(self, price: float, customer_type: str) -> float:
        if customer_type == "regular":
            return price
        elif customer_type == "premium":
            return price * 0.9
        elif customer_type == "vip":
            return price * 0.8
        # Adding "student" means editing THIS method again → OCP broken
        else:
            raise ValueError(f"Unknown customer type: {customer_type}")


# =============================================================================
# GOOD EXAMPLE — Follows OCP
# New discount strategies are added as NEW classes.
# DiscountCalculator never needs to change.
# =============================================================================

class DiscountStrategy(ABC):
    """Abstraction — closed core depends on this, not on concrete types."""

    @abstractmethod
    def apply(self, price: float) -> float:
        ...


class RegularDiscount(DiscountStrategy):
    def apply(self, price: float) -> float:
        return price


class PremiumDiscount(DiscountStrategy):
    def apply(self, price: float) -> float:
        return price * 0.9


class VipDiscount(DiscountStrategy):
    def apply(self, price: float) -> float:
        return price * 0.8


# NEW behavior later — only ADD this class. No change to DiscountCalculator.
class StudentDiscount(DiscountStrategy):
    def apply(self, price: float) -> float:
        return price * 0.85


class DiscountCalculator:
    """Closed for modification — open for extension via new strategies."""

    def calculate(self, price: float, strategy: DiscountStrategy) -> float:
        return strategy.apply(price)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    price = 1000.0
    calculator = DiscountCalculator()

    print("--- BAD (edit class for every new type) ---")
    print("Premium:", BadDiscountCalculator().calculate(price, "premium"))

    print("\n--- GOOD (extend with new classes) ---")
    for strategy in (RegularDiscount(), PremiumDiscount(), VipDiscount(), StudentDiscount()):
        print(f"{strategy.__class__.__name__}: {calculator.calculate(price, strategy)}")
