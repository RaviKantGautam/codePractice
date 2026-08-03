'''
The SOLID principles are five design guidelines that help developers create more maintainable, scalable, and flexible software. They are commonly applied in object-oriented design and are considered fundamental to writing clean, robust code. Here’s what each principle stands for:

1. S - Single Responsibility Principle (SRP)
    Definition: A class should have only one reason to change, meaning it should have only one job or responsibility.
    Benefit: This makes the class simpler, easier to understand, and maintain. It also reduces the likelihood of introducing bugs when modifying the class.
    Example: If a class handles both user authentication and email notifications, splitting it into two classes — one for authentication and one for email notifications — follows SRP.
2. O - Open/Closed Principle (OCP)
    Definition: Software entities (classes, modules, functions) should be open for extension but closed for modification.
    Benefit: You can add new functionality without altering existing code, which reduces the risk of introducing bugs and makes the code more adaptable to future changes.
    Example: If you need to add a new payment method in a system, rather than modifying the existing payment processing class, you can extend it by adding new subclasses.
3. L - Liskov Substitution Principle (LSP)
    Definition: Objects of a superclass should be replaceable with objects of a subclass without affecting the correctness of the program.
    Benefit: Ensures that derived classes extend functionality without breaking the functionality of the base class.
    Example: If a Bird class has a fly() method, and a subclass Penguin does not support flying, then Penguin should not inherit from Bird because it violates LSP.
4. I - Interface Segregation Principle (ISP)
    Definition: A client should not be forced to depend on methods it does not use. Instead of one large interface, smaller and more specific interfaces should be created.
    Benefit: Reduces unnecessary dependencies and makes the code easier to implement and maintain.
    Example: Rather than having a large interface like IMachine with methods for print(), scan(), and fax(), split it into smaller interfaces like IPrinter, IScanner, and IFax.
5. D - Dependency Inversion Principle (DIP)
    Definition: High-level modules should not depend on low-level modules; both should depend on abstractions. Additionally, abstractions should not depend on details; details should depend on abstractions.
    Benefit: Promotes loose coupling between classes and improves flexibility by allowing code to depend on interfaces rather than specific implementations.
    Example: Rather than having a class depend directly on a MySQLDatabase class, it should depend on a Database interface, allowing for easy substitution of other database types like PostgreSQL.

Summary of SOLID Principles:
    S: One class, one responsibility.
    O: Add new functionality by extending, not modifying.
    L: Subclasses should be replaceable with their parent classes.
    I: Create specific, client-focused interfaces.
    D: Depend on abstractions (interfaces), not concrete implementations.
'''


'''
1. S - Single Responsibility Principle (SRP)
'''




from abc import ABC, abstractmethod
class Shape:
    def __init__(self, name) -> None:
        self.name = name


class Circle(Shape):
    def __init__(self, radius) -> None:
        super().__init__('Circle')
        self.radius = radius


class Square(Shape):
    def __init__(self, side) -> None:
        super().__init__('Square')
        self.side = side


class AreaCalculate:

    @staticmethod
    def calculate_circle_area(circle):
        return 3.14159 * (circle.radius ** 2)


class VolumeCalculate:

    @staticmethod
    def calculate_square_area(square):
        return square.side*square.side


circle = Circle(5)
square = Square(5)

area = AreaCalculate()
area_calculator = area.calculate_circle_area(circle=circle)
print(f"This is the area of circle of raduis 5: {area_calculator}")

volume = VolumeCalculate()
volume_calculator = volume.calculate_square_area(square=square)
print(f"This is the area of Square of square of side 5: {volume_calculator}")


'''
2. O - Open/Closed Principle (OCP)
'''


class Shape(ABC):
    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def volume(self):
        pass


class Circle(Shape):
    def __init__(self, radius) -> None:
        super().__init__('Circle')
        self.radius = radius

    def area(self):
        return 3.14159 * (self.radius ** 2)

    def volume(self):
        return None


class Square(Shape):
    def __init__(self, side) -> None:
        super().__init__('Square')
        self.side = side

    def area(self):
        return self.side*self.side

    def volume(self):
        return None


