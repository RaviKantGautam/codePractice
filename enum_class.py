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