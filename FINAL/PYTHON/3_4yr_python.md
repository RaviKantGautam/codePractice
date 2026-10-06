# Python Interview Questions & Answers (3–4 Years Experience)

Comprehensive interview questions and answers tailored for mid-level backend Python engineers (3–4 years experience). Topics focus on Python object model internals, descriptors, metaprogramming foundations, concurrency architecture (`threading`, `multiprocessing`, `asyncio`), memory mechanics, and production-grade scenario problem solving.

---

## Section 1: Advanced Language Mechanics & OOP

### Q1. What is the difference between `__new__` and `__init__`? In what practical backend scenarios would you override `__new__`?

**Answer:**
* **`__new__(cls, *args, **kwargs)`:** A static method responsible for **allocating and creating** the instance in memory. It must return a new instance of `cls` (usually by calling `super().__new__(cls)`). If `__new__` does not return an instance of `cls`, `__init__` is never invoked.
* **`__init__(self, *args, **kwargs)`:** An instance method responsible for **initializing** the freshly created object's attributes. It returns `None`.

**Practical Scenarios for Overriding `__new__`:**
1. **Subclassing Immutable Types:** When extending immutable built-ins (`tuple`, `str`, `int`), values cannot be modified in `__init__`. You must alter them in `__new__` before creation:
```python
class UppercaseTuple(tuple):
    def __new__(cls, iterable):
        upper_items = (str(x).upper() for x in iterable)
        return super().__new__(cls, upper_items)

t = UppercaseTuple(["apple", "banana"])  # ('APPLE', 'BANANA')
```
2. **Singleton Pattern:** Enforcing a single shared instance across the process (e.g., a shared configuration manager or connection pool):
```python
class DatabasePool:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, dsn: str = "default_dsn"):
        if not self._initialized:
            self.dsn = dsn
            self._initialized = True
```

---

### Q2. How does `__slots__` optimize memory, and what are its caveats when used in inheritance?

**Answer:**
* **Standard Mechanism:** By default, Python classes store dynamic instance attributes in a dictionary (`__dict__`). A dictionary has substantial memory overhead (hash table bucketing, keys, pointers).
* **`__slots__` Optimization:** Declaring `__slots__ = ("attr1", "attr2")` instructs CPython to allocate a fixed-size compact C array for references instead of creating a `__dict__` for every instance. For classes with millions of lightweight instances (e.g., ORM models, points, telemetry packets), this reduces RAM consumption by 40%–70% and slightly improves attribute access speed.

**Caveats in Inheritance:**
1. **Inheritance without `__slots__`:** If a child class inherits from a class with `__slots__` but does not declare its own `__slots__`, instances of the child class **will allocate a `__dict__`**, neutralizing the memory benefits.
2. **Multiple Inheritance Collisions:** Multiple base classes with non-empty `__slots__` cannot be combined in multiple inheritance (raises `TypeError: multiple bases have instance lay-out conflict`).
3. **No Dynamic Attributes:** Attempting to assign an attribute not listed in `__slots__` raises an `AttributeError` (unless `"__dict__"` is explicitly included in `__slots__`).

---

### Q3. Explain the relationship between `__hash__` and `__eq__`. What happens if you override `__eq__` without defining `__hash__`?

**Answer:**
* **The Python Invariant:** If two objects are considered equal according to `__eq__`, they **must** produce the exact same integer hash code via `__hash__`:
$$\text{If } a == b \implies \operatorname{hash}(a) == \operatorname{hash}(b)$$
* **Why this matters for Dictionaries and Sets:** When inserting an item into a hash table (dict/set), Python computes `hash(key)` to locate the bucket. If two objects have identical values but different hashes, they will land in separate buckets, breaking set uniqueness and dictionary key lookups.
* **What happens if you only override `__eq__`:** CPython automatically sets `__hash__ = None` on that class. The object becomes **unhashable**, and attempting to add it to a `set` or use it as a `dict` key raises `TypeError: unhashable type`.

```python
class User:
    def __init__(self, user_id: int, email: str):
        self.user_id = user_id
        self.email = email

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id

    def __hash__(self):
        # Hash based strictly on immutable identifying attributes used in __eq__
        return hash(self.user_id)
```

---

### Q4. How does the Python Descriptor Protocol work? What is the difference between data and non-data descriptors, and how does `@property` use this?

**Answer:**
A descriptor is an object attribute whose access and modification behavior is controlled by implementing one or more methods of the **Descriptor Protocol**:
1. `__get__(self, instance, owner=None)`
2. `__set__(self, instance, value)`
3. `__delete__(self, instance)`

* **Data Descriptor:** Implements at least `__set__` or `__delete__` (in addition to `__get__`).
* **Non-Data Descriptor:** Implements **only** `__get__` (e.g., standard methods).

**Lookup Precedence Order:**
When evaluating `obj.attr`, Python traverses this strict hierarchy:
1. Data descriptors defined on `type(obj)`.
2. Instance dictionary (`obj.__dict__["attr"]`).
3. Non-data descriptors defined on `type(obj)`.
4. Class dictionary (`type(obj).__dict__["attr"]`).
5. `__getattr__()` hook if defined.

**How `@property` works:**
`@property` is a built-in C-implemented **data descriptor**. When you write `@property def price(self):`, it assigns an instance of `property` with a `__get__` method to the class attribute `price`. Defining `@price.setter` attaches a `__set__` implementation, making it a data descriptor that intercepts attribute writes ahead of `instance.__dict__`.

```python
class PositiveNumber:
    """Reusable data descriptor for field validation."""
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, 0)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError(f"{self.name} must be >= 0")
        instance.__dict__[self.name] = value

class Product:
    price = PositiveNumber()
    stock = PositiveNumber()
```

---

### Q5. What is Method Resolution Order (MRO)? How does the C3 Linearization algorithm resolve multiple inheritance?

**Answer:**
* **MRO:** The linear search sequence Python constructs to resolve attributes and methods when multiple inheritance is involved. You can inspect it on any class via `Class.mro()` or `Class.__mro__`.
* **C3 Linearization Algorithm:** Python guarantees three properties:
  1. Subclasses appear before parents.
  2. The declaration order of base classes in the class definition is strictly preserved.
  3. **Monotonicity:** If a class precedes another in one base class's MRO, it must precede it in all subclasses.

```python
class A:
    def ping(self): print("A")

class B(A):
    def ping(self): print("B"); super().ping()

class C(A):
    def ping(self): print("C"); super().ping()

class D(B, C):
    def ping(self): print("D"); super().ping()

# D.mro() -> [D, B, C, A, object]
D().ping()
# Output:
# D
# B
# C
# A
```
* **Why `super()` matters:** Notice that `B.ping()` calls `super().ping()`, which resolves to **`C.ping()`**, not `A.ping()`. `super()` is **cooperative**—it follows the runtime MRO of the calling instance, preventing the duplicate execution of ancestor classes in diamond inheritance patterns.

---

