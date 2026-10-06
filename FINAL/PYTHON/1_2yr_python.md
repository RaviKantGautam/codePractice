# Python Interview Questions & Answers (1–2 Years Experience)

Comprehensive interview questions and answers tailored for junior to associate backend Python developers (1–2 years experience). Topics cover core language mechanics, data structures, OOP fundamentals, common traps, the standard library, and hands-on scenario-based problem solving.

---

## Section 1: Core Fundamentals & Data Structures

### Q1. What is the difference between mutable and immutable types in Python? How does Python treat them in memory?

**Answer:**
* **Immutable types:** Once created, their internal state cannot be modified. Examples include `int`, `float`, `str`, `tuple`, `frozenset`, and `bytes`. Any operation that appears to modify an immutable object actually allocates a new object in memory and rebinds the reference.
* **Mutable types:** Can have their contents altered in-place without changing their memory identity (`id()`). Examples include `list`, `dict`, `set`, and `bytearray`.

```python
# Immutable: Rebinds 'x' to a new integer object
x = 10
original_id = id(x)
x += 1
print(id(x) == original_id)  # False

# Mutable: Modifies existing list in-place
nums = [1, 2, 3]
original_id = id(nums)
nums.append(4)
print(id(nums) == original_id)  # True
```

**Key Takeaway for Backend Devs:** Passing mutable objects (like lists or dicts) into functions passes their reference. Modifying them inside a helper function mutates the caller's object unless an explicit copy is made.

---

### Q2. Compare Lists, Tuples, Sets, and Dictionaries in terms of time complexity and primary use cases.

**Answer:**

| Data Structure | Ordered? | Mutable? | Duplicates? | Lookup Complexity | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`list`** | Yes (index-based) | Yes | Yes | $O(n)$ search, $O(1)$ by index | Sequential collections, dynamic queues/stacks |
| **`tuple`** | Yes (index-based) | No | Yes | $O(n)$ search, $O(1)$ by index | Fixed records, coordinates, dict keys, function returns |
| **`set`** | No (hash-based) | Yes | No | $O(1)$ average | Deduplication, membership testing (`in`), math sets |
| **`dict`** | Yes (by insertion) | Yes | Keys: No; Values: Yes | $O(1)$ average key lookup | Key-value mappings, entity representations, caches |

* **Lists vs Tuples:** Tuples use slightly less memory and are read-only; Python optimizes them at the C level. Tuples containing only immutable elements are hashable and can serve as dictionary keys.
* **Sets and Dictionaries:** Both rely on internal hash tables. Looking up `item in my_set` is $O(1)$ on average, whereas `item in my_list` is $O(n)$. Always use a `set` for frequent membership checks.

---

### Q3. How does slicing work in Python, and how do you use packing and unpacking with `*` and `**`?

**Answer:**
* **Slicing syntax:** `sequence[start:stop:step]`
  * `nums[::-1]` reverses a sequence.
  * `nums[1:4]` gets elements from index 1 up to (but not including) index 4.
  * Negative indices count backwards from the end (`-1` is the last item). Slicing a list creates a shallow copy.

* **Positional & Keyword Unpacking:**
  * `*args` packs extra positional arguments into a `tuple`.
  * `**kwargs` packs extra keyword arguments into a `dict`.
  * In assignments, `*` captures residual items:

```python
first, *middle, last = [10, 20, 30, 40, 50]
# first = 10, middle = [20, 30, 40], last = 50

# Merging dictionaries (Python 3.5+) or using unpacking in function calls:
defaults = {"timeout": 30, "retries": 3}
overrides = {"retries": 5}
config = {**defaults, **overrides}  # {'timeout': 30, 'retries': 5}
```

---

### Q4. Compare List Comprehensions with `map()` and `filter()`. When should you prefer one over the other?

**Answer:**
* **List Comprehension:** More Pythonic, easier to read, and allows combined mapping and filtering in a single readable statement:
```python
# List comprehension: Filter even numbers and square them
squares_of_evens = [x**2 for x in range(10) if x % 2 == 0]
```
* **`map()` and `filter()`:** Return lazy iterators in Python 3 (saving memory when iterating large streams). However, combining them with `lambda` expressions often leads to unreadable code:
```python
# Equivalent using map and filter
squares_of_evens = list(map(lambda x: x**2, filter(lambda x: x % 2 == 0, range(10))))
```
* **Best Practice:** Use comprehensions for readability and when you need a concrete list. Use `map()` / `filter()` only if you have pre-defined named functions (e.g., `map(str.strip, lines)`) or need lazy iterator pipelines without wrapping in generator expressions.

---

### Q5. How does string formatting work in modern Python, and why are strings immutable?

**Answer:**
* **String Formatting Evolution:**
  * `%` formatting (legacy C-style): `"%s has %d items" % (user, count)`
  * `str.format()`: `"{} has {} items".format(user, count)`
  * **f-strings (Recommended, Python 3.6+):** Evaluated at runtime, faster than `.format()`, supports inline expressions, formatting specifiers, and self-documenting syntax (`=`).

```python
price = 49.9567
tax = 0.08
print(f"Total: ${price * (1 + tax):.2f}")  # Total: $53.95
print(f"{price=}")  # price=49.9567 (debugging helper in Python 3.8+)
```

* **Why strings are immutable:**
  1. **Hashability & Dictionary Keys:** Strings are the most common dictionary key. If strings were mutable, altering a string's content would change its hash code, corrupting hash table buckets.
  2. **Security & Thread Safety:** Strings are passed across file paths, network sockets, and database queries. Immutability guarantees they cannot be modified concurrently.
  3. **Memory Optimization (Interning):** Python can reuse identical string literals across the runtime.

---

### Q6. What is the difference between `is` and `==`? Explain small integer interning.

