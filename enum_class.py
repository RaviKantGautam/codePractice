from enum import Enum

class Color(Enum):
    RED = "Red"
    GREEN = "Green"

color = Color.RED
print(type(color))
print(dir(color))
print(color.name)