### Q6. Compare Abstract Base Classes (`abc.ABC`) with Protocols (`typing.Protocol`). When should you use nominal vs structural typing?

**Answer:**

| Feature | `abc.ABC` (Nominal Subtyping) | `typing.Protocol` (Structural Subtyping / Duck Typing) |
| :--- | :--- | :--- |
| **Philosophy** | "Explicit is better than implicit." Subclass must declare inheritance. | "If it walks like a duck and quacks like a duck, it is a duck." |
| **Inheritance Required?** | **Yes** (`class Concrete(BaseABC):`) | **No**. Any class matching the method signatures satisfies it. |
| **Runtime Enforcement** | Prevents instantiation if `@abstractmethod` is missing. | Static type checkers (`mypy`) enforce it; runtime checks optional with `@runtime_checkable`. |
| **Best Use Case** | Internal domain models, framework cores where strict hierarchy is desired. | Decoupling libraries, third-party plugin boundaries, test mocks. |

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Notifier(Protocol):
    def send(self, message: str, recipient: str) -> bool:
        ...

# No inheritance needed!
class TwilioSMS:
    def send(self, message: str, recipient: str) -> bool:
        print(f"SMS sent to {recipient}: {message}")
        return True

def notify_user(n: Notifier, msg: str, to: str):
    n.send(msg, to)

# Valid for both mypy and isinstance() checks:
notify_user(TwilioSMS(), "Hello", "+1234567890")
print(isinstance(TwilioSMS(), Notifier))  # True
```

---

### Q7. Compare `@dataclass`, `NamedTuple`, and Pydantic models in terms of performance, immutability, and validation.

**Answer:**

| Attribute | `@dataclass` | `NamedTuple` | Pydantic (`BaseModel`) |
| :--- | :--- | :--- | :--- |
| **Base Type** | Standard class with auto-generated dunder methods | Subclass of `tuple` | Metaclass-backed parsing engine |
| **Memory Footprint** | Standard class (can use `slots=True`) | Highly compact (native tuple C-array) | Higher overhead due to rich metadata |
| **Immutability** | Mutable by default; `frozen=True` supported | Strictly **immutable** | Mutable by default; configurable `frozen=True` |
| **Runtime Validation** | **No** (type hints are purely informational) | **No** (type hints are informational) | **Yes** (strict casting, parsing, schema validation) |
| **Performance** | Instant initialization ($O(1)$) | Fast C-level tuple initialization | Slower parsing overhead (mitigated by Pydantic V2 core in Rust) |
| **Primary Use Case** | Internal domain entities, data transfer within a service | Lightweight immutable records, coordinates, tuple returns | Parsing untrusted external HTTP request payloads, settings |

---

### Q8. How do you create a custom Context Manager using both a class and the `@contextmanager` generator? How are exceptions handled?

**Answer:**
* **1. Class-Based Approach:**
```python
import time

class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start
        # If exc_type is not None, returning True suppresses the exception;
        # Returning None or False allows it to propagate.
        return False
```

* **2. Generator-Based Approach (`contextlib.contextmanager`):**
```python
from contextlib import contextmanager
import sqlite3

@contextmanager
def db_transaction(db_path: str):
    conn = sqlite3.connect(db_path)
    try:
        print("Starting transaction...")
        yield conn  # Hand control to with-block
        conn.commit()
        print("Transaction committed.")
    except Exception as exc:
        conn.rollback()
        print(f"Transaction rolled back due to: {exc}")
        raise  # Re-raise unless suppression is intentional
    finally:
        conn.close()
        print("Connection closed.")
```

---

## Section 2: Advanced Decorators, Iterables & Generators

### Q9. How do you write a decorator that accepts arbitrary arguments? What is the execution flow?

**Answer:**
A decorator that accepts arguments requires **three levels of nested functions**:
1. **Outer factory function:** Accepts arguments meant for the decorator configuration and returns the actual decorator.
2. **Intermediate decorator function:** Accepts the target function.
3. **Inner wrapper function:** Intercepts execution, receives runtime `*args` and `**kwargs`, and calls the target.

```python
from functools import wraps
import time

def rate_limit(calls_per_second: int):
    min_interval = 1.0 / calls_per_second

    def decorator(func):
        last_called = 0.0

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            elapsed = time.time() - last_called
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called = time.time()
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_second=5)
def send_webhook(url: str):
    # Sends webhook throttled to 5 req/s
    pass
```

---

### Q10. How do you implement a class-based decorator to maintain state across invocations?

**Answer:**
A class-based decorator implements the `__call__` dunder method. The target function is captured in `__init__`, and the class instance becomes the callable wrapper:

```python
from functools import wraps

class CallCounter:
    def __init__(self, func):
        self.func = func
        self.count = 0
        wraps(func)(self)  # Preserves metadata on the class instance

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"Function {self.func.__name__} has been called {self.count} times.")
        return self.func(*args, **kwargs)

    def reset(self):
        self.count = 0

@CallCounter
def process_payment(amount: float):
    return f"Processed ${amount}"

process_payment(100)  # Call count: 1
process_payment(200)  # Call count: 2
print(process_payment.count)  # 2
```

---

### Q11. Explain bidirectional generator communication with `send()`, `throw()`, and `yield from`.

**Answer:**
Generators are not just data producers; they can also consume values sent by the caller:
* **`gen.send(value)`:** Resumes the generator and passes `value` into the expression where `yield` paused. On the first start, you must call `next(gen)` or `gen.send(None)` to prime it.
* **`gen.throw(typ, val, tb)`:** Raises an exception inside the generator at the point of the current yield.
* **`yield from subgenerator`:** Establishes a transparent bidirectional channel between the caller and a sub-generator, automatically delegating `send()`, `throw()`, and returning the sub-generator's final `return` value.

```python
def average_stream():
    total = 0.0
    count = 0
    avg = None
    while True:
        # yield avg sends value out; .send() injects new_val in
        new_val = yield avg
        if new_val is None:
            break
        total += new_val
        count += 1
        avg = total / count

gen = average_stream()
next(gen)  # Prime generator (returns None)
print(gen.send(10))  # 10.0
print(gen.send(20))  # 15.0
print(gen.send(30))  # 20.0
```

---

### Q12. How do `itertools.groupby`, `chain`, and `islice` work? What is the critical gotcha with `groupby`?

**Answer:**
* **`itertools.chain(*iterables)`:** Lazily stitches multiple iterables end-to-end without allocating combined lists in memory.
* **`itertools.islice(iterable, start, stop, step)`:** Slices an iterator lazily without materializing the underlying stream into RAM.
* **`itertools.groupby(iterable, keyfunc)`:** Groups adjacent items with matching keys.
* **CRITICAL GOTCHA with `groupby`:** Unlike SQL `GROUP BY`, `itertools.groupby` **only groups consecutive duplicate keys**. If identical keys are scattered across the iterable, separate groups are generated. **You must always sort the data by the grouping key before calling `groupby`:**

```python
from itertools import groupby