class Cube(Shape):
    def __init__(self, side) -> None:
        super().__init__('Cube')
        self.side = side

    def area(self):
        return self.side*self.side

    def volume(self):
        return self.side*self.side*self.side


class Calculator:
    @staticmethod
    def calculate_area(shape):
        return shape.area()

    @staticmethod
    def calculate_volume(shape):
        return shape.volume()


circle = Circle(5)
cube = Cube(4)

c = Calculator()
print(
    f"This is the area and volume of circele area = {c.calculate_area(circle)} and volume = {c.calculate_volume(circle)}")
print(
    f"This is the area and volume of a cube area = {c.calculate_area(cube)} and volume = {c.calculate_volume(cube)}")


'''
3. L - Liskov Substitution Principle (LSP)
'''


class Shape(ABC):
    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def area(self):
        pass


class Shape2D(Shape):
    def __init__(self, name) -> None:
        super().__init__(name)


class Shape3D(Shape):
    def __init__(self, name) -> None:
        super().__init__(name)

    @abstractmethod
    def volume(self):
        pass


class Circle(Shape2D):
    def __init__(self, radius) -> None:
        super().__init__('Circle')
        self.radius = radius

    def area(self):
        return 3.14159 * (self.radius ** 2)


class Cube(Shape3D):
    def __init__(self, side) -> None:
        super().__init__('Cube')
        self.side = side

    def area(self):
        return self.side*self.side

    def volume(self):
        return self.side*self.side*self.side


class AreaCalculator:
    @staticmethod
    def calculate_area(shape):
        return shape.area()


class VolumeCalculator:
    @staticmethod
    def calculate_volume(shape):
        if isinstance(shape, Shape3D):
            return shape.volume()
        else:
            raise TypeError("Volume can only be calculated over 3d shapes.")


circle = Circle(5)
cube = Cube(4)

lsparea = AreaCalculator()
lspvolume = VolumeCalculator()

print(lsparea.calculate_area(circle))
print(lspvolume.calculate_volume(cube))


'''
4. I - Interface Segregation Principle (ISP)
'''


class AreaInterace(ABC):

    @abstractmethod
    def area(self):
        pass


class VolumeInterface(ABC):

    @abstractmethod
    def volume(self):
        pass


class Circle(AreaInterace):
    def __init__(self, radius) -> None:
        self.radius = radius

    def area(self):
        return 3.14 * (self.radius**2)


class Cube(AreaCalculate, VolumeCalculate):
    def __init__(self, side) -> None:
        self.side = side

    def area(self):
        return self.side*self.side

    def volume(self):
        return self.side*self.side*self.side


class AreaCalculator:

    @staticmethod
    def calculate_area(shape: AreaInterace):
        return shape.area()


class VolumeCalculator:

    @staticmethod
    def calculate_volume(shape: VolumeInterface):
        return shape.volume()


circle = Circle(5)
cube = Cube(4)

area = AreaCalculator()
print(area.calculate_area(circle))

volume = VolumeCalculator()
print(volume.calculate_volume(cube))


'''
5. D - Dependency Inversion Principle (DIP)
'''


class AreaInterace(ABC):

    @abstractmethod
    def area(self):
        pass


class VolumeInterface(ABC):

    @abstractmethod
    def volume(self):
        pass


class Circle(AreaInterace):
    def __init__(self, radius) -> None:
        self.radius = radius

    def area(self):
        return 3.14 * (self.radius**2)


class Cube(AreaCalculate, VolumeCalculate):
    def __init__(self, side) -> None:
        self.side = side

    def area(self):
        return self.side*self.side

    def volume(self):
        return self.side*self.side*self.side


class AreaCalculator:
    def __init__(self, shape: AreaInterace) -> None:
        self.shape = shape

    def calculate_area(self):
        return self.shape.area()


class VolumeCalculator:
    def __init__(self, shape: VolumeInterface) -> None:
        self.shape = shape

    def calculate_volume(self):
        return self.shape.volume()


circle = Circle(5)
cube = Cube(4)

area = AreaCalculator(circle)
print(area.calculate_area())

volume = VolumeCalculator(cube)
print(volume.calculate_volume())
