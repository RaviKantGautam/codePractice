class MyMeta(type):
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