transactions = [
    {"user": "Alice", "amount": 50},
    {"user": "Bob", "amount": 20},
    {"user": "Alice", "amount": 30},
]

# WRONG: Alice appears twice because input wasn't sorted!
# CORRECT:
transactions.sort(key=lambda t: t["user"])
for user, group in groupby(transactions, key=lambda t: t["user"]):
    total = sum(t["amount"] for t in group)
    print(f"{user}: ${total}")
```

---

### Q13. How does `functools.lru_cache` work? What are its pitfalls regarding mutable arguments and cache stampedes?

**Answer:**
* **Mechanism:** `lru_cache` wraps a function with a Least Recently Used dictionary. It builds a key out of the positional and keyword arguments passed to the function.
* **Pitfall 1 - Unhashable Arguments:** Because cache keys are stored in an internal dictionary, all arguments passed to an `@lru_cache` function **must be hashable**. Passing a `list` or `dict` raises `TypeError: unhashable type`.
* **Pitfall 2 - Mutable Object Changes:** If an argument is a custom object whose state changes later, the cache cannot detect this mutation and will return stale results.
* **Pitfall 3 - Cache Stampede:** Under high concurrency (threads or asyncio), when a cached item expires or cold starts, hundreds of concurrent requests may simultaneously run the expensive function before the cache is repopulated.
* **Memory Management:** Always set an explicit `maxsize` (e.g., `@lru_cache(maxsize=1024)`). Setting `maxsize=None` results in an unbounded cache that leaks memory over long production runs.

---

### Q14. What are weak references (`weakref`), and how do they prevent circular reference memory leaks?

**Answer:**
* **Normal Reference:** Increments the target object's reference counter by 1. The object cannot be garbage collected as long as this reference exists.
* **Weak Reference (`weakref.ref` / `weakref.WeakValueDictionary`):** Points to an object **without** incrementing its reference counter. If only weak references to an object remain, the garbage collector immediately deallocates it.

**Practical Backend Use Case - In-Memory Caches:**
If an in-memory cache holds strong references to large data objects, they will never be freed even if the rest of the application has dropped them. Using `WeakValueDictionary` ensures the cache only holds objects that are actively in use elsewhere:

```python
import weakref

class HeavySessionData:
    def __init__(self, session_id: str):
        self.session_id = session_id

# Cache that automatically evicts dead objects
session_cache = weakref.WeakValueDictionary()

s = HeavySessionData("sess_123")
session_cache["sess_123"] = s
print("sess_123" in session_cache)  # True

del s  # No strong references left
print("sess_123" in session_cache)  # False! Automatically evicted.
```

---

### Q15. Compare `__getattr__` and `__getattribute__`. How do you avoid infinite recursion?

**Answer:**
* **`__getattr__(self, name)`:** Fallback hook called **only if** the attribute was **not found** in the object's `__dict__`, class hierarchy, or descriptors. Safe for implementing dynamic proxying or lazy loading.
* **`__getattribute__(self, name)`:** Unconditionally invoked for **every single attribute access**, regardless of whether the attribute exists or not.

**The Infinite Recursion Trap:**
Inside `__getattribute__`, if you write `self.attribute` or `self.__dict__`, Python intercepts that access and calls `__getattribute__` again, leading to an infinite recursion crash (`RecursionError: maximum recursion depth exceeded`).
* **Fix:** Always route internal attribute lookups through `super().__getattribute__(name)`:

```python
class AuditProxy:
    def __init__(self, target):
        super().__setattr__("target", target)

    def __getattribute__(self, name):
        print(f"[AUDIT] Accessing attribute: {name}")
        # MUST use super() to avoid recursion:
        target = super().__getattribute__("target")
        return getattr(target, name)
```

---

## Section 3: Concurrency, Asyncio & Multiprocessing

### Q16. What is the Global Interpreter Lock (GIL)? How does it affect CPU-bound vs I/O-bound workflows?

**Answer:**
The GIL is a mutual-exclusion lock used by the CPython memory manager to prevent multiple native OS threads from executing Python bytecodes concurrently. It exists because CPython's reference counting is not thread-safe.

* **Impact on I/O-Bound Workflows:** Multi-threading is **effective**. When a thread initiates an I/O operation (socket read, file write, database query) or calls a C-extension (like NumPy or OpenCV), it **releases the GIL**, allowing other Python threads to execute while the first thread waits on the network/disk.
* **Impact on CPU-Bound Workflows:** Multi-threading is **ineffective (and often slower)**. Multiple threads competing for CPU cores will continuously fight over the single GIL lock, adding context-switching overhead without gaining true parallelism. CPU-bound workloads must use **`multiprocessing`** (separate processes, each with its own GIL and memory space) or offload compute to native extensions.

---

### Q17. How do you choose between `threading`, `multiprocessing`, and `asyncio` for a backend architecture?

**Answer:**

```
Workload Evaluation:
┌─────────────────────────┐
│ Is task CPU or I/O bound?│
└────────────┬────────────┘
             ├──────────────────────────┐
             ▼                          ▼
      [ CPU-Bound ]               [ I/O-Bound ]
             │                          │
             ▼                          ▼
   Use multiprocessing        High concurrency (>5k sockets)?
 (Data crunching, crypto,               │
   image processing)                    ├───► YES: Use asyncio (FastAPI, aiohttp)
                                        │
                                        └───► NO: Use threading / thread pool
                                              (Legacy DB drivers, simpler code)
```

* **`multiprocessing`:** Heavy memory footprint (each process duplicates interpreter overhead, ~30–50 MB RAM per worker). Expensive inter-process communication (IPC via pickling). Provides true multi-core CPU utilization.
* **`threading`:** Lightweight memory footprint (shared memory space). Subject to GIL. Prone to race conditions on shared state.
* **`asyncio`:** Single-threaded cooperative multitasking. Ultra-low RAM overhead (~tens of thousands of concurrent connections on a single thread). Requires non-blocking, async-native libraries (`asyncpg`, `httpx`). A single synchronous blocking call freezes the entire event loop.

---

### Q18. How does the `asyncio` event loop work? What is the lifecycle of a coroutine vs a task?

**Answer:**
* **Event Loop:** A single-threaded runtime loop that monitors an array of active I/O file descriptors (using OS primitives like `epoll` on Linux or `kqueue` on macOS). When an event occurs, it wakes up the corresponding callback.
* **Coroutine (`async def`):** Calling a coroutine function does not execute it; it returns a coroutine object. It only executes when explicitly `await`ed or scheduled on the loop.
* **`asyncio.Task` (`asyncio.create_task(coro)`):** Wraps a coroutine into an independent unit of execution and schedules it on the event loop immediately. It allows the background task to make concurrent progress while the current function continues running.

```python
import asyncio

async def fetch_metrics(service_id: str):
    await asyncio.sleep(1)  # Simulates non-blocking network I/O
    return {"service": service_id, "healthy": True}

