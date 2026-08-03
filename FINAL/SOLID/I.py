"""
================================================================================
I — Interface Segregation Principle (ISP)
================================================================================

DEFINITION
----------
Clients should not be forced to depend on interfaces they do not use.

Prefer many small, focused interfaces over one large "fat" interface.

WHY IT MATTERS (Interview talking points)
-----------------------------------------
1. Classes implement only what they need — no dummy / empty methods.
2. Changes to unused methods don't ripple into unrelated clients.
3. Clearer design — interfaces express precise capabilities.
4. Works hand-in-hand with LSP (no forced NotImplementedError methods).

KEY PHRASE TO REMEMBER
----------------------
"Many specific interfaces > one general-purpose interface."

HOW TO DETECT VIOLATIONS
------------------------
- Interface has methods that some implementers leave empty / raise errors
- Implementing a class requires methods that are irrelevant to it
- Clients depend on a huge interface but call only 1–2 methods
- "God interface": Worker, Machine, Service with unrelated operations

HOW TO FOLLOW ISP
-----------------
- Split fat interfaces by role/capability
- Use role interfaces: Printable, Scannable, Faxable
- Let classes implement only the interfaces they support

REAL-WORLD ANALOGY
------------------
A restaurant menu is better as sections (starters, mains, drinks)
than one giant unordered list. Customers pick only what they need —
they shouldn't be forced to order everything on the menu.

INTERVIEW QUICK ANSWERS
-----------------------
Q: What is ISP?
A: No client should be forced to depend on methods it does not use.

Q: How is ISP different from SRP?
A: SRP is about a class having one reason to change.
   ISP is about interfaces being slim so clients aren't forced into unused APIs.
   They often appear together but solve different problems.

Q: What is a fat interface?
A: An interface packed with many unrelated methods that not all implementers need.

Q: Common fix?
A: Split into smaller role-based interfaces and compose them as needed.
"""

from abc import ABC, abstractmethod


# =============================================================================
# BAD EXAMPLE — Violates ISP
# MultiFunctionDevice forces EVERY machine to support print + scan + fax.
# SimplePrinter must stub methods it cannot support.
# =============================================================================

class BadMultiFunctionDevice(ABC):
    @abstractmethod
    def print_doc(self, doc: str) -> None:
        ...

    @abstractmethod
    def scan_doc(self, doc: str) -> None:
        ...

    @abstractmethod
    def fax_doc(self, doc: str) -> None:
        ...


class BadAllInOnePrinter(BadMultiFunctionDevice):
    def print_doc(self, doc: str) -> None:
        print(f"Printing: {doc}")

    def scan_doc(self, doc: str) -> None:
        print(f"Scanning: {doc}")

    def fax_doc(self, doc: str) -> None:
        print(f"Faxing: {doc}")


class BadSimplePrinter(BadMultiFunctionDevice):
    def print_doc(self, doc: str) -> None:
        print(f"Printing: {doc}")

    def scan_doc(self, doc: str) -> None:
        # Forced to implement — ISP violation
        raise NotImplementedError("Simple printer cannot scan")

    def fax_doc(self, doc: str) -> None:
        # Forced to implement — ISP violation
        raise NotImplementedError("Simple printer cannot fax")


# =============================================================================
# GOOD EXAMPLE — Follows ISP
# Segregated interfaces. Classes implement only what they can do.
# =============================================================================

class Printer(ABC):
    @abstractmethod
    def print_doc(self, doc: str) -> None:
        ...


class Scanner(ABC):
    @abstractmethod
    def scan_doc(self, doc: str) -> None:
        ...


class Fax(ABC):
    @abstractmethod
    def fax_doc(self, doc: str) -> None:
        ...


class SimplePrinter(Printer):
    def print_doc(self, doc: str) -> None:
        print(f"Printing: {doc}")


class Photocopier(Printer, Scanner):
    def print_doc(self, doc: str) -> None:
        print(f"Printing: {doc}")

    def scan_doc(self, doc: str) -> None:
        print(f"Scanning: {doc}")


class AllInOnePrinter(Printer, Scanner, Fax):
    def print_doc(self, doc: str) -> None:
        print(f"Printing: {doc}")

    def scan_doc(self, doc: str) -> None:
        print(f"Scanning: {doc}")

    def fax_doc(self, doc: str) -> None:
        print(f"Faxing: {doc}")


def send_to_printer(device: Printer, doc: str) -> None:
    """Depends only on Printer — not forced to know about scan/fax."""
    device.print_doc(doc)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("--- BAD (fat interface forces unused methods) ---")
    BadAllInOnePrinter().print_doc("invoice.pdf")
    try:
        BadSimplePrinter().scan_doc("invoice.pdf")
    except NotImplementedError as exc:
        print(f"ISP violation caught: {exc}")

    print("\n--- GOOD (segregated interfaces) ---")
    send_to_printer(SimplePrinter(), "report.pdf")
    send_to_printer(Photocopier(), "report.pdf")
    send_to_printer(AllInOnePrinter(), "report.pdf")

    Photocopier().scan_doc("id-card.pdf")
    AllInOnePrinter().fax_doc("contract.pdf")
