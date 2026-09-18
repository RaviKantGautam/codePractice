class MyMeta(type):
    # A metaclass is the class used to create and control other classes. Just as a class defines how objects are created, a metaclass defines how classes are created. Python’s default metaclass is type. Custom metaclasses can intercept class creation to modify classes, enforce rules, register classes, or generate class-level behavior.
    def __new__(cls, name, bases, attrs):
        attrs['new_attribute'] = 'Hello, World!'
        return super().__new__(cls, name, bases, attrs)

class MyClass(metaclass=MyMeta):
    t_1 = "Kya baat hai!"
    def __init__(self) -> None:
        self.default_name = "Hello Bhai"

class ChildClass(MyClass):
    pass


obj = ChildClass()
print(obj.new_attribute)
print(obj.default_name)
print(obj.t_1)