**Answer:**
* `==` checks for **equality of values** (calls the `__eq__` method).
* `is` checks for **reference identity** (verifies whether both variables point to the exact same memory address via `id(a) == id(b)`).

```python
a = [1, 2, 3]
b = [1, 2, 3]

print(a == b)  # True (identical content)
print(a is b)  # False (distinct objects in memory)
```

* **Small Integer Interning:** CPython pre-allocates an array of integer objects in the range **`-5` to `256`** at interpreter startup. Any variable assigned an integer in this range references the exact same shared object:
```python
x = 250
y = 250
print(x is y)  # True (shares interned object)

m = 1000
n = 1000
print(m is n)  # False (in standard REPL, separate allocations)
```
* **Rule:** Never use `is` to compare values or strings; use `is` exclusively for singleton comparisons such as `if x is None:`.

---

### Q7. Explain truthy vs falsy values and short-circuit evaluation in Python.

**Answer:**
* **Falsy values in Python:**
  * Constants: `None`, `False`
  * Zero numeric values: `0`, `0.0`, `0j`, `Decimal(0)`
  * Empty sequences/collections: `""`, `()`, `[]`, `{}`, `set()`, `range(0)`
  * Custom objects where `__bool__()` or `__len__()` returns `False` or `0`.
* Everything else evaluates to `True`.

* **Short-Circuit Evaluation:**
  * `A and B`: If `A` is falsy, Python returns `A` immediately without evaluating `B`. If `A` is truthy, it returns `B`.
  * `A or B`: If `A` is truthy, Python returns `A` immediately without evaluating `B`. If `A` is falsy, it returns `B`.

```python
# Safe dictionary access with fallback using short-circuiting
user = {"name": "Alice"}
display_name = user.get("nickname") or user.get("name") or "Anonymous"
# display_name -> "Alice"
```

---

### Q8. How do `try`, `except`, `else`, and `finally` work together? How do you create custom exceptions?

**Answer:**
* **Block Execution Flow:**
  * `try`: Code that might raise an exception.
  * `except SpecificError as err`: Executes only if the specified exception is raised.
  * `else`: Executes **only if no exceptions** were raised in the `try` block. Ideal for actions that must only run on successful completion.
  * `finally`: Executes **unconditionally**, even if an exception was raised, unhandled, or a `return` statement was encountered. Used for cleanup (closing sockets, DB connections).

```python
# Custom Exception
class InsufficientFundsError(Exception):
    def __init__(self, balance: float, amount: float):
        super().__init__(f"Attempted to withdraw {amount} with balance {balance}")
        self.balance = balance
        self.amount = amount

def withdraw(balance: float, amount: float) -> float:
    try:
        if amount > balance:
            raise InsufficientFundsError(balance, amount)
        balance -= amount
    except InsufficientFundsError as err:
        print(f"Transaction failed: {err}")
        raise
    else:
        print("Withdrawal successful, updating audit logs.")
    finally:
        print("Database transaction handle released.")
    return balance
```

---

## Section 2: Functions, Scope & OOP Basics

### Q9. Explain variable scope in Python and the LEGB rule. When do you use `global` and `nonlocal`?

**Answer:**
Python resolves variable names using the **LEGB** lookup order:
1. **L - Local:** Names defined inside the current function/lambda.
2. **E - Enclosing:** Names in the local scope of any enclosing/outer functions (closures).
3. **G - Global:** Names defined at the top level of the current module.
4. **B - Built-in:** Built-in names pre-loaded into Python (e.g., `len`, `range`, `ValueError`).

* **`global` keyword:** Allows a function to bind or modify a variable in the top-level module scope.
* **`nonlocal` keyword:** Allows an inner nested function to rebind a variable in the outer enclosing function's scope without polluting global scope.

```python
def make_counter():
    count = 0  # Enclosing scope
    def increment():
        nonlocal count  # Rebinds 'count' in make_counter's scope
        count += 1
        return count
    return increment

counter = make_counter()
print(counter())  # 1
print(counter())  # 2
```

---

### Q10. What does it mean that functions are "first-class citizens"? What are lambdas and their limitations?

**Answer:**
* **First-Class Citizens:** In Python, functions can be:
  1. Assigned to variables (`f = print`).
  2. Passed as arguments to other functions (higher-order functions like `sort(key=...)`).
  3. Returned as values from other functions (decorators/closures).
  4. Stored in data structures (like a dictionary of command handlers).

* **Lambda Expressions:** Anonymous, inline single-expression functions:
```python
users = [{"name": "Bob", "age": 28}, {"name": "Alice", "age": 22}]
users.sort(key=lambda u: u["age"])  # Sorted by age ascending
```
* **Limitations of Lambdas:**
  * Can only contain a **single expression**, not statements (`return`, `pass`, assignments, `try-except` are forbidden).
  * Harder to read and debug when complex (stack traces report `<lambda>`). If logic spans multiple lines, always define a standard function with `def`.

---

### Q11. Explain classes, instances, `__init__`, and the role of `self`.

**Answer:**
* **Class:** A blueprint that defines attributes and methods for an entity.
* **Instance:** A concrete object instantiated from that class.
* **`__init__`:** An instance initializer called automatically immediately after an object is created.
* **`self`:** Explicitly references the current instance of the class. Python passes the instance automatically as the first argument when invoking an instance method (`obj.method()` translates to `Class.method(obj)` under the hood).

```python
class PaymentGateway:
    def __init__(self, api_key: str):
        self.api_key = api_key  # Instance variable bound to self

    def charge(self, amount: float) -> bool:
        # self gives access to this specific instance's attributes
        print(f"Charging ${amount} via gateway with key {self.api_key[:4]}****")
        return True
```

---

### Q12. How does inheritance work, and how do method overriding and `super()` operate?