async def main():
    # Schedules tasks concurrently on the active loop:
    task1 = asyncio.create_task(fetch_metrics("svc_auth"))
    task2 = asyncio.create_task(fetch_metrics("svc_billing"))

    # Both tasks run concurrently while we await results:
    res1 = await task1
    res2 = await task2
    print(res1, res2)

asyncio.run(main())
```

---

### Q19. Compare `asyncio.gather()`, `asyncio.wait()`, and Python 3.11+ `TaskGroup`.

**Answer:**
* **`asyncio.gather(*coros, return_exceptions=False)`:** Concurrently executes an unpack of coroutines and returns an aggregated list of results preserving input order. If `return_exceptions=False`, the first exception aborts the gather, but orphaned sibling tasks continue running in the background.
* **`asyncio.wait(tasks, return_when=...)`:** Lower-level API that accepts a set of Tasks. Yields a tuple of `(done, pending)` based on criteria like `FIRST_COMPLETED` or `ALL_COMPLETED`.
* **`asyncio.TaskGroup` (Python 3.11+ Recommended):** Implements **Structured Concurrency**. If any task inside the context manager fails, all remaining sibling tasks are **automatically cancelled**, and exceptions are cleanly aggregated into an `ExceptionGroup`:

```python
async def run_pipeline():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(step_one())
        t2 = tg.create_task(step_two())
    # Both tasks guaranteed to be finished or cleanly cancelled here
    print(t1.result(), t2.result())
```

---

### Q20. How do you safely execute blocking, CPU-heavy, or synchronous I/O operations inside an `asyncio` application?

**Answer:**
Any synchronous call (e.g., `requests.get()`, heavy image resizing, or CPU crypto hashing) executed directly in an `async` function will block the single-threaded event loop, preventing all other concurrent requests from being processed.

**Solution:** Offload the blocking operation to a thread or process pool using `loop.run_in_executor()`:

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def blocking_io_call():
    time.sleep(2)  # Simulates legacy synchronous library
    return "done"

def heavy_cpu_math(n):
    return sum(i * i for i in range(n))

async def main():
    loop = asyncio.get_running_loop()

    # Offload blocking I/O to a background thread pool:
    with ThreadPoolExecutor() as pool:
        io_result = await loop.run_in_executor(pool, blocking_io_call)

    # Offload heavy CPU work to a separate process pool (bypasses GIL):
    with ProcessPoolExecutor() as process_pool:
        cpu_result = await loop.run_in_executor(process_pool, heavy_cpu_math, 10_000_000)

    print(io_result, cpu_result)
```

---

### Q21. Explain `threading.Lock`, `RLock`, and `Semaphore`. What is a race condition, and how does `RLock` solve re-entrant locking?

**Answer:**
* **Race Condition:** Occurs when multiple threads concurrently read and mutate shared mutable state without synchronization, producing inconsistent or corrupted data.
* **`threading.Lock`:** A standard mutual exclusion lock. If a thread that already holds the lock attempts to acquire it again, it **deadlocks with itself**.
* **`threading.RLock` (Re-entrant Lock):** Tracks the thread that currently owns it and a recursion count. The owning thread can acquire the lock multiple times without deadlocking; each `acquire()` must be balanced by a corresponding `release()`.
* **`threading.Semaphore(n)`:** Allows up to $n$ threads to access a resource concurrently (ideal for connection pool throttling).

```python
import threading

class ThreadSafeAccount:
    def __init__(self, balance: float):
        self.balance = balance
        self._lock = threading.RLock()  # Re-entrant lock

    def withdraw(self, amount: float):
        with self._lock:
            self.balance -= amount

    def transfer(self, target_account, amount: float):
        # Calls withdraw() while already holding the lock!
        with self._lock:
            self.withdraw(amount)  # Succeeds with RLock, deadlocks with standard Lock
            target_account.deposit(amount)
```

---

### Q22. How does CPython manage memory? Explain reference counting, cyclic garbage collection, and generation thresholds.

**Answer:**
CPython combines two memory management systems:
1. **Reference Counting (Primary System):**
   * Every Python object has an internal `ob_refcnt` field.
   * When referenced (assignment, passed to function, added to list), count increments. When references go out of scope or are deleted (`del`), count decrements.
   * As soon as `ob_refcnt == 0`, the object's memory is **immediately freed**.

2. **Generational Cyclic Garbage Collector (Secondary System):**
   * Reference counting alone cannot clean up **reference cycles** (e.g., Object A references Object B, and Object B references Object A; both counts remain at 1 even if all external references are gone).
   * CPython uses a generational cyclic GC that classifies all container objects into three generations:
     * **Generation 0:** Newly allocated objects. Scanned most frequently.
     * **Generation 1:** Objects surviving Gen 0 collections.
     * **Generation 2:** Long-lived objects (surviving Gen 1). Scanned least frequently.
   * The cyclic GC periodically pauses and runs an algorithm tracking pointer graphs to detect isolated circular islands and deallocates them.

---

## Section 4: Scenario-Based Engineering & Production Debugging

### Q23. Scenario: A long-running background worker process gradually consumes gigabytes of memory over several days without ever releasing it. How do you diagnose and resolve this circular reference leak?

**Answer:**
**Diagnostics:**
1. Use the built-in **`tracemalloc`** module to take memory snapshots over time and compare the differences:
```python
import tracemalloc

tracemalloc.start()
snapshot1 = tracemalloc.take_snapshot()
# ... wait or run suspicious worker batch ...
snapshot2 = tracemalloc.take_snapshot()

top_stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in top_stats[:10]:
    print(stat)
```
2. Use **`objgraph`** to find leaking object types and inspect their backreferences:
```python
import objgraph
objgraph.show_most_common_types(limit=5)
# Generates a PNG graph showing who holds references to leaked objects:
# objgraph.show_backrefs(objgraph.by_type("LeakingNode")[:1], filename="leak.png")
```

**Common Root Causes & Fixes:**
* **Unbounded Global Caches:** Dictionaries or lists at module level accumulating data. Fix: Use `weakref.WeakValueDictionary` or an LRU cache with an explicit `maxsize`.
* **Closures retaining large objects:** Inner functions capturing outer variables. Fix: Explicitly set unneeded large variables to `None` before closing functions.
* **Circular references with custom `__del__` methods:** (Prior to Python 3.4, objects with `__del__` in cycles were marked uncollectable). Ensure clean teardown using explicit cleanup methods instead of relying on `__del__`.

---

### Q24. Scenario: Design a generic, thread-safe in-memory cache with Time-To-Live (TTL) expiration in pure Python.

**Answer:**
```python
import time
from threading import RLock
from typing import Any, Optional, Dict, Tuple

class TTLCache:
    def __init__(self, default_ttl_seconds: float = 60.0):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = RLock()

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        expiry = time.time() + (ttl_seconds if ttl_seconds is not None else self.default_ttl)
        with self._lock:
            self._store[key] = (value, expiry)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key not in self._store:
                return default
            value, expiry = self._store[key]
            if time.time() > expiry:
                del self._store[key]  # Lazy eviction on read
                return default
            return value

    def purge_expired(self) -> int:
        """Periodic background cleanup method."""
        now = time.time()
        with self._lock:
            expired_keys = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired_keys:
                del self._store[k]
            return len(expired_keys)
```

