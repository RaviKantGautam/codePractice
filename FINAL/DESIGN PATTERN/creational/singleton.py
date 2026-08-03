"""
================================================================================
Singleton
Category: Creational Design Pattern
Source: https://refactoring.guru/design-patterns/singleton
================================================================================

DEFINITION
----------
Singleton is a creational design pattern that lets you ensure that a class has
only one instance, while providing a global access point to this instance.

It is handy for shared resources (config, logger, connection pool), but can
hurt modularity and testability — many treat it as an antipattern when overused.

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Guarantees a single shared instance.
2. Provides a global access point.
3. Lazily initializes expensive shared resources.
4. Caution: can hide dependencies and complicate unit testing.

WHEN TO USE
-----------
- A class should have exactly one instance (e.g., a single DB connection manager).
- You need stricter control than a simple global variable.
- Prefer dependency injection when testability matters more.

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

class SingletonMeta(type):
    """
    Singleton via metaclass. Some alternatives: base class, decorator, module-level.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Singleton(metaclass=SingletonMeta):
    def some_business_logic(self):
        # ... any shared business logic ...
        pass


if __name__ == "__main__":
    s1 = Singleton()
    s2 = Singleton()

    if id(s1) == id(s2):
        print("Singleton works, both variables contain the same instance.")
    else:
        print("Singleton failed, variables contain different instances.")

