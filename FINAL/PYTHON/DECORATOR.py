'''
Build-in decorator example in Python

@classmethod
: Binds a method to the class rather than its object instances. It passes the class (cls) as the first argument, making it great for creating alternative constructors.

@staticmethod
: Defines a method that doesn't operate on an instance or class. It doesn't take self or cls as the first argument, making it suitable for utility functions related to the class.

@property
: Allows a method to be accessed like an attribute. It is commonly used to define read-only attributes or computed properties.

@dataclass
: Automatically generates special methods like __init__(), __repr__(), and __eq__() for classes, reducing boilerplate code.

@contextmanager
: Used to define a context manager, which allows you to allocate and release resources precisely when you want to. It is commonly used with the with statement.

@abstractmethod
: Indicates that a method must be implemented by any subclass. It is used within abstract base classes to define methods that derived classes are required to override.

@lru_cache
: Caches the results of a function based on its arguments, improving performance for expensive or frequently called functions with the same inputs.

@singledispatch
: Transforms a function into a single-dispatch generic function. It allows you to define a default implementation and register additional implementations for different types.

from functools import lru_cache, singledispatch
from dataclasses import dataclass
from contextlib import contextmanager
from abc import abstractmethod
'''

def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before the function call")
        result = func(*args, **kwargs)
        print("After the function call")
        return result
    return wrapper


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            cls_name = args[0].__class__.__name__ if args else "UnknownClass"
            print(f"[{cls_name}.{func.__name__}] Exception handled: {e}")
            return None
    return wrapper

@my_decorator
@repeat(3)
def say_hello():
    print("Hello!")


class Calculator:
    @handle_exceptions
    def divide(self, a, b):
        return a / b


class AdvancedCalculator(Calculator):
    @handle_exceptions
    def square_root(self, value):
        if value < 0:
            raise ValueError("Cannot take square root of a negative number")
        return value ** 0.5




# say_hello()

calc = Calculator()
print("Division result:", calc.divide(10, 2))
print("Division result:", calc.divide(10, 0))

adv_calc = AdvancedCalculator()
print("Square root result:", adv_calc.square_root(25))
print("Square root result:", adv_calc.square_root(-4))