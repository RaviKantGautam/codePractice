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

'''
Metaclasses are one of Python’s more advanced concepts, but the core idea is actually simple:

A metaclass is the class of a class.

We normally say:

* An object is an instance of a class.
* A class is an instance of a metaclass.

1. Normal class/object relationship

class User:
    pass
user = User()

Here:

user
  ↓ instance of
User
  ↓ instance of
type

You can verify this:

print(type(user))
# <class '__main__.User'>
print(type(User))
# <class 'type'>

So User itself is an object, and its type is type.

⸻

2. What is type?

type is Python’s built-in metaclass.

When you write:

class User:
    name = "Ravi"

Python internally creates the User class using type.

Conceptually, this:

class User:
    name = "Ravi"

is roughly equivalent to:

User = type(
    "User",
    (),
    {
        "name": "Ravi"
    }
)

You can actually do this:

def say_hello(self):
    return "Hello"
User = type(
    "User",
    (),
    {
        "name": "Ravi",
        "say_hello": say_hello
    }
)
user = User()
print(user.name)
# Ravi
print(user.say_hello())
# Hello

So type is capable of creating classes dynamically.

⸻

3. Then what is a custom metaclass?

A custom metaclass allows you to control how classes themselves are created.

For example:

class MyMeta(type):
    def __new__(cls, name, bases, attrs):
        print(f"Creating class: {name}")
        return super().__new__(cls, name, bases, attrs)
class User(metaclass=MyMeta):
    pass

When Python executes this:

class User(metaclass=MyMeta):
    pass

the metaclass gets involved in creating User.

Output:

Creating class: User

The relationship becomes:

user
  ↓
User
  ↓
MyMeta
  ↓
type

More accurately:

type(user) is User
type(User) is MyMeta

⸻

4. Why would we need metaclasses?

This is where metaclasses become useful.

A metaclass can enforce rules whenever a class is created.

For example, suppose you want every class in your application to have a created_by attribute.

class MyMeta(type):
    def __new__(cls, name, bases, attrs):
        attrs["created_by"] = "MyMeta"
        return super().__new__(cls, name, bases, attrs)
class User(metaclass=MyMeta):
    pass
class Product(metaclass=MyMeta):
    pass
print(User.created_by)
print(Product.created_by)

Output:

MyMeta
MyMeta

The metaclass modified the classes at class creation time.

⸻

5. A more practical example: enforcing class rules

Imagine you’re building a framework and want every model to define a table_name.

You could create:

class ModelMeta(type):
    def __new__(cls, name, bases, attrs):
        if name != "BaseModel" and "table_name" not in attrs:
            raise TypeError(
                f"{name} must define table_name"
            )
        return super().__new__(cls, name, bases, attrs)
class BaseModel(metaclass=ModelMeta):
    pass

Now:

class User(BaseModel):
    table_name = "users"

works.

But:

class Product(BaseModel):
    pass

raises:

TypeError: Product must define table_name

This is a powerful use case because the rule is enforced when the class is defined, rather than later at runtime.

⸻

6. __new__ vs __init__ in a metaclass

You’ll commonly see:

class MyMeta(type):
    def __new__(cls, name, bases, attrs):
        return super().__new__(cls, name, bases, attrs)
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)

The distinction is:

__new__

Responsible for creating the class object.

def __new__(cls, name, bases, attrs):

Think:

“Create the class.”

__init__

Responsible for initializing the already-created class object.

Think:

“Configure the class.”

For metaclass interview questions, this distinction is important.

⸻

7. Metaclass vs decorator

This is a common interview discussion.

A class decorator:

def add_feature(cls):
    cls.version = 1
    return cls
@add_feature
class User:
    pass

can modify a class.

A metaclass:

class MyMeta(type):
    def __new__(cls, name, bases, attrs):
        attrs["version"] = 1
        return super().__new__(cls, name, bases, attrs)
class User(metaclass=MyMeta):
    pass

also modifies a class.

The difference is that a metaclass controls class creation itself, whereas a decorator operates on the class after it has been created.

⸻

8. Where are metaclasses actually used?

You don’t normally need to create custom metaclasses in everyday Python development.

They’re mainly useful for frameworks and libraries.

Some important examples include:

Django

Django makes heavy use of metaclasses internally.

For example:

class User(models.Model):
    name = models.CharField(max_length=100)

Django needs to inspect the class definition and turn things like:

name = models.CharField(...)

into metadata used by the ORM.

This contributes to Django’s powerful declarative model system.

Other examples

Metaclasses are commonly used for:

* ORM frameworks
* API frameworks
* plugin systems
* automatic class registration
* validation frameworks
* enforcing class-level conventions
* automatically generating metadata
* implementing declarative APIs

⸻

9. The three-level hierarchy

This is the part I’d remember for an interview:

Object
   ↓
Class
   ↓
Metaclass

For example:

class User:
    pass
user = User()

Then:

type(user)
# User
type(User)
# type

And:

type(type)
# type

That last one looks strange, but it’s valid:

type(type) is type
# True

type is effectively an instance of itself.

⸻

10. Interview-ready definition

If an interviewer asks:

“What is a metaclass in Python?”

A strong answer would be:

A metaclass is the class used to create and control other classes. Just as a class defines how objects are created, a metaclass defines how classes are created. Python’s default metaclass is type. Custom metaclasses can intercept class creation to modify classes, enforce rules, register classes, or generate class-level behavior.

And if they ask for an example:

class Meta(type):
    def __new__(cls, name, bases, attrs):
        print(f"Creating {name}")
        return super().__new__(cls, name, bases, attrs)
class User(metaclass=Meta):
    pass

The key line to remember is:

type(user) == User
type(User) == Meta

Simple mental model:

Class → creates objects
Metaclass → creates classes
'''