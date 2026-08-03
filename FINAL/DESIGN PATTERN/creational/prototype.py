"""
================================================================================
Prototype
Category: Creational Design Pattern
Source: https://refactoring.guru/design-patterns/prototype
================================================================================

DEFINITION
----------
Prototype is a creational design pattern that lets you copy existing objects
without making your code dependent on their classes.

All prototype classes share a common interface for cloning. Python provides
this out of the box via the `copy` module (`copy.copy` / `copy.deepcopy`).

WHY IT MATTERS / IMPORTANCE
---------------------------
1. Clone complex objects without coupling to their concrete classes.
2. Avoid expensive re-initialization when copying similar objects.
3. Produce objects with nested structures and circular references safely (deepcopy).
4. Built into Python via the copy module.

WHEN TO USE
-----------
- Creating an object is more expensive than copying an existing one.
- You want to avoid a hierarchy of factories for product subclasses.
- Objects have private fields that should be copied (same-class access).

INTERVIEW TIP
-------------
Explain the problem first, then the pattern solution, then walk through the code.
Mention real-world use cases from your projects if possible.
"""

# Conceptual Python example adapted from Refactoring.Guru
# https://refactoring.guru/design-patterns

import copy


class SelfReferencingEntity:
    def __init__(self):
        self.parent = None

    def set_parent(self, parent):
        self.parent = parent


class SomeComponent:
    """
    Python provides Prototype via `copy.copy` and `copy.deepcopy`.
    Override `__copy__` / `__deepcopy__` for custom cloning behavior.
    """

    def __init__(self, some_int, some_list_of_objects, some_circular_ref):
        self.some_int = some_int
        self.some_list_of_objects = some_list_of_objects
        self.some_circular_ref = some_circular_ref

    def __copy__(self):
        some_list_of_objects = copy.copy(self.some_list_of_objects)
        some_circular_ref = copy.copy(self.some_circular_ref)
        new = self.__class__(self.some_int, some_list_of_objects, some_circular_ref)
        new.__dict__.update(self.__dict__)
        return new

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        some_list_of_objects = copy.deepcopy(self.some_list_of_objects, memo)
        some_circular_ref = copy.deepcopy(self.some_circular_ref, memo)
        new = self.__class__(self.some_int, some_list_of_objects, some_circular_ref)
        new.__dict__ = copy.deepcopy(self.__dict__, memo)
        return new


if __name__ == "__main__":
    list_of_objects = [1, {1, 2, 3}, [1, 2, 3]]
    circular_ref = SelfReferencingEntity()
    component = SomeComponent(23, list_of_objects, circular_ref)
    circular_ref.set_parent(component)

    shallow_copied_component = copy.copy(component)
    shallow_copied_component.some_list_of_objects.append("another object")
    if component.some_list_of_objects[-1] == "another object":
        print("Shallow copy shares nested list reference.")
    else:
        print("Shallow copy does not share nested list reference.")

    component.some_list_of_objects[1].add(4)
    if 4 in shallow_copied_component.some_list_of_objects[1]:
        print("Shallow copy shares nested mutable objects.")
    else:
        print("Shallow copy does not share nested mutable objects.")

    deep_copied_component = copy.deepcopy(component)
    deep_copied_component.some_list_of_objects.append("one more object")
    if component.some_list_of_objects[-1] == "one more object":
        print("Deep copy unexpectedly shares list.")
    else:
        print("Deep copy has an independent nested list.")

    component.some_list_of_objects[1].add(10)
    if 10 in deep_copied_component.some_list_of_objects[1]:
        print("Deep copy unexpectedly shares nested set.")
    else:
        print("Deep copy has an independent nested set.")