**Answer:**
* **Inheritance:** Allows a child class to inherit methods and attributes from a parent class.
* **Method Overriding:** A subclass re-implements a method defined in its parent class to provide custom behavior.
* **`super()`:** Returns a proxy object that delegates method calls to the parent or sibling classes in the Method Resolution Order (MRO). It avoids hardcoding parent class names and guarantees correct initialization in inheritance trees.

```python
class BaseService:
    def __init__(self, service_name: str):
        self.service_name = service_name

    def health_check(self) -> dict:
        return {"status": "UP", "service": self.service_name}

class DatabaseService(BaseService):
    def __init__(self, service_name: str, host: str):
        super().__init__(service_name)  # Initialize parent attributes
        self.host = host

    def health_check(self) -> dict:
        result = super().health_check()  # Extend parent behavior
        result["host"] = self.host
        return result
```

---

### Q13. What is the difference between class variables and instance variables? What is the mutation trap?

**Answer:**
* **Instance variables:** Bound to `self`. Unique to every instance of the class.
* **Class variables:** Defined directly inside the class body outside any methods. Shared across **all** instances of that class.

**The Mutation Trap:**
If a class variable is mutable (e.g., a list or dictionary), mutating it in-place affects every single instance of the class:

```python
class Employee:
    # Class variable (Shared by all instances!)
    skills = []

    def __init__(self, name: str):
        self.name = name  # Instance variable

emp1 = Employee("Alice")
emp2 = Employee("Bob")

emp1.skills.append("Python")  # Mutates the shared class variable!
print(emp2.skills)  # ['Python'] -> Bug!

# Solution: Initialize mutable structures inside __init__
class SafeEmployee:
    def __init__(self, name: str):
        self.name = name
        self.skills = []  # Bound to individual instance
```

---

### Q14. What is the difference between a shallow copy and a deep copy? When does it cause bugs?

**Answer:**
* **Shallow Copy (`copy.copy(x)` or `list(x)`, `x.copy()`):** Creates a new container object, but populates it with **references** to the objects contained in the original.
* **Deep Copy (`copy.deepcopy(x)`):** Recursively clones the container **and** all nested objects inside it, ensuring complete memory independence.

```python
import copy

original = {"user": "Alice", "permissions": ["read", "write"]}

# Shallow copy
shallow = original.copy()
shallow["permissions"].append("admin")
print(original["permissions"])  # ['read', 'write', 'admin'] -> Mutated!

# Deep copy
deep = copy.deepcopy(original)
deep["permissions"].append("delete")
print(original["permissions"])  # Still ['read', 'write', 'admin'] -> Safe!
```

---

### Q15. How does the `with` statement work, and what is the Context Manager protocol?

**Answer:**
The `with` statement ensures deterministic resource acquisition and cleanup (e.g., closing file descriptors or releasing database locks), even if exceptions occur.

It relies on the **Context Manager Protocol**, which consists of two dunder methods:
1. `__enter__()`: Sets up the resource, returns the target bound to `as <var>`.
2. `__exit__(exc_type, exc_val, exc_tb)`: Executes cleanup. If an exception occurred, its details are passed in. If `__exit__` returns `True`, the exception is swallowed; if it returns `False` or `None`, the exception propagates.

```python
class DatabaseConnection:
    def __enter__(self):
        print("Acquiring DB connection...")
        self.conn = "Connected"
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing DB connection...")
        return False  # Do not suppress exceptions

with DatabaseConnection() as conn:
    print(f"Executing query with: {conn}")
```

---

### Q16. What are generators, iterators, and the `yield` statement?

**Answer:**
* **Iterable:** Any object with an `__iter__()` method that returns an iterator (e.g., `list`, `str`, `dict`).
* **Iterator:** An object with a `__next__()` method that yields the next item or raises `StopIteration` when depleted.
* **Generator:** A function that contains the `yield` keyword. Calling a generator function returns a lazy generator iterator without executing code upfront.
* **Why use `yield`:** Yielding pauses the function, saves execution state in memory, and returns a value to the caller. When called again via `next()`, execution resumes right after the `yield`. This enables processing gigabyte-scale streams in $O(1)$ memory.

```python
def read_in_chunks(file_path: str, chunk_size: int = 1024):
    with open(file_path, "r") as f:
        while chunk := f.read(chunk_size):
            yield chunk  # Lazily streams file without loading full content into RAM
```

---

## Section 3: Standard Library & Common Gotchas

### Q17. Explain the "mutable default argument" gotcha in Python function definitions.

**Answer:**
In Python, default parameter values are evaluated **once**, at the time the function is **defined** (compiled into bytecode), not each time the function is executed. If a mutable object (like `[]` or `{}`) is used as a default, all subsequent function calls share that same object instance.

```python
# BUGGY PATTERN
def add_item(item: str, target_list: list = []):
    target_list.append(item)
    return target_list

print(add_item("apple"))   # ['apple']
print(add_item("banana"))  # ['apple', 'banana'] -> Bug!

# IDIOMATIC SOLUTION: Use None as default sentinel
def add_item_safe(item: str, target_list: list = None):
    if target_list is None:
        target_list = []
    target_list.append(item)
    return target_list
```

---

### Q18. How do `defaultdict`, `Counter`, and `deque` from the `collections` module simplify code?

**Answer:**
* **`defaultdict`:** Automatically initializes missing keys with a default factory callable (e.g., `list`, `int`), avoiding repetitive `if key not in d:` checks:
```python
from collections import defaultdict
grouped = defaultdict(list)
grouped["engineering"].append("Alice")  # No KeyError raised
```
* **`Counter`:** A dictionary subclass specifically designed for counting hashable elements:
```python
from collections import Counter
counts = Counter(["apple", "banana", "apple", "orange"])
print(counts.most_common(1))  # [('apple', 2)]
```
* **`deque` (Double-ended queue):** Provides $O(1)$ appends and pops from both ends. Standard Python lists have $O(n)$ cost for `pop(0)` or `insert(0)` because all remaining elements must be shifted in memory.