---

### Q25. Scenario: Implement an asynchronous rate limiter in Python using the Token Bucket algorithm to protect an external API from getting throttled.

**Answer:**
```python
import asyncio
import time

class AsyncTokenBucket:
    def __init__(self, rate_per_second: float, capacity: float):
        self.rate = rate_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens_needed: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now

                # Replenish tokens based on elapsed time:
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= tokens_needed:
                    self.tokens -= tokens_needed
                    return

                # Calculate sleep duration until sufficient tokens regenerate:
                deficit = tokens_needed - self.tokens
                sleep_time = deficit / self.rate
                await asyncio.sleep(sleep_time)

# Usage in backend:
limiter = AsyncTokenBucket(rate_per_second=10.0, capacity=10.0)

async def call_external_gateway():
    await limiter.acquire(1.0)
    # Perform HTTP request...
```

---

### Q26. Scenario: A nightly batch job queries 1,000,000 database records via an ORM and crashes with an OOM error. How do you rewrite the data-loading pipeline using generator chunking?

**Answer:**
**Problem:** A standard ORM call like `queryset.all()` attempts to load all 1,000,000 model objects into memory simultaneously, exhausting available RAM.

**Solution: Server-Side Cursors and Generator Chunking:**
```python
def chunked_query_processor(fetch_chunk_callable, chunk_size: int = 5000):
    """
    Yields records one-by-one while keeping memory consumption bounded
    to exactly chunk_size records in memory at any given time.
    """
    offset = 0
    while True:
        chunk = fetch_chunk_callable(limit=chunk_size, offset=offset)
        if not chunk:
            break
        for record in chunk:
            yield record
        offset += chunk_size

# Example consumption:
def fetch_users_from_db(limit: int, offset: int):
    # Executes SQL with LIMIT :limit OFFSET :offset or uses DB server-side cursor
    return db.query("SELECT id, email, status FROM users LIMIT ? OFFSET ?", limit, offset)

for user in chunked_query_processor(fetch_users_from_db, chunk_size=5000):
    process_user_statement(user)  # Memory stays strictly capped!
```
* **Best Practice:** If using raw databases or SQLAlchemy, enable server-side cursors (`yield_per(chunk_size)`) so records are streamed directly from the socket rather than buffered by the driver.

---

### Q27. Scenario: Multiple worker threads share a dictionary that tracks active user sessions. Occasionally, sessions disappear or the process throws `RuntimeError: dictionary changed size during iteration`. How do you fix this?

**Answer:**
* **Root Cause:** Dictionaries in Python are not thread-safe for concurrent read-writes or mutations during iteration. When Thread A iterates over `sessions.items()` while Thread B adds or deletes a key, Python detects the size mismatch and raises `RuntimeError`.
* **Fix 1: Synchronize with a Lock:**
```python
from threading import RLock

class SessionManager:
    def __init__(self):
        self._sessions = {}
        self._lock = RLock()

    def remove_session(self, session_id: str):
        with self._lock:
            self._sessions.pop(session_id, None)

    def get_active_user_ids(self) -> list:
        with self._lock:
            # Taking a snapshot of keys or values while locked prevents iteration errors:
            return list(self._sessions.keys())
```
* **Fix 2: Iterate over a snapshot:** If locking during long iterations would block other workers, take an atomic snapshot of keys:
```python
for session_id in list(sessions.keys()):  # list() creates a static copy of keys
    validate_session(session_id)
```

---

### Q28. Scenario: An async worker initiates a background task that calls an external webhook. If the webhook hangs, the entire task must time out after 5 seconds and perform cleanup. How do you implement this safely?

**Answer:**
Use `asyncio.wait_for()` or `asyncio.timeout` (Python 3.11+). When a timeout occurs, the inner task is sent a cancellation request (`CancelledError`), and your code must handle cleanup in a `finally` block:

```python
import asyncio

async def call_webhook_with_teardown(client_session, url: str):
    try:
        # Python 3.11+ context-manager syntax:
        async with asyncio.timeout(5.0):
            print("Initiating webhook request...")
            response = await client_session.post(url, timeout=None)
            return await response.json()
    except TimeoutError:
        print("[WARN] Webhook timed out after 5.0 seconds.")
        # Trigger fallback or alert metrics
        return {"status": "TIMEOUT"}
    except asyncio.CancelledError:
        print("[INFO] Task was externally cancelled. Cleaning up socket...")
        raise  # Must re-raise CancelledError to allow proper task cancellation
    finally:
        print("Releasing reserved resources and decrementing metrics counter.")
```

---

### Q29. Scenario: Build a dynamic plugin loader that scans a directory, dynamically imports Python modules at runtime using `importlib`, and registers all classes implementing a specific base class.

**Answer:**
```python
import importlib
import inspect
from pathlib import Path
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    @abstractmethod
    def execute(self, payload: dict) -> dict:
        pass

def load_plugins(plugins_directory: str) -> dict:
    registry = {}
    path = Path(plugins_directory)

    for py_file in path.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        module_name = py_file.stem
        # Dynamically import module
        module = importlib.import_module(f"{plugins_directory}.{module_name}")

        # Inspect all classes inside the imported module
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, BasePlugin) and cls is not BasePlugin:
                print(f"Registered plugin: {name} from {module_name}")
                registry[name] = cls()

    return registry
```

---

### Q30. Scenario: An API endpoint has high p99 latency in staging. How do you profile the slow code path using `cProfile` and `timeit` to pinpoint whether the bottleneck is CPU-bound or database/network-bound?

**Answer:**
1. **Micro-benchmarking isolated functions with `timeit`:**
```python
import timeit

setup_code = "from my_app.services import serialize_user; u = {'id': 1, 'name': 'Alice'}"
benchmark = timeit.timeit("serialize_user(u)", setup=setup_code, number=100_000)
print(f"Time for 100k executions: {benchmark:.4f}s")
```

2. **Full execution profiling with `cProfile` and `pstats`:**
```python
import cProfile
import pstats
from my_app.views import generate_invoice_view

profiler = cProfile.Profile()
profiler.enable()

# Execute target logic
generate_invoice_view(order_id=5001)

profiler.disable()

# Sort by cumulative time spent inside the function and its children
stats = pstats.Stats(profiler)
stats.strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE).print_stats(15)
```

**Interpreting Results:**
* If top cumulative time is concentrated in `socket.recv` or `psycopg2.wait`, the bottleneck is **I/O-bound** (slow database queries, un-indexed joins, or remote API latency).
* If top cumulative time is concentrated in internal loops, regex matching, or `json.loads`, the bottleneck is **CPU-bound** (inefficient algorithms, unnecessary serializations, or lack of caching).

---

## Section 5: Advanced Concurrency, Metaprogramming & Production Scenarios

