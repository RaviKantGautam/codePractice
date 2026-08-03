"""
================================================================================
S — Single Responsibility Principle (SRP)
================================================================================

DEFINITION
----------
A class should have only ONE reason to change.

In other words: a class should do one job only. If you find yourself using
the word "and" when describing what a class does ("it validates AND saves AND
emails"), that class likely violates SRP.

WHY IT MATTERS (Interview talking points)
-----------------------------------------
1. Easier to understand — each class has a clear purpose.
2. Easier to test — you can unit-test one concern in isolation.
3. Safer to change — modifying email logic won't accidentally break DB saves.
4. Better teamwork — different developers can own different responsibilities.

KEY PHRASE TO REMEMBER
----------------------
"One class = one responsibility = one reason to change."

HOW TO DETECT VIOLATIONS
------------------------
- Class name is vague: Manager, Handler, Util, Helper
- Class has many unrelated methods
- Changing one feature forces edits in the same class for unrelated features
- Hard to write focused unit tests

REAL-WORLD ANALOGY
------------------
A chef cooks. A waiter serves. A cashier bills.
If one person does all three, any change (new menu / new payment / new seating)
affects that single overloaded person.

INTERVIEW QUICK ANSWERS
-----------------------
Q: What is SRP?
A: A class should have only one reason to change / one responsibility.

Q: Does SRP mean a class can have only one method?
A: No. Multiple methods are fine if they serve the SAME responsibility.
   e.g. UserRepository can have save(), find(), delete() — all about persistence.

Q: How is SRP related to cohesion?
A: High cohesion = methods in a class are closely related = supports SRP.

Q: Common mistake?
A: Splitting too aggressively into tiny classes that create unnecessary complexity.
   Aim for "one reason to change", not "one method per class".
"""


# =============================================================================
# BAD EXAMPLE — Violates SRP
# UserService does THREE jobs: validation, persistence, and notification.
# Reasons to change: validation rules OR DB schema OR email template.
# =============================================================================

class BadUserService:
    def create_user(self, name: str, email: str) -> dict:
        # Responsibility 1: validation
        if not name or "@" not in email:
            raise ValueError("Invalid user data")

        # Responsibility 2: persistence
        user = {"name": name, "email": email}
        print(f"[DB] Saving user: {user}")

        # Responsibility 3: notification
        print(f"[EMAIL] Welcome mail sent to {email}")

        return user


# =============================================================================
# GOOD EXAMPLE — Follows SRP
# Each class has a single responsibility and a single reason to change.
# =============================================================================

class UserValidator:
    """Only validates user input. Changes when validation rules change."""

    def validate(self, name: str, email: str) -> None:
        if not name:
            raise ValueError("Name is required")
        if "@" not in email:
            raise ValueError("Invalid email")


class UserRepository:
    """Only persists users. Changes when storage mechanism changes."""

    def save(self, name: str, email: str) -> dict:
        user = {"name": name, "email": email}
        print(f"[DB] Saving user: {user}")
        return user


class EmailNotifier:
    """Only sends emails. Changes when notification channel/template changes."""

    def send_welcome(self, email: str) -> None:
        print(f"[EMAIL] Welcome mail sent to {email}")


class UserService:
    """
    Orchestrates the flow — does NOT own validation, storage, or email logic.
    Coordinates other single-purpose collaborators.
    """

    def __init__(
        self,
        validator: UserValidator,
        repository: UserRepository,
        notifier: EmailNotifier,
    ) -> None:
        self._validator = validator
        self._repository = repository
        self._notifier = notifier

    def create_user(self, name: str, email: str) -> dict:
        self._validator.validate(name, email)
        user = self._repository.save(name, email)
        self._notifier.send_welcome(email)
        return user


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("--- BAD (one class, many jobs) ---")
    BadUserService().create_user("Ravi", "ravi@example.com")

    print("\n--- GOOD (one class, one job) ---")
    service = UserService(UserValidator(), UserRepository(), EmailNotifier())
    service.create_user("Ravi", "ravi@example.com")