---

### Q19. How do you parse and serialize JSON in Python? How do you handle non-serializable objects like `datetime` or `Decimal`?

**Answer:**
* Use the built-in `json` module:
  * `json.loads(str_data)`: Parses a JSON string to a Python dictionary/list.
  * `json.dumps(py_obj)`: Serializes a Python object to a JSON string.
* **Handling Custom / Non-Serializable Types:** Types like `datetime.datetime` or `decimal.Decimal` raise `TypeError: Object of type X is not JSON serializable`.
  * **Solution:** Pass a custom `default` callable to `json.dumps`:

```python
import json
from datetime import datetime
from decimal import Decimal

payload = {
    "order_id": 101,
    "amount": Decimal("199.99"),
    "created_at": datetime.now()
}

def custom_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

json_output = json.dumps(payload, default=custom_serializer)
```

---

### Q20. What is a decorator, how does it work, and why must you use `functools.wraps`?

**Answer:**
A decorator is a callable that takes another function as an argument, wraps it with additional behavior, and returns the modified function.

**Why `functools.wraps` is mandatory:**
When a function is wrapped, the outer wrapper function replaces the original. Without `@wraps(func)`, the decorated function loses its original identity—its `__name__`, `__doc__`, and parameter signature are overwritten by the wrapper's metadata.

```python
import time
from functools import wraps

def time_it(func):
    @wraps(func)  # Preserves func's __name__ and docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        print(f"Function {func.__name__} executed in {duration:.4f}s")
        return result
    return wrapper

@time_it
def compute():
    """Computes test data."""
    return sum(range(1_000_000))

print(compute.__name__)  # 'compute' (would be 'wrapper' without @wraps)
```

---

### Q21. What is the role of virtual environments (`venv`), `requirements.txt`, and package lockfiles?

**Answer:**
* **Virtual Environment (`venv`):** An isolated directory containing its own Python interpreter and `site-packages` directory. It prevents dependency version collisions between different projects on the same host machine.
* **`requirements.txt`:** Lists project dependencies (e.g., `requests==2.31.0`). Without pinning exact versions (`==`), automated builds can install newer breaking minor/major versions.
* **Lockfiles (`poetry.lock`, `Pipfile.lock`):** Store the exact dependency graph, cryptographic hashes, and transitive sub-dependency versions installed during development. This guarantees identical, deterministic builds across developer laptops, staging, and production containers.

---

### Q22. What are Python Type Hints, and what value do tools like `mypy` bring to a backend codebase?

**Answer:**
* Introduced in Python 3.5 via PEP 484, type hints allow annotating variables, function arguments, and return values:
```python
from typing import Optional, List, Dict

def fetch_users(department: str, limit: Optional[int] = 10) -> List[Dict[str, str]]:
    return [{"name": "Alice", "role": department}]
```
* **Runtime Behavior:** Type hints **do not** enforce types at runtime; Python remains dynamically typed and will not crash if invalid types are passed.
* **Value in Production:**
  1. Static type checkers (e.g., `mypy`, `pyright`) analyze code before deployment, catching `NoneType` errors and type mismatches.
  2. IDE autocompletion and refactoring become reliable.
  3. Serves as self-documenting code for new team members.

---

## Section 4: Scenario-Based Questions & Debugging

### Q23. Scenario: You are parsing responses from an unpredictable third-party API where certain nested fields may be missing or `None`. How do you safely extract nested values without crashing with `KeyError` or `AttributeError`?

**Answer:**
**Problem:** Direct chained indexing (`data["profile"]["address"]["zipcode"]`) crashes with `KeyError` if any intermediate key is absent, or `TypeError` if an intermediate value is `None`.

**Solutions:**
1. **Chained `.get()` calls with default fallbacks:**
```python
payload = {"user_id": 123, "profile": None}

# Safe extraction
zipcode = (payload.get("profile") or {}).get("address", {}).get("zipcode", "00000")
```
2. **Helper function for arbitrary nested paths:**
```python
def safe_get(dictionary: dict, *keys, default=None):
    current = dictionary
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current

zipcode = safe_get(payload, "profile", "address", "zipcode", default="00000")
```
3. In modern production codebases, prefer validating third-party inputs using a schema parsing library like **Pydantic** (`pydantic.BaseModel`).

---

### Q24. Scenario: You have a list with duplicate elements. You need to remove duplicates while strictly preserving the original insertion order. How do you implement this?

**Answer:**
* **Naive approach (`list(set(items))`):** Deduplicates in $O(n)$ time, but **destroys order** because sets are unordered.
* **Idiomatic Python 3.7+ approach:** In Python 3.7+, standard dictionaries are guaranteed to maintain insertion order. `dict.fromkeys()` builds a dictionary whose keys are the unique elements, preserving first appearance:

```python
raw_items = ["apple", "banana", "apple", "orange", "banana", "grape"]

# O(n) deduplication preserving original order:
unique_items = list(dict.fromkeys(raw_items))
print(unique_items)  # ['apple', 'banana', 'orange', 'grape']
```

* **If items are unhashable (e.g., a list of dictionaries):**
```python
records = [{"id": 1}, {"id": 2}, {"id": 1}]
seen_ids = set()
unique_records = []
for r in records:
    if r["id"] not in seen_ids:
        seen_ids.add(r["id"])
        unique_records.append(r)
```

---

### Q25. Scenario: A server receives a 20 GB log file that must be analyzed for error lines. How do you process this file without running out of memory (OOM)?

**Answer:**
**Anti-Pattern:** Using `f.readlines()` or `f.read()`. Both load the entire file contents into RAM, instantly killing the worker process with an Out-Of-Memory error.