### Q31. Compare `asyncio.Event`, `asyncio.Condition`, and `asyncio.Queue`. When should each synchronization primitive be used in asynchronous services?

**Answer:**
* **`asyncio.Event`:** Manages an internal boolean flag (`set()`, `clear()`, `is_set()`). Tasks wait via `await event.wait()`. Ideal for **one-to-many broadcast notifications** (e.g., notifying all background workers that the database connection pool has finished initializing or that a shutdown signal has fired).
* **`asyncio.Condition`:** Combines an event with a lock. Allows tasks to wait (`await cond.wait()`) until a specific state predicate is satisfied, waking either one task (`cond.notify(1)`) or all tasks (`cond.notify_all()`). Ideal for stateful coordination (e.g., waiting for an in-memory buffer to reach a threshold size).
* **`asyncio.Queue`:** A thread-safe, coroutine-safe FIFO queue with optional `maxsize`. Provides built-in backpressure via `await queue.put()` and `await queue.get()`. Ideal for **producer-consumer pipelines**, distributing tasks evenly among a pool of worker coroutines.

---

### Q32. Explain `contextvars` in Python. Why can't you use `threading.local()` for request-scoped context in `asyncio` applications?

**Answer:**
* **Why `threading.local()` fails in `asyncio`:**
  In multi-threaded architectures (e.g., standard Flask/Django), each HTTP request is assigned a dedicated OS thread. `threading.local()` isolates data per thread. However, `asyncio` runs **thousands of concurrent requests on a single OS thread**. If Request A stores its `user_id` in `threading.local()`, Request B running on the same thread will overwrite or read Request A's data, causing severe data leakage bugs.
* **`contextvars` (PEP 567):**
  Provides **Context-Local Storage** that understands both threads and coroutine task boundaries. When a coroutine spawns a child task (`asyncio.create_task()`), `contextvars` creates a shallow copy of the current context. Mutations in the child task do not pollute the parent context, and sibling concurrent requests remain strictly isolated:

```python
import contextvars
import asyncio

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

async def handle_request(req_id: str):
    # Isolated per async task tree:
    token = request_id_var.set(req_id)
    try:
        await perform_db_query()
    finally:
        request_id_var.reset(token)

async def perform_db_query():
    # Reads current context safely
    print(f"Executing query for request: {request_id_var.get()}")
```

---

### Q33. How does `functools.singledispatch` work? How does it solve function overloading based on argument types in Python?

**Answer:**
Python does not support traditional method overloading where multiple functions share the same name with different type signatures (the last defined function simply overwrites previous ones).

`functools.singledispatch` transforms a regular function into a **generic function**, dispatching execution to specialized implementations based on the runtime type of the **first argument**:

```python
from functools import singledispatch
from decimal import Decimal

@singledispatch
def format_payload(val):
    raise NotImplementedError(f"Unsupported type: {type(val)}")

@format_payload.register(int)
def _(val: int):
    return f"INTEGER:{val}"

@format_payload.register(Decimal)
def _(val: Decimal):
    return f"CURRENCY:${val:.2f}"

@format_payload.register(list)
def _(val: list):
    return f"ARRAY:[{', '.join(map(str, val))}]"

print(format_payload(42))            # INTEGER:42
print(format_payload(Decimal("19.5"))) # CURRENCY:$19.50
print(format_payload(["a", "b"]))     # ARRAY:[a, b]
```
* Note: For dispatching based on multiple arguments or class methods, use `functools.singledispatchmethod` for instance methods.

---

### Q34. What is the difference between deep and shallow immutability? How do `types.MappingProxyType` and `types.SimpleNamespace` operate?

**Answer:**
* **Shallow Immutability:** An immutable container (like a `tuple`) cannot have elements added, removed, or replaced. However, if the tuple holds a reference to a mutable object (like a `list`), the nested list can still be mutated in-place:
```python
t = ([1, 2], "immutable_string")
t[0].append(3)  # ALLOWED! The list is mutated, violating deep immutability.
```
* **`types.MappingProxyType`:** Creates a **read-only view** of a dictionary. If external code attempts to mutate the proxy (`proxy["key"] = val`), it raises `TypeError`. However, if the underlying dict is modified, the proxy reflects that change:
```python
from types import MappingProxyType

internal_config = {"debug": False, "timeout": 30}
public_config = MappingProxyType(internal_config)
# public_config["debug"] = True -> TypeError: 'mappingproxy' object does not support item assignment
```
* **`types.SimpleNamespace`:** An alternative to a dictionary or lightweight class providing attribute-style access (`ns.host` instead of `ns["host"]`) with a clean `repr`, often used for mocking or structured function arguments.

---

### Q35. What is `sys.intern()`? When and how should a backend engineer use manual string interning to optimize memory?

**Answer:**
* **Automatic Interning:** CPython automatically interns string literals that look like Python identifiers (ASCII alphanumeric characters and underscores) during compilation.
* **Dynamic Strings:** Strings constructed dynamically at runtime (e.g., read from database columns, parsed from JSON, or read from CSV files) are **not automatically interned**. If you load 1,000,000 records containing repetitive status strings (`"PENDING"`, `"COMPLETED"`, `"FAILED"`), Python allocates 1,000,000 distinct string objects in memory.
* **Manual Interning (`sys.intern(s)`):** Enters the string into CPython's internal global interned string dictionary. If an identical string already exists, it returns a reference to the existing object and allows the new string to be immediately garbage collected:

```python
import sys

# Simulating parsing repeated statuses from an external feed:
raw_statuses = ["PENDING", "COMPLETED", "FAILED"] * 500_000

# ANTI-PATTERN: Allocates 1.5M string objects in RAM
data_raw = [s for s in raw_statuses]

# OPTIMIZED: Reuses the exact same 3 string objects in memory
data_interned = [sys.intern(s) for s in raw_statuses]

# Bonus: Comparing interned strings can use 'is' (O(1) pointer comparison):
print(sys.intern("PENDING") is sys.intern("PENDING"))  # True
```

---

### Q36. Compare cooperative multitasking (`asyncio`) with preemptive multitasking (OS threads). What happens if a coroutine never calls `await`?

**Answer:**
* **Preemptive Multitasking (OS Threads):** The operating system kernel scheduler arbitrarily interrupts running threads at any point in time (context switch) to give CPU time to other threads. Even if a thread enters an infinite calculation loop, the OS ensures other threads still receive CPU slices.
* **Cooperative Multitasking (`asyncio`):** A single OS thread executes coroutines. The event loop **cannot preempt or interrupt** a running coroutine. Execution is handed back to the event loop **only when the coroutine explicitly yields control** via an `await` expression on a non-blocking primitive.

**What happens if a coroutine never yields:**
If a coroutine enters a tight CPU loop (`while True: pass`) or calls a blocking synchronous function (`time.sleep(10)`), the **entire process freezes**. All other pending concurrent requests, health-check probes, and WebSocket heartbeats are completely starved and will time out.

---

