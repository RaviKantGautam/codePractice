from enum import Enum

class Color(Enum):
    RED = "Red"
    GREEN = "Green"

color = Color.RED
print(type(color))
print(dir(color))
print(color.name)

'''
Why Use Enums? 
In Python, the enum class is used to create enumerations, which are sets of symbolic names bound to unique, constant values

Readability: Replaces obscure values with descriptive names (e.g., Status.PENDING instead of 3).Type Safety: Enums prevent you from accidentally typing an invalid value or mixing up variable types.Immutability: Enum values are constants; they cannot be reassigned or modified at runtime.Iteration & Lookups: You can easily loop through all possible options or look up a name by its value. [1] (https://mimo.org/glossary/python/enum), [2] (https://arjancodes.com/blog/python-enum-classes-for-managing-constants/), [3] (https://www.youtube.com/watch?v=4JvIO8YC3hA&t=3), [4] (https://www.geeksforgeeks.org/python/enum-in-python/), [5] (https://realpython.com/python-enum/)

'''

from dataclasses import dataclass

@dataclass
class Point:
    '''
    what is dataclass
    A dataclass automatically generates special methods like __init__(), __repr__(), and __eq__() for the class based on its fields.
    '''
    x: float
    y: float

    def distance_to_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

point = Point(3, 4)
print(point.distance_to_origin())