**Idiomatic Pattern:** File objects in Python are iterators that stream line-by-line using an internal buffer:

```python
def find_errors(file_path: str):
    # Consumes one line at a time in O(1) memory
    with open(file_path, "r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            if "ERROR" in line:
                yield (line_num, line.strip())

# Consuming the generator:
for error_num, error_msg in find_errors("/var/log/app_20gb.log"):
    # Process or write to an external database
    pass
```

---

### Q26. Scenario: You need to merge two configuration dictionaries where nested keys might collide. How do you handle flat and deep merging?

**Answer:**
* **Flat Merging (Python 3.9+ Dictionary Union Operator `|`):**
```python
base_cfg = {"host": "localhost", "port": 8000, "debug": True}
override_cfg = {"port": 5000, "env": "staging"}

merged = base_cfg | override_cfg
# {'host': 'localhost', 'port': 5000, 'debug': True, 'env': 'staging'}
```

* **Deep Merging (Recursive):** The `|` operator overwrites entire nested dictionaries rather than merging them. For nested configs, write a recursive merger:
```python
def deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

c1 = {"db": {"host": "localhost", "port": 5432}}
c2 = {"db": {"port": 5433, "user": "postgres"}}
print(deep_merge(c1, c2))
# {'db': {'host': 'localhost', 'port': 5433, 'user': 'postgres'}}
```

---

### Q27. Scenario: A developer wrote a function to duplicate an order, but modifying the items in the new order unexpectedly altered the original order. What caused this, and how do you resolve it?

**Answer:**
```python
original_order = {
    "order_id": 1001,
    "items": [{"sku": "A1", "qty": 2}]
}

# The bug:
cloned_order = original_order.copy()  # Shallow copy!
cloned_order["items"][0]["qty"] = 5

print(original_order["items"][0]["qty"])  # Prints 5! Mutated original.
```
* **Cause:** `original_order.copy()` creates a shallow copy. The outer dictionary is a new object, but the nested list `items` and its inner dictionaries still share the exact same references in memory.
* **Resolution:** Use `copy.deepcopy()` to create independent clones of all nested collections:
```python
import copy
cloned_order = copy.deepcopy(original_order)
cloned_order["items"][0]["qty"] = 5
print(original_order["items"][0]["qty"])  # 2 (Preserved)
```

---

### Q28. Scenario: Write a reusable decorator that retries a flaky function up to $N$ times with a delay when a specific exception occurs.

**Answer:**
```python
import time
from functools import wraps

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        print(f"[ERROR] Max retries reached for {func.__name__}. Raising exception.")
                        raise
                    print(f"[WARN] {func.__name__} failed ({e}). Retrying in {delay}s (Attempt {attempts}/{max_attempts})...")
                    time.sleep(delay)
        return wrapper
    return decorator

# Usage:
@retry(max_attempts=3, delay=0.5, exceptions=(ConnectionError, TimeoutError))
def call_external_payment_api():
    # Network call
    pass
```

---

### Q29. Scenario: You have a list of employee dictionaries. You must sort them primarily by department ascending, and secondarily by salary descending. How do you implement this in a single `sort()` call?

**Answer:**
In Python, tuples are compared element-by-element from left to right. When sorting numerical values, negating the number (`-salary`) reverses the sort direction for that individual field:

```python
employees = [
    {"name": "Alice", "dept": "Engineering", "salary": 90000},
    {"name": "Bob", "dept": "Sales", "salary": 70000},
    {"name": "Charlie", "dept": "Engineering", "salary": 120000},
    {"name": "Diana", "dept": "Sales", "salary": 95000},
]

# Sort by dept ASC, then salary DESC
employees.sort(key=lambda emp: (emp["dept"], -emp["salary"]))

for emp in employees:
    print(f"{emp['dept']:12} | ${emp['salary']:<6} | {emp['name']}")

# Output:
# Engineering  | $120000 | Charlie
# Engineering  | $90000  | Alice
# Sales        | $95000  | Diana
# Sales        | $70000  | Bob
```

---

### Q30. Scenario: You are writing a backend endpoint that accepts an untrusted registration payload dictionary. How do you validate and sanitize fields using pure Python before proceeding?

**Answer:**
```python
class ValidationError(Exception):
    pass

def validate_and_sanitize_registration(payload: dict) -> dict:
    errors = {}
    sanitized = {}

    # 1. Validate username (required, non-empty string, length constraint)
    raw_username = payload.get("username")
    if not isinstance(raw_username, str) or not raw_username.strip():
        errors["username"] = "Username is required and cannot be empty."
    else:
        sanitized["username"] = raw_username.strip().lower()

    # 2. Validate email (basic format check)
    raw_email = payload.get("email")
    if not isinstance(raw_email, str) or "@" not in raw_email or "." not in raw_email:
        errors["email"] = "A valid email address is required."
    else:
        sanitized["email"] = raw_email.strip().lower()

    # 3. Validate age (optional integer with bounds)
    raw_age = payload.get("age")
    if raw_age is not None:
        try:
            age = int(raw_age)
            if age < 18 or age > 120:
                errors["age"] = "Age must be between 18 and 120."
            else:
                sanitized["age"] = age
        except (ValueError, TypeError):
            errors["age"] = "Age must be a valid integer."
    else:
        sanitized["age"] = None

    if errors:
        raise ValidationError(errors)

    return sanitized
```
* **Best Practice:** Keep validation logic cleanly separated from business logic, collect all field errors before raising an exception (so users get full feedback in a single response), and always strip/normalize strings.

---

## Section 5: Practical Backend Essentials, Data Handling & Scenarios

### Q31. What is the difference between `__str__` and `__repr__` in Python? When should you implement each?

**Answer:**
* **`__repr__(self)`:** Intended to be an **unambiguous**, developer-facing representation of the object. Ideally, the string returned should look like valid Python code that could recreate the object (e.g., `User(id=1, email='a@b.com')`). If only `__repr__` is defined on a class, Python uses it as a fallback for `__str__` as well.
* **`__str__(self)`:** Intended to be a **readable**, end-user-friendly representation (e.g., `"Alice (alice@example.com)"`). It is invoked by `str(obj)` and `print(obj)`.

```python
class Customer:
    def __init__(self, customer_id: int, name: str):
        self.customer_id = customer_id
        self.name = name

    def __repr__(self):
        # Developer-focused, unambiguous
        return f"Customer(customer_id={self.customer_id!r}, name={self.name!r})"

    def __str__(self):
        # Human-readable display string
        return f"{self.name} [ID: {self.customer_id}]"

c = Customer(42, "Bob")
print(str(c))   # Bob [ID: 42]
print(repr(c))  # Customer(customer_id=42, name='Bob')
```

---

### Q32. How do `any()` and `all()` work in Python? How do they leverage short-circuiting with generator expressions?

**Answer:**
* **`any(iterable)`:** Returns `True` if **at least one** element in the iterable is truthy. Returns `False` for an empty iterable.
* **`all(iterable)`:** Returns `True` if **all** elements in the iterable are truthy. Returns `True` for an empty iterable ("vacuous truth").

**Short-Circuiting Optimization:**
When passed a generator expression, both functions stop evaluating as soon as the outcome is determined, preventing unnecessary computation or database/API calls:

```python
users = [
    {"name": "Alice", "is_admin": False},
    {"name": "Bob", "is_admin": True},
    {"name": "Charlie", "is_admin": False},
]

# Stops evaluating immediately after inspecting Bob:
has_admin = any(u["is_admin"] for u in users)  # True

# Verifying all users have valid emails:
emails = ["alice@test.com", "bob@test.com", ""]
all_valid = all(len(e) > 0 for e in emails)    # False (stops at index 2)
```

---

### Q33. How does Python's `zip()` function work, and what is `itertools.zip_longest()`?

**Answer:**
* **`zip(*iterables)`:** Pairs corresponding elements from multiple iterables into tuples until the **shortest** iterable is exhausted. Extra elements in longer iterables are discarded:
```python
names = ["Alice", "Bob", "Charlie"]
roles = ["Admin", "Dev"]

paired = list(zip(names, roles))
print(paired)  # [('Alice', 'Admin'), ('Bob', 'Dev')] -> Charlie truncated!

# Python 3.10+ strict mode raises ValueError if lengths differ:
# zip(names, roles, strict=True)
```

* **`itertools.zip_longest(*iterables, fillvalue=None)`:** Continues iterating until the **longest** iterable is exhausted, substituting `fillvalue` for missing entries:
```python
from itertools import zip_longest

paired_longest = list(zip_longest(names, roles, fillvalue="Pending"))
print(paired_longest)
# [('Alice', 'Admin'), ('Bob', 'Dev'), ('Charlie', 'Pending')]
```

---

### Q34. What is the purpose of `enumerate()`, and why is `for i in range(len(items)):` considered an anti-pattern?

**Answer:**
* **Anti-Pattern (`range(len(items))`):** It is unidiomatic, harder to read, error-prone when modifying index boundaries, and does not work on non-subscriptable iterables (generators, sets, file streams).
* **Idiomatic Python (`enumerate(iterable, start=0)`):** Returns a lazy enumerate iterator yielding pairs of `(index, item)` in $O(1)$ memory:

```python
statuses = ["INIT", "PENDING", "COMPLETED"]

for idx, status in enumerate(statuses, start=1):
    print(f"Step {idx}: {status}")

# Step 1: INIT
# Step 2: PENDING
# Step 3: COMPLETED
```

---

### Q35. What is the Walrus Operator (`:=`) introduced in Python 3.8? Give a practical backend example.

**Answer:**
The **walrus operator** (`:=`) is the assignment expression operator. It assigns a value to a variable as part of a larger expression, avoiding redundant calculations or function calls:

```python
# Without walrus operator (redundant length call or extra lines):
line = file.readline()
while line:
    process(line)
    line = file.readline()

# With walrus operator (clean and concise):
while (line := file.readline()):
    process(line)

# Practical API payload example:
data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
if (count := len(data.get("users", []))) > 0:
    print(f"Processing {count} users found in payload.")
```

---

### Q36. How do you safely read and set environment variables in Python (`os.environ` vs `os.getenv()`)?

**Answer:**
* **`os.environ["KEY"]`:** Accesses the dictionary of environment variables directly. If `"KEY"` is missing, it raises a **`KeyError`**. Use this for **mandatory** configurations (e.g., `DATABASE_URL`) that should crash early during app boot if not supplied.
* **`os.getenv("KEY", default=None)`:** Returns the environment variable value or the fallback default if missing. Use this for **optional** parameters with sensible defaults (e.g., `PORT`, `DEBUG`).

```python
import os

# Mandatory configuration (crashes early on startup if missing):
try:
    DATABASE_URL = os.environ["DATABASE_URL"]
except KeyError:
    raise RuntimeError("Missing required environment variable: DATABASE_URL")

# Optional configuration with default:
SERVER_PORT = int(os.getenv("PORT", 8000))
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
```

---

### Q37. Why should you always use timezone-aware datetimes in backend applications, and how do you handle them?

**Answer:**
* **Naive Datetimes (`datetime.now()`):** Contain no timezone information. Comparing or storing naive datetimes across servers in different regions or handling Daylight Saving Time (DST) shifts causes silent scheduling bugs and corrupted audit logs.
* **Aware Datetimes (`timezone.utc`):** Always represent an absolute point in time on the UTC timeline.

```python
from datetime import datetime, timezone, timedelta

# Always record timestamps in UTC:
now_utc = datetime.now(timezone.utc)
print(now_utc.isoformat())  # e.g., '2026-10-05T08:54:00+00:00'

# Calculating expiration timestamp:
token_expiry = now_utc + timedelta(hours=2)

# Converting to client's local timezone for display:
client_tz = timezone(timedelta(hours=5, minutes=30))  # IST (+05:30)
display_time = now_utc.astimezone(client_tz)
```

---

### Q38. What is the difference between keyword-only (`*`) and positional-only (`/`) parameters in function signatures?

**Answer:**
* **Positional-Only (`/`, Python 3.8+):** Parameters placed **before** the `/` must be passed positionally and cannot be passed as keyword arguments.
* **Keyword-Only (`*`):** Parameters placed **after** the `*` must be passed by keyword name and cannot be passed positionally.

```python
def configure_cache(name, max_size, /, *, timeout=300, evict_policy="LRU"):
    # 'name' and 'max_size' MUST be positional
    # 'timeout' and 'evict_policy' MUST be keywords
    pass

# VALID:
configure_cache("redis_cache", 1000, timeout=60)

# INVALID:
# configure_cache(name="redis_cache", max_size=1000) -> TypeError!
# configure_cache("redis_cache", 1000, 60)          -> TypeError!
```
* **Backend Benefit:** Keyword-only arguments force callers to write self-documenting code for boolean flags and optional configurations (e.g., `run_job(dry_run=True)` instead of `run_job(True)`).

---

### Q39. What is the difference between `list.append()` and `list.extend()`?

**Answer:**
* **`list.append(x)`:** Adds its argument `x` as a **single element** to the end of the list. If `x` is another list, the entire list is nested.
* **`list.extend(iterable)`:** Iterates through the given iterable and appends **each individual item** to the end of the list.

```python
a = [1, 2]
b = [3, 4]

a.append(b)
print(a)  # [1, 2, [3, 4]] -> Nested! Length is 3.

x = [1, 2]
y = [3, 4]
x.extend(y)
print(x)  # [1, 2, 3, 4]   -> Flattened! Length is 4.
```

---

### Q40. Why is string concatenation with `+=` inside loops an anti-pattern? Why is `str.join()` preferred?

**Answer:**
* **The `+=` Problem:** Because strings in Python are immutable, executing `text += chunk` inside a loop often allocates a brand-new string object of size $O(\text{len}(text) + \text{len}(chunk))$ and copies characters over on each iteration, leading to $O(n^2)$ time complexity.
* **`str.join(iterable)`:** Pre-computes the exact total byte length required for all elements in the collection, allocates a single memory buffer once, and copies all strings in C, running in optimal **$O(n)$ time**.

```python
words = [f"word_{i}" for i in range(10_000)]

# ANTI-PATTERN: O(n^2) time
res = ""
for w in words:
    res += w + ","

# IDIOMATIC: O(n) time
res = ",".join(words)
```

---

### Q41. How do you read and write CSV files safely using `csv.DictReader` and `csv.DictWriter`?

**Answer:**
`DictReader` and `DictWriter` map CSV rows to Python dictionaries based on column header names, eliminating bugs caused by changing column index positions:

```python
import csv

# Reading CSV into dictionaries
def load_products(file_path: str):
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # row is a dict: {'sku': 'A100', 'price': '19.99', 'stock': '50'}
            yield {"sku": row["sku"], "price": float(row["price"])}

# Writing dictionaries to CSV
def export_products(file_path: str, products: list[dict]):
    fieldnames = ["sku", "price", "stock"]
    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
```
* Note: Always pass `newline=""` when opening files for writing with the `csv` module to prevent unintended blank lines on Windows.

---

### Q42. Explain the difference between `@classmethod`, `@staticmethod`, and regular instance methods.

**Answer:**
* **Instance Method:** Receives the current instance (`self`) as its first argument. Has full access to instance variables and the class via `type(self)`.
* **`@classmethod`:** Receives the class object (`cls`) as its first argument. Has access to class-level state. Commonly used for **alternative constructors / factory methods**.
* **`@staticmethod`:** Receives neither `self` nor `cls`. Behaves like a plain function scoped inside the class namespace for logical grouping.

```python
class DateParser:
    def __init__(self, year: int, month: int, day: int):
        self.year = year
        self.month = month
        self.day = day

    @classmethod
    def from_iso_string(cls, date_str: str):
        # Alternative constructor
        y, m, d = map(int, date_str.split("-"))
        return cls(y, m, d)

    @staticmethod
    def is_valid_year(year: int) -> bool:
        return 1900 <= year <= 2100

d = DateParser.from_iso_string("2026-10-05")
print(DateParser.is_valid_year(2026))  # True
```

---

### Q43. How do `assert` statements work, and why should you never use `assert` for data validation in production?

**Answer:**
* **How it works:** `assert condition, "Error message"` evaluates the condition. If false, it raises `AssertionError`.
* **The Production Hazard:** If Python is run with optimization flags (`python -O` or `PYTHONOPTIMIZE=1`), the interpreter **completely strips out all `assert` statements from bytecode**.
* If you write `assert user.is_authenticated, "Unauthorized"`, running under `-O` completely skips the check, exposing protected endpoints to unauthenticated users.
* **Rule:** Use `assert` strictly in unit test suites or internal sanity invariants that should never occur. For business logic and input validation, always use explicit `if not condition: raise ValidationError(...)`.

---

### Q44. What makes an object "hashable" in Python? Why can't a `list` or `dict` be added to a `set`?

**Answer:**
* An object is hashable if it has a hash value that **remains unchanged throughout its entire lifetime** (implemented via `__hash__`) and can be compared to other objects for equality (via `__eq__`).
* **Why lists and dicts are unhashable:**
  * Lists and dicts are **mutable**. If a list could be added to a set, modifying the list in-place would change its hash code.
  * The hash table wouldn't be able to find the element in its original bucket, corrupting the hash table.