### Q37. How do you test asynchronous code and mock external HTTP/DB calls using `unittest.mock` (`AsyncMock`, `patch`)?

**Answer:**
In Python 3.8+, `unittest.mock.AsyncMock` was introduced to properly mock coroutines and async context managers:

```python
import pytest
from unittest.mock import patch, AsyncMock

# Service under test
async def fetch_user_balance(client, user_id: int) -> float:
    async with client.get(f"/users/{user_id}/balance") as response:
        data = await response.json()
        return data["balance"]

# Async unit test
@pytest.mark.asyncio
async def test_fetch_user_balance():
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.json.return_value = {"balance": 250.75}

    # Setting up async context manager mock:
    mock_client.get.return_value.__aenter__.return_value = mock_response

    balance = await fetch_user_balance(mock_client, user_id=101)
    assert balance == 250.75
    mock_client.get.assert_called_once_with("/users/101/balance")
```

---

### Q38. How does Python evaluate late-binding closures inside loops? How do you fix the classic closure loop trap?

**Answer:**
* **The Gotcha:** Python closures look up variables in enclosing scopes **by name at the time the function is called**, not when the function is defined:

```python
# THE TRAP:
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])  # [2, 2, 2] -> All return the final value of i!
```

* **The Fix - Default Argument Binding:**
Default arguments are evaluated once at function **definition time**. By binding the loop variable to a default argument, you freeze its current value into the local scope:

```python
# FIX 1: Default argument idiom
funcs = []
for i in range(3):
    funcs.append(lambda i=i: i)

print([f() for f in funcs])  # [0, 1, 2] -> Correct!

# FIX 2: functools.partial
from functools import partial
funcs = [partial(lambda val: val, i) for i in range(3)]
```

---

### Q39. What is `__missing__` on a `dict` subclass? How does `collections.defaultdict` utilize it?

**Answer:**
* **`__missing__(self, key)`:** A special dunder method defined on `dict` subclasses. When `dict.__getitem__(key)` fails to locate `key` in the dictionary, rather than immediately raising `KeyError`, Python delegates to `self.__missing__(key)` if implemented.
* **How `defaultdict` works:** `collections.defaultdict(default_factory)` inherits from `dict` and defines `__missing__` to call `default_factory()`, insert the returned value into the dictionary under `key`, and return it.

```python
class LowercaseDict(dict):
    """Automatically converts missing keys to lowercase before lookup."""
    def __missing__(self, key):
        if isinstance(key, str) and key != key.lower():
            lower_key = key.lower()
            if lower_key in self:
                return self[lower_key]
        raise KeyError(key)

d = LowercaseDict({"api_key": "secret_123"})
print(d["API_KEY"])  # Returns 'secret_123' via __missing__
```

---

### Q40. How do asynchronous generators and context managers work under the hood? What are `__aiter__`, `__anext__`, `__aenter__`, and `__aexit__`?

**Answer:**
* **Asynchronous Iterator Protocol:**
  * `__aiter__(self)`: Must return an asynchronous iterator object.
  * `__anext__(self)`: Must return an **awaitable** that resolves to the next item or raises `StopAsyncIteration`.
  * Used by `async for item in async_iterable:`
* **Asynchronous Context Manager Protocol:**
  * `__aenter__(self)`: Returns an awaitable that sets up resources.
  * `__aexit__(self, exc_type, exc_val, exc_tb)`: Returns an awaitable that performs teardown.
  * Used by `async with async_resource as res:`

```python
class AsyncMessageStream:
    def __init__(self, count: int):
        self.count = count
        self.current = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current < self.count:
            await asyncio.sleep(0.01)  # Simulates async I/O
            self.current += 1
            return f"msg_{self.current}"
        raise StopAsyncIteration
```

---

### Q41. Compare `ThreadPoolExecutor` and `ProcessPoolExecutor`. What happens when worker processes crash or exceed memory?

**Answer:**
* **`ThreadPoolExecutor`:**
  * Executes callables on worker threads within the same memory space.
  * Low overhead. If a worker thread throws an unhandled exception, the exception is captured in the returned `Future` object and re-raised when calling `.result()`. The thread pool remains intact.
* **`ProcessPoolExecutor`:**
  * Spawns separate OS processes using `multiprocessing`.
  * All arguments and return values must be **pickleable**.
  * **Worker Crashes (OOM / Segfault):** If a child worker process is killed by the OS (e.g., Linux OOMKiller), it dies abruptly without returning a serialized exception. The executor catches the broken communication channel and raises **`BrokenProcessPool: A process in the process pool was terminated abruptly`**. All remaining pending futures in the pool fail.

---

### Q42. What is `functools.partial`? How does it differ from a `lambda` in performance and inspection?

**Answer:**
* **`functools.partial(func, *args, **kwargs)`:** Returns a callable partial object that freezes a portion of a function's arguments and keyword arguments.
* **Advantages over `lambda`:**
  1. **Introspectability:** A `partial` object exposes `.func`, `.args`, and `.keywords`, allowing serializers, debuggers, and frameworks to inspect the bound parameters. A lambda is an opaque code block.
  2. **Performance:** Implemented in C in CPython; faster execution overhead than invoking a Python-level lambda frame.
  3. **Avoiding Late-Binding Gotchas:** Evaluates argument references at creation time, preventing closure variable mutation bugs.

```python
from functools import partial

def send_email(smtp_server, timeout, recipient, subject, body):
    pass

# Freeze base server and timeout parameters:
send_corp_email = partial(send_email, "smtp.corp.internal", 30)
send_corp_email("user@example.com", "Welcome", "Hello!")
```

---

### Q43. What is the difference between `__dir__` and `__dict__`? How do dynamic proxies implement `__dir__`?

**Answer:**
* **`__dict__`:** The internal dictionary mapping an individual object or class's namespace to its attributes. Only includes attributes directly bound to that specific object.
* **`__dir__()`:** Called by the built-in `dir(obj)`. Returns a sorted list of all valid attribute names available on the object, including attributes inherited from parents, descriptors, metaclass attributes, and dynamically resolved properties.
* **Dynamic Proxies:** If an object uses `__getattr__` to dynamically forward calls to a wrapped target, standard tools and IDE autocompletion cannot detect the forwarded methods. Implementing `__dir__` enables autocompletion and inspection tools (`inspect.getmembers`) to see dynamic attributes:

```python
class DynamicServiceProxy:
    def __init__(self, target_service):
        self._target = target_service

    def __getattr__(self, name):
        return getattr(self._target, name)

    def __dir__(self):
        # Merge local proxy attributes with underlying service attributes
        return sorted(set(super().__dir__() + dir(self._target)))
```

---

### Q44. How does Python's standard `logging` hierarchy work? Why does duplicate log output occur, and how do you prevent it?

