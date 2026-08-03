"""
================================================================================
Proxy
Category: Structural Design Pattern
Source: https://refactoring.guru/design-patterns/proxy
================================================================================

DEFINITION
----------
Proxy is a structural design pattern that lets you provide a substitute or
placeholder for another object. A proxy controls access to the original object,
allowing you to perform something either before or after the request goes to it.

Common variants: remote proxy, virtual (lazy) proxy, protection proxy, caching proxy.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Controls access without changing the real subject's code.
2. Adds cross-cutting concerns: logging, caching, auth, lazy loading.
3. Same interface as the real object — interchangeable for clients.
4. Open/Closed friendly — extend behavior via proxy wrappers.

WHEN TO USE
-----------
- Lazy initialization of expensive objects.
- Access control / security checks.
- Logging, caching, or rate-limiting requests.
- Local representation of a remote service.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

from abc import ABC, abstractmethod


class Subject(ABC):
    @abstractmethod
    def request(self) -> None:
        pass


class RealSubject(Subject):
    def request(self) -> None:
        print("RealSubject: Handling request.")


class Proxy(Subject):
    def __init__(self, real_subject: RealSubject) -> None:
        self._real_subject = real_subject

    def request(self) -> None:
        if self.check_access():
            self._real_subject.request()
            self.log_access()

    def check_access(self) -> bool:
        print("Proxy: Checking access prior to firing a real request.")
        return True

    def log_access(self) -> None:
        print("Proxy: Logging the time of request.", end="")


def client_code(subject: Subject) -> None:
    subject.request()


if __name__ == "__main__":
    print("Client: Executing the client code with a real subject:")
    real_subject = RealSubject()
    client_code(real_subject)
    print("")

    print("Client: Executing the same client code with a proxy:")
    client_code(Proxy(real_subject))