* **Solution:** Convert mutable collections to immutable equivalents before adding to sets or using as dict keys:
  * Use `tuple()` instead of `list()`.
  * Use `frozenset()` instead of `set()`.

---

### Q45. Scenario: Write a clean, reusable pagination helper function for an in-memory collection or query result.

**Answer:**
```python
import math
from typing import Sequence, TypeVar, Generic

T = TypeVar("T")

def paginate(items: Sequence[T], page: int = 1, page_size: int = 10) -> dict:
    if page < 1:
        raise ValueError("Page number must be >= 1")
    if page_size < 1:
        raise ValueError("Page size must be >= 1")

    total_items = len(items)
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = items[start_idx:end_idx]

    return {
        "items": paginated_items,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

# Example usage:
records = [f"record_{i}" for i in range(1, 45)]
result = paginate(records, page=2, page_size=10)
print(result["items"])     # ['record_11', ..., 'record_20']
print(result["has_next"])  # True
```

---

### Q46. Scenario: You are comparing two lists of product IDs from an external catalog sync. How do you find added, removed, and common IDs in $O(n)$ time?

**Answer:**
Convert both lists to sets and use native **set operations**:

```python
current_catalog = ["prod_1", "prod_2", "prod_3", "prod_4"]
synced_catalog = ["prod_3", "prod_4", "prod_5", "prod_6"]

set_current = set(current_catalog)
set_synced = set(synced_catalog)

# Set difference and intersection:
added_items = list(set_synced - set_current)       # ['prod_5', 'prod_6']
removed_items = list(set_current - set_synced)     # ['prod_1', 'prod_2']
retained_items = list(set_current & set_synced)    # ['prod_3', 'prod_4']

print(f"Added: {added_items}")
print(f"Removed: {removed_items}")
print(f"Retained: {retained_items}")
```
* **Performance:** Set construction and operations run in $O(n)$ average time, compared to $O(n^2)$ for nested list loops (`[x for x in synced if x not in current]`).

---

### Q47. Scenario: You receive a stream of financial transaction records. How do you aggregate total spend and transaction count per category cleanly?

**Answer:**
```python
from collections import defaultdict
from decimal import Decimal

transactions = [
    {"category": "Food", "amount": Decimal("15.50")},
    {"category": "Transport", "amount": Decimal("4.25")},
    {"category": "Food", "amount": Decimal("22.00")},
    {"category": "Utilities", "amount": Decimal("85.00")},
    {"category": "Transport", "amount": Decimal("12.00")},
]

def aggregate_by_category(records: list[dict]) -> dict:
    # Default factory initializes: [total_amount, count]
    stats = defaultdict(lambda: {"total": Decimal("0.00"), "count": 0})

    for tx in records:
        category = tx["category"]
        stats[category]["total"] += tx["amount"]
        stats[category]["count"] += 1

    return dict(stats)

result = aggregate_by_category(transactions)
for cat, data in result.items():
    print(f"{cat:12} | Total: ${data['total']:>6} | Tx Count: {data['count']}")
```

---

### Q48. Scenario: Write a robust parsing function to safely convert diverse string representations of booleans (from query params or config files) into Python booleans.

**Answer:**
```python
TRUTHY_VALUES = frozenset({"true", "1", "yes", "y", "t", "on", "enabled"})
FALSY_VALUES = frozenset({"false", "0", "no", "n", "f", "off", "disabled"})

def parse_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUTHY_VALUES:
            return True
        if normalized in FALSY_VALUES:
            return False

    raise ValueError(f"Cannot parse {value!r} as a valid boolean.")

# Tests:
print(parse_bool("True"))     # True
print(parse_bool("0"))        # False
print(parse_bool("enabled"))  # True
print(parse_bool(None, default=True))  # True
```

---

### Q49. Scenario: How do you securely hash and verify user passwords in Python using `hashlib` with salt or `bcrypt`?

**Answer:**
**Anti-Pattern:** Using plain MD5 or SHA256 (`hashlib.sha256(password.encode()).hexdigest()`). These algorithms are fast by design and vulnerable to GPU rainbow-table attacks.

**Secure Pattern with `hashlib.pbkdf2_hmac` (Standard Library):**
```python
import hashlib
import os
import hmac

def hash_password(password: str) -> str:
    # 16-byte cryptographically secure salt
    salt = os.urandom(16)
    # PBKDF2 with 600,000 SHA256 iterations
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    # Store salt and hash together
    return f"{salt.hex()}${derived.hex()}"

def verify_password(stored_hash: str, provided_password: str) -> bool:
    salt_hex, derived_hex = stored_hash.split("$")
    salt = bytes.fromhex(salt_hex)
    new_derived = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 600_000)
    # Constant-time comparison prevents timing attacks:
    return hmac.compare_digest(new_derived.hex(), derived_hex)
```

---

### Q50. Scenario: Implement a simple in-memory sliding window rate limiter in Python to restrict IP addresses to 60 requests per minute.

**Answer:**
```python
import time
from collections import defaultdict, deque

class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window = window_seconds
        # Maps client_ip -> deque of timestamps
        self.requests = defaultdict(deque)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        client_history = self.requests[client_ip]

        # 1. Evict timestamps older than the sliding window:
        cutoff = now - self.window
        while client_history and client_history[0] < cutoff:
            client_history.popleft()

        # 2. Check if request count exceeds threshold:
        if len(client_history) < self.max_requests:
            client_history.append(now)
            return True

        return False

# Example usage in an API middleware:
limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=2.0)
ip = "192.168.1.10"
print(limiter.is_allowed(ip))  # True
print(limiter.is_allowed(ip))  # True
print(limiter.is_allowed(ip))  # True
print(limiter.is_allowed(ip))  # False (Throttled!)
```

---