**Answer:**
* **Logger Hierarchy:** Loggers are organized in a dot-separated naming hierarchy (e.g., `"app.services.billing"` is a child of `"app.services"`, which is a child of `"app"`, which inherits from root `""`).
* **Propagation (`logger.propagate`):** By default, when a message is logged to a child logger, after handling it locally, the record is **passed up to the parent logger's handlers** recursively until it reaches the root logger.
* **Why Duplicate Logs Occur:**
  1. A handler is attached to the child logger (`"app.services"`).
  2. The parent or root logger *also* has a handler attached (e.g., basic config attached a console stream).
  3. The child logs the message via its own handler, then propagates the record up to the root, which logs it again!
* **Fix:** If a child logger configures its own handlers, disable propagation:
```python
logger = logging.getLogger("app.services")
logger.addHandler(custom_handler)
logger.propagate = False  # Prevents passing records to root handlers
```

---

### Q45. Scenario: Implement an async Semaphore-governed worker pool that processes 10,000 URLs with a strict concurrency ceiling of 50 simultaneous connections.

**Answer:**
```python
import asyncio
import aiohttp

async def fetch_url(session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, url: str) -> dict:
    async with semaphore:  # Capped at exactly 50 concurrent requests
        try:
            async with session.get(url, timeout=10) as response:
                return {"url": url, "status": response.status}
        except Exception as exc:
            return {"url": url, "error": str(exc)}

async def crawl_all(urls: list[str], max_concurrency: int = 50):
    sem = asyncio.Semaphore(max_concurrency)
    connector = aiohttp.TCPConnector(limit=max_concurrency)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_url(session, sem, url) for url in urls]
        # Streams results as they finish to avoid buffering all in memory
        results = await asyncio.gather(*tasks)
        return results

# Invocation:
# asyncio.run(crawl_all(["https://example.com"] * 10_000))
```

---

### Q46. Scenario: Design a thread-safe producer-consumer system with graceful shutdown using `queue.Queue` and Poison Pills.

**Answer:**
```python
import threading
import queue
import time

# Sentinel value representing termination
POISON_PILL = object()

def producer(work_queue: queue.Queue, items: list):
    for item in items:
        work_queue.put(item)
    print("Producer finished submitting work.")

def worker(work_queue: queue.Queue, worker_id: int):
    while True:
        item = work_queue.get()
        if item is POISON_PILL:
            work_queue.task_done()
            print(f"Worker {worker_id} received poison pill. Shutting down.")
            break

        try:
            # Process unit of work
            print(f"Worker {worker_id} processing {item}")
            time.sleep(0.05)
        finally:
            work_queue.task_done()

def run_system():
    q = queue.Queue(maxsize=100)
    num_workers = 3
    threads = []

    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(q, i))
        t.start()
        threads.append(t)

    producer(q, [f"job_{i}" for i in range(20)])

    # Graceful shutdown: Put one poison pill per worker thread
    for _ in range(num_workers):
        q.put(POISON_PILL)

    # Wait for all tasks to be acknowledged:
    q.join()
    for t in threads:
        t.join()
    print("All workers shut down cleanly.")
```

---

### Q47. Scenario: An async task checking out a connection from a database pool is cancelled midway. The connection leaks and remains permanently checked out. How do you fix this?

**Answer:**
* **Root Cause:** When an async task is cancelled, an `asyncio.CancelledError` is raised at the current `await` suspension point. If connection release logic is not wrapped in a `try...finally` block, the exception bypasses cleanup:

```python
# LEAKY ANTI-PATTERN:
async def execute_query_leaky(pool, sql):
    conn = await pool.acquire()
    # If task is cancelled while awaiting fetch(), conn.release() NEVER runs!
    data = await conn.fetch(sql)
    await pool.release(conn)
    return data

# IDIOMATIC SAFE PATTERN:
async def execute_query_safe(pool, sql):
    # Async context manager guarantees __aexit__ executes even on CancelledError
    async with pool.acquire() as conn:
        return await conn.fetch(sql)

# OR MANUAL TRY-FINALLY:
async def execute_query_manual(pool, sql):
    conn = await pool.acquire()
    try:
        return await conn.fetch(sql)
    finally:
        # Guaranteed cleanup regardless of CancelledError or runtime exceptions
        await pool.release(conn)
```

---

### Q48. Scenario: Write a reusable validation descriptor that enforces field types and numeric bounds across model attributes.

**Answer:**
```python
class ValidatedField:
    def __init__(self, expected_type, min_val=None, max_val=None):
        self.expected_type = expected_type
        self.min_val = min_val
        self.max_val = max_val

    def __set_name__(self, owner, name):
        self.storage_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.storage_name, None)

    def __set__(self, instance, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(f"Expected {self.expected_type.__name__}, got {type(value).__name__}")
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"Value must be >= {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Value must be <= {self.max_val}")
        setattr(instance, self.storage_name, value)

class InventoryItem:
    quantity = ValidatedField(int, min_val=0, max_val=10_000)
    price = ValidatedField(float, min_val=0.01)

    def __init__(self, quantity: int, price: float):
        self.quantity = quantity
        self.price = price

item = InventoryItem(10, 19.99)
# item.quantity = -1   -> ValueError: Value must be >= 0
# item.price = "free"  -> TypeError: Expected float, got str
```

---

### Q49. Scenario: Implement an async context manager that records endpoint execution time and emits latency metrics to StatsD/CloudWatch.

**Answer:**
```python
import time
from contextlib import asynccontextmanager

class MetricsClient:
    async def timing(self, metric_name: str, duration_ms: float):
        # Simulates sending UDP/HTTP packet to metrics daemon
        print(f"[METRIC] {metric_name}: {duration_ms:.2f}ms")

metrics = MetricsClient()

@asynccontextmanager
async def track_latency(metric_name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        # Schedule metric emission without blocking business logic
        await metrics.timing(metric_name, elapsed_ms)

# Usage in an async route or service:
async def handle_checkout():
    async with track_latency("api.checkout.latency"):
        await asyncio.sleep(0.12)  # Process order
```

---

### Q50. Scenario: Implement a cache-aside pattern with an in-memory lock to prevent a Cache Stampede (Dog-piling) when an expensive database key expires.

**Answer:**
```python
import asyncio

class SafeCacheAside:
    def __init__(self, cache_client, db_client):
        self.cache = cache_client
        self.db = db_client
        # Per-key locks prevent concurrent stampedes
        self._locks = {}
        self._global_lock = asyncio.Lock()

    async def _get_lock_for_key(self, key: str) -> asyncio.Lock:
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def get_or_set(self, key: str, ttl_seconds: int = 60):
        # 1. Fast read from cache
        value = await self.cache.get(key)
        if value is not None:
            return value

        # 2. Key expired or missed: Acquire lock for this specific key
        lock = await self._get_lock_for_key(key)
        async with lock:
            # 3. Double-checked locking: check if another worker already repopulated the cache
            value = await self.cache.get(key)
            if value is not None:
                return value

            print(f"[CACHE MISS] Fetching expensive data from DB for {key}...")
            value = await self.db.query_expensive_data(key)
            await self.cache.set(key, value, ttl=ttl_seconds)
            return value
```

---

