"""
================================================================================
D — Dependency Inversion Principle (DIP)
================================================================================

DEFINITION
----------
1. High-level modules should not depend on low-level modules.
   Both should depend on abstractions.
2. Abstractions should not depend on details.
   Details should depend on abstractions.

In plain English:
Business logic (high-level) should NOT hard-code concrete infrastructure
(low-level: MySQL, SMTP, Stripe). Both should depend on interfaces.

WHY IT MATTERS (Interview talking points)
-----------------------------------------
1. Decouples business rules from databases, APIs, frameworks.
2. Makes code testable — swap real DB with a fake/mock in unit tests.
3. Makes code flexible — change MySQL → MongoDB without rewriting services.
4. Core idea behind Dependency Injection (DI).

KEY PHRASE TO REMEMBER
----------------------
"Depend on abstractions, not on concretions."

IMPORTANT DISTINCTION
---------------------
- Dependency Inversion  = DESIGN principle (who depends on what)
- Dependency Injection  = TECHNIQUE to supply dependencies from outside
  (constructor injection, setter injection, etc.)

DIP is the "why". DI is one common "how".

HOW TO DETECT VIOLATIONS
------------------------
- Service does `from mysql import connector` and uses it directly
- `self.db = MySQLDatabase()` hard-coded inside business class
- Impossible to unit-test without a real database / email server
- Changing storage forces rewriting business logic

HOW TO FOLLOW DIP
-----------------
1. Define an interface / ABC / Protocol for the dependency
2. High-level code depends only on that abstraction
3. Inject concrete implementation from the outside (composition root)

REAL-WORLD ANALOGY
------------------
A laptop depends on a USB-C port (abstraction), not on one brand of charger
(concretion). Any compatible charger can be plugged in.

INTERVIEW QUICK ANSWERS
-----------------------
Q: What is DIP?
A: High-level and low-level modules both depend on abstractions, not on each other.

Q: DIP vs Dependency Injection?
A: DIP is the principle. DI is a pattern/technique used to apply DIP.

Q: DIP vs OCP?
A: Both favor abstractions. OCP focuses on extending without modifying.
   DIP focuses on the direction of dependencies (toward abstractions).

Q: What is a high-level module?
A: Policy / business logic layer (e.g. OrderService), not infrastructure details.
"""

from abc import ABC, abstractmethod


# =============================================================================
# BAD EXAMPLE — Violates DIP
# NotificationService (high-level) depends directly on EmailSender (low-level).
# Switching to SMS requires modifying NotificationService.
# =============================================================================

class BadEmailSender:
    def send(self, message: str) -> None:
        print(f"[EMAIL] {message}")


class BadNotificationService:
    def __init__(self) -> None:
        # Hard dependency on a concrete class → DIP broken
        self._sender = BadEmailSender()

    def notify(self, message: str) -> None:
        self._sender.send(message)


# =============================================================================
# GOOD EXAMPLE — Follows DIP
# Both high-level and low-level depend on MessageSender abstraction.
# Concrete channels are injected from outside.
# =============================================================================

class MessageSender(ABC):
    """Abstraction — high-level policy depends on this."""

    @abstractmethod
    def send(self, message: str) -> None:
        ...


class EmailSender(MessageSender):
    """Low-level detail — depends on the abstraction by implementing it."""

    def send(self, message: str) -> None:
        print(f"[EMAIL] {message}")


class SmsSender(MessageSender):
    def send(self, message: str) -> None:
        print(f"[SMS] {message}")


class SlackSender(MessageSender):
    def send(self, message: str) -> None:
        print(f"[SLACK] {message}")


class NotificationService:
    """
    High-level module.
    Depends on MessageSender abstraction, NOT on Email/SMS/Slack concretions.
    """

    def __init__(self, sender: MessageSender) -> None:
        # Dependency Injection (constructor injection) applying DIP
        self._sender = sender

    def notify(self, message: str) -> None:
        self._sender.send(message)


# Fake for unit tests — no real email/SMS needed
class FakeSender(MessageSender):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("--- BAD (high-level tightly coupled to email) ---")
    BadNotificationService().notify("Order placed")

    print("\n--- GOOD (depend on abstraction, inject details) ---")
    NotificationService(EmailSender()).notify("Order placed")
    NotificationService(SmsSender()).notify("OTP: 4821")
    NotificationService(SlackSender()).notify("Deploy succeeded")

    print("\n--- TESTABILITY benefit ---")
    fake = FakeSender()
    NotificationService(fake).notify("hello")
    assert fake.messages == ["hello"]
    print("FakeSender captured:", fake.messages)
