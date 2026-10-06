# Python Concurrency, Multithreading, Multiprocessing & AsyncIO Interview Guide

This guide contains **60 in-depth interview questions and answers** covering CPython concurrency internals, the Global Interpreter Lock (GIL), asynchronous programming (`asyncio`), multithreading (`threading`), multiprocessing (`multiprocessing`), synchronization primitives, and production architecture scenarios.

---

## Table of Contents
1. [Section 1: Core Concurrency Models & The GIL (Q1 - Q10)](#section-1-core-concurrency-models--the-gil)
2. [Section 2: Asyncio Fundamentals, Event Loop & Coroutines (Q11 - Q22)](#section-2-asyncio-fundamentals-event-loop--coroutines)
3. [Section 3: Asyncio Synchronization, Networking & Advanced Patterns (Q23 - Q33)](#section-3-asyncio-synchronization-networking--advanced-patterns)
4. [Section 4: Multithreading & Thread Synchronization (Q34 - Q44)](#section-4-multithreading--thread-synchronization)
5. [Section 5: Multiprocessing & Inter-Process Communication (IPC) (Q45 - Q53)](#section-5-multiprocessing--inter-process-communication-ipc)
6. [Section 6: Production Architectures, Hybrid Patterns & Scenarios (Q54 - Q60)](#section-6-production-architectures-hybrid-patterns--scenarios)

---

## Section 1: Core Concurrency Models & The GIL

### Q1. Define Concurrency, Parallelism, and Asynchronous execution. How do they differ in Python?

**Answer:**
* **Concurrency:** Managing multiple tasks by interleaving their execution over time. On a single CPU core, two tasks can be concurrent by switching back and forth; they make progress without necessarily running at the exact same physical millisecond.
* **Parallelism:** Executing multiple computational tasks simultaneously at the exact same physical instant on multiple distinct CPU cores or physical processors.
* **Asynchronous Programming:** A programming paradigm (often single-threaded) based on cooperative multitasking and non-blocking I/O. Tasks voluntarily yield execution when waiting for external events (network, disk, timers) so that other tasks can execute on the same thread.

**In Python:**
* `asyncio` provides **single-threaded cooperative concurrency** for I/O-bound tasks.
* `threading` provides **multi-threaded preemptive concurrency** governed by the OS scheduler, but subject to the GIL (preventing multi-core CPU parallelism).
* `multiprocessing` provides **true multi-core parallelism** by bypassing the GIL via separate OS processes with dedicated memory spaces.

---

### Q2. What is the Global Interpreter Lock (GIL)? Why does it exist in CPython, and which operations release it?

**Answer:**
* **What it is:** A mutual exclusion lock used by CPython to ensure that only one OS thread executes Python bytecode at any given moment, even on multi-core hardware.
* **Why it exists:**
  1. **Thread-Safe Memory Management:** CPython uses reference counting (`Py_INCREF`, `Py_DECREF`) for garbage collection. Without the GIL, concurrent threads modifying object reference counts would cause severe race conditions and memory corruption.
  2. **Fast Single-Threaded Performance:** A single global lock avoids the overhead of thousands of fine-grained locks across all individual objects and data structures.
  3. **C Extension Compatibility:** Simplified integrating legacy C libraries that were not thread-safe.
* **When the GIL is Released:**
  1. **I/O Operations:** Network socket operations, file reads/writes, and `time.sleep()`.
  2. **Computation in C Extensions:** Optimized libraries like NumPy, OpenCV, cryptography, and PyTorch release the GIL before performing intensive C/Fortran/CUDA matrix computations.
  3. **Bytecode Interval (Check Interval):** In CPython 3.2+, the interpreter releases the GIL every 5 milliseconds (configurable via `sys.setswitchinterval()`) to give other waiting threads a chance to run.

---

### Q3. How does the GIL affect CPU-bound vs. I/O-bound workloads across threads, processes, and coroutines?

**Answer:**

| Concurrency Model | I/O-Bound Workload | CPU-Bound Workload | GIL Impact |
| :--- | :--- | :--- | :--- |
| **`asyncio` (Coroutines)** | **Ideal:** High throughput, single thread, negligible context-switch overhead. | **Poor:** Blocks the entire event loop; starves all concurrent requests. | GIL is irrelevant because execution is single-threaded. |
| **`threading` (OS Threads)** | **Effective:** Threads waiting on network/disk release the GIL, allowing other threads to run. | **Ineffective (often slower):** Threads constantly fight for the GIL, adding OS context-switching overhead. | GIL severely bottlenecks CPU-bound execution to a single core. |
| **`multiprocessing` (Processes)** | **Good, but high overhead:** Can handle I/O, but process creation and memory usage are heavy. | **Ideal:** Scales linearly across physical CPU cores; completely bypasses the GIL. | Each process has its own Python interpreter and its own independent GIL. |

---

### Q4. Provide a concrete decision matrix: When should you choose `asyncio` vs `threading` vs `multiprocessing`?

**Answer:**

```
                                Workload Type?
                               /              \
                     I/O-Bound                  CPU-Bound
                    /         \                          \
       Network / Web Sockets   Blocking C-Libs / Disk     Data Science / Image Processing / Math
       High Concurrency (10k+)    Low Concurrency (10-100)               |
               |                         |                               |
          Use ASYNCIO              Use THREADING               Use MULTIPROCESSING
      (FastAPI, aiohttp)         (SQLAlchemy sync, disk)       (ProcessPoolExecutor, Celery)
```

* **Choose `asyncio` when:**
  * Handling thousands of concurrent network connections (chat servers, WebSocket gateways, microservice fan-outs).
  * Libraries used have native async drivers (`asyncpg`, `aiohttp`, `httpx`).
* **Choose `threading` when:**
  * Integrating with legacy synchronous libraries (e.g., standard `requests`, older DBAPI drivers).
  * Handling moderate I/O concurrency (tens or hundreds of threads).
  * Executing native C-extensions that release the GIL (e.g., NumPy heavy processing).
* **Choose `multiprocessing` when:**
  * Doing CPU-heavy data parsing, video encoding, cryptography, image transformations, or machine learning training on multi-core CPUs.

---

### Q5. What are atomic operations in Python under the GIL? Why can `count += 1` cause a race condition even with the GIL?

**Answer:**
* **Atomic Operation:** An operation that translates to a single bytecode instruction that CPython executes without releasing the GIL midway.
  * Examples: `list.append()`, reading a dictionary key `d[k]`, setting an attribute `d[k] = v`.
* **Why `count += 1` is NOT atomic:**
  `count += 1` compiles into **4 distinct bytecode instructions**:
  ```
  1. LOAD_GLOBAL     (count)
  2. LOAD_CONST      (1)
  3. BINARY_OP       (+)
  4. STORE_GLOBAL    (count)
  ```
* If thread A executes instructions 1 and 2, and CPython context-switches to thread B before instruction 4, thread B reads the old `count`, increments it, and writes it back. When thread A resumes, it overwrites thread B's increment with its stale calculation.
* **Key Interview Takeaway:** **The GIL does NOT guarantee thread safety at the application level.** Any compound operation requires an explicit `threading.Lock`.

---

### Q6. What is Free-Threaded Python (PEP 703 / Python 3.13 without the GIL)? What does it mean for multithreading?

**Answer:**
* **PEP 703 ("Free-Threaded CPython"):** Introduced in Python 3.13 as an optional build configuration (`--disable-gil`).
* **How it replaces the GIL:**
  1. **Biased Reference Counting:** Fast, single-owner reference counts for thread-local objects; atomic increments only when objects are shared across threads.
  2. **Mimalloc Memory Allocator:** Thread-safe, lock-free memory allocation.
  3. **Thread-Safe Collections:** Internal locking on dictionaries and lists.
* **Impact:**
  * Python threads can run pure Python bytecode in true multi-core physical parallelism.
  * Eliminates the need to spawn heavy `multiprocessing` workers for CPU-bound Python workloads.

---

### Q7. Explain OS Threads vs Green Threads vs Coroutines. What is cooperative vs preemptive multitasking?

**Answer:**
* **OS Threads (Preemptive):** Managed directly by the operating system kernel. The kernel scheduler preempts (interrupts) running threads at arbitrary times to balance CPU cores.
  * *Pros:* Transparent scheduling across cores.
  * *Cons:* Expensive context switches, larger memory footprint (typically 1–8 MB stack per thread).
* **Green Threads (Virtual Threads / Fibers):** Managed by a user-space runtime (e.g., Go Goroutines, Gevent/Eventlet via monkey-patching). The runtime preempts or switches them cooperatively without kernel involvement.
* **Coroutines (`asyncio` - Cooperative):** Language-level constructs that yield execution explicitly via keywords like `await` or `yield`.
  * *Pros:* Ultra-lightweight (~few KB memory), zero OS context-switching overhead, no locks needed for in-memory structures if no `await` sits between reads and writes.
  * *Cons:* If one coroutine executes a long CPU loop or synchronous blocking call, **it blocks the entire thread and all other coroutines**.

---

### Q8. What is the memory footprint and context-switch overhead of a coroutine vs an OS thread vs an OS process?

**Answer:**

| Dimension | Coroutine (`asyncio`) | OS Thread (`threading`) | OS Process (`multiprocessing`) |
| :--- | :--- | :--- | :--- |
| **Creation Overhead** | Extremely fast (microseconds) | Moderate (~millisecond) | Slow (~tens of milliseconds, forks process) |
| **Memory per Unit** | ~1 to 2 KB (Python generator frame) | ~8 KB to 8 MB (OS stack + Python thread state) | ~15 to 50+ MB (duplicate interpreter runtime) |
| **Context Switch Cost** | Nanoseconds (function pointer jump in user space) | Microseconds (kernel interrupt, CPU registers swapped) | Microseconds to Milliseconds (virtual memory TLB flushed, cache invalidated) |
| **Scale Limit on 1 Server** | 100,000+ concurrently | 1,000 to 5,000 threads | 10 to 100 processes (tied to CPU count/RAM) |

---

### Q9. Can multithreading achieve true parallelism in Python? Under what exact circumstances?

**Answer:**
**Yes**, multithreading in CPython can achieve true multi-core parallelism **if and only if the workload releases the GIL**.

**Concrete Examples:**
1. **NumPy & BLAS:** Matrix multiplications (`np.dot(a, b)`) release the GIL and leverage OpenMP/MKL to saturate all CPU cores.
2. **Image Processing (OpenCV / Pillow):** Heavy C-level image filtering algorithms release the GIL during kernel processing.
3. **Cryptography:** Hashing gigabytes of data with `hashlib.sha256()` or OpenSSL releases the GIL in C.
4. **Compression:** Zstandard (`zstd`) or `gzip` streaming compression implemented in C extensions.

If the work consists of evaluating pure Python objects (loops over Python lists, dict manipulations), threads **cannot** achieve parallelism due to the GIL.

---

### Q10. What are Subinterpreters (PEP 554 / PEP 684 per-interpreter GIL)?

**Answer:**
* **PEP 684 (Python 3.12+):** Allowed multiple Python interpreters to coexist within a single OS process, each having its **own isolated GIL**.
* **Key Advantages:**
  * Runs parallel Python code across OS threads without cross-thread GIL contention.
  * Uses much less memory than `multiprocessing` because dynamic shared libraries and process address spaces are shared.
* **Communication:** Interpreters do not share Python objects directly. They pass messages via high-performance shared memory channels (`interpreters.create_channel()`).

---

## Section 2: Asyncio Fundamentals, Event Loop & Coroutines

### Q11. What is a Coroutine, a Task, and a Future in `asyncio`? How are they related?

**Answer:**
* **Coroutine Function:** A function defined with `async def`.
* **Coroutine Object:** The object returned when calling a coroutine function. It does not execute immediately; it is scheduled or awaited.
* **Future (`asyncio.Future`):** A low-level object representing an eventual result of an asynchronous operation (similar to a Promise in JavaScript). It tracks execution state: `PENDING`, `CANCELLED`, or `FINISHED`.
* **Task (`asyncio.Task`):** A concrete subclass of `Future` that wraps a coroutine object and schedules it to run on the event loop. Tasks enable concurrent execution:

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return {"status": 200}

async def main():
    # 1. Coroutine object (NOT yet scheduled):
    coro = fetch_data()

    # 2. Task (Immediately scheduled to run on event loop):
    task = asyncio.create_task(coro)

    # 3. Awaiting the task retrieves the Future's result:
    result = await task
    print(result)

asyncio.run(main())
```

---

### Q12. How does the Python Event Loop work internally? What are selectors (`epoll`, `kqueue`) and the ready queue?

**Answer:**
* **Core Architecture:** The event loop is a single-threaded loop running an OS-level I/O multiplexer:
  * Linux: `epoll`
  * macOS/BSD: `kqueue`
  * Windows: `IOCP` (I/O Completion Ports)
* **Execution Cycle:**
  1. **Ready Queue:** The loop checks its FIFO queue of tasks ready to run immediately. It executes each task until it reaches an `await` suspension point.
  2. **Timer Heap:** The loop checks a min-heap of scheduled timer callbacks (`asyncio.sleep()`).
  3. **I/O Polling:** The loop invokes `selector.select(timeout)` to ask the OS kernel which network sockets have incoming bytes or are ready for writing.
  4. **Resume Coroutines:** The loop wakes up the coroutines associated with the active file descriptors and places them back into the ready queue.

---

### Q13. What is the difference between `async def` and a generator-based coroutine (`@asyncio.coroutine`)?

**Answer:**
* **Generator-based Coroutines (Python 3.4, deprecated in 3.8, removed in 3.11):** Used the `@asyncio.coroutine` decorator on generator functions with `yield from`.
* **Native Coroutines (Python 3.5+ PEP 492):** Defined using explicit `async def` and `await` syntax.
* **Key Differences:**
  1. Native coroutines have distinct internal flags (`CO_COROUTINE`), making them recognizable by introspection (`inspect.iscoroutine()`).
  2. You cannot accidentally iterate over a native coroutine with a regular `for` loop.
  3. Native coroutines enable asynchronous context managers (`async with`) and asynchronous iterators (`async for`).

---

### Q14. What happens when you call a coroutine function without `await`? What is the `"coroutine was never awaited"` runtime warning?

**Answer:**
Calling an `async def` function returns a **coroutine object** without executing the function's internal body:

```python
async def send_email():
    print("Email sent!")

def main():
    # Calling the coroutine function creates the object, but doesn't run it:
    res = send_email()
    # Output: RuntimeWarning: coroutine 'send_email' was never awaited
```

* **Why the warning occurs:** When CPython's garbage collector collects a coroutine object whose execution frame never reached completion or was never scheduled on an event loop, its destructor (`__del__`) logs `RuntimeWarning: coroutine was never awaited`.
* **Fix:** Either `await send_email()` inside an async function or schedule it via `asyncio.create_task(send_email())`.

---

### Q15. What is `asyncio.run()`? Why shouldn't you call `asyncio.run()` inside an already running event loop?

**Answer:**
* **`asyncio.run(coro)` (Python 3.7+):** The standard high-level entrypoint for async applications. It:
  1. Creates a brand-new event loop.
  2. Runs the passed coroutine until it finishes.
  3. Cancels all remaining pending tasks.
  4. Shuts down asynchronous generators.
  5. Closes the event loop cleanly.
* **Why calling it inside an active loop raises `RuntimeError: This event loop is already running`:**
  The CPython event loop is single-threaded and not re-entrant. If an active event loop is currently running and you call `asyncio.run()`, it attempts to start a second loop on the same thread, causing conflicting socket polling and frame corruption.
* **In nested environments (e.g., Jupyter Notebook, Celery, or FastAPI route):** Use `asyncio.create_task()` or `await` directly instead of `asyncio.run()`, or use `nest_asyncio` if working in interactive notebooks.

---

### Q16. Compare `asyncio.gather()`, `asyncio.wait()`, and `asyncio.as_completed()`.

**Answer:**

```python
import asyncio

async def worker(i, delay):
    await asyncio.sleep(delay)
    if i == 2:
        raise ValueError("Boom!")
    return f"Done {i}"
```

1. **`asyncio.gather(*aws, return_exceptions=False)`:**
   * Returns a list of results in the **exact order** the awaitables were submitted.
   * If `return_exceptions=True`, caught exceptions are returned as list elements instead of immediately aborting other tasks.
2. **`asyncio.wait(aws, return_when=ALL_COMPLETED)`:**
   * Takes a set of `Task` objects and returns a tuple of two sets: `(done, pending)`.
   * Configurable via `return_when`: `FIRST_COMPLETED`, `FIRST_EXCEPTION`, or `ALL_COMPLETED`.
   * Does NOT automatically cancel pending tasks if one fails.
3. **`asyncio.as_completed(aws)`:**
   * Returns an iterator of coroutines that yield results **as soon as each task finishes** (out of order). Useful for processing results as they stream in without waiting for the slowest task.

---

### Q17. What is Structured Concurrency in Python 3.11+ via `asyncio.TaskGroup`? Why is it preferred over `asyncio.gather()`?

**Answer:**
* **Structured Concurrency:** A paradigm ensuring that concurrent tasks spawned within a block have clear lifetime boundaries. Child tasks cannot outlive the scope that created them.
* **The Problem with `asyncio.gather()`:** If one task in `gather()` raises an exception, the other sibling tasks continue running in the background as abandoned "orphan" tasks, leaking sockets and memory.
* **`asyncio.TaskGroup` (Python 3.11+):**
  * Implemented as an async context manager.
  * If any task within the group raises an unhandled exception, **all other running sibling tasks in the group are immediately cancelled**.
  * The context manager waits for all tasks to terminate and re-raises exceptions packaged in an `ExceptionGroup`:

```python
import asyncio

async def fetch_api(endpoint):
    await asyncio.sleep(0.5)
    if endpoint == "bad":
        raise RuntimeError("Service unavailable")
    return {"endpoint": endpoint}

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(fetch_api("users"))
            t2 = tg.create_task(fetch_api("bad"))
            t3 = tg.create_task(fetch_api("orders"))
        # Only reaches here if ALL tasks succeeded:
        print(t1.result(), t3.result())
    except* RuntimeError as eg:  # Python 3.11+ except* syntax
        print(f"Handled error group: {eg.exceptions}")
```

---

### Q18. How does task cancellation work in `asyncio`? What is `asyncio.CancelledError`?

**Answer:**
* **How cancellation works:** Calling `task.cancel()` does not forcibly terminate thread execution. Instead, the event loop schedules an `asyncio.CancelledError` exception to be thrown inside the coroutine the next time it pauses at an `await` expression.
* **Catching `CancelledError`:**
  * In Python 3.8+, `asyncio.CancelledError` inherits from `BaseException` (not `Exception`) so standard `except Exception:` blocks do not inadvertently suppress cancellation.
  * If you intercept `CancelledError` for cleanup, you **must re-raise it** unless you intentionally want to ignore the cancellation request:

```python
async def worker():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Cleaning up database connections...")
        # Clean up resources
        raise  # MUST re-raise CancelledError!
```

---

### Q19. What is `asyncio.shield()`? When and why would you protect a coroutine from cancellation?

**Answer:**
* **What it is:** `asyncio.shield(awaitable)` wraps an awaitable in a protective shield so that if the outer calling task is cancelled, the inner coroutine **continues executing to completion**.
* **Use Case - Critical Atomic Actions:** In an e-commerce checkout, if a user closes their browser tab (cancelling the HTTP request task), you must ensure payment capture or inventory decrements complete:

```python
async def commit_transaction():
    # Critical write to database
    await asyncio.sleep(2)
    print("Transaction safely committed.")

async def handle_request():
    try:
        # If handle_request is cancelled, commit_transaction is shielded:
        await asyncio.shield(commit_transaction())
    except asyncio.CancelledError:
        print("Client disconnected, but transaction was shielded.")
```

---

### Q20. How do timeouts work in `asyncio`? Compare `asyncio.wait_for()` with `asyncio.timeout()` (Python 3.11+).

**Answer:**
* **`asyncio.wait_for(coro, timeout)` (Legacy):**
  * Wraps a single coroutine. If the timeout expires, it cancels the inner task and raises `asyncio.TimeoutError`.
  * *Downside:* In Python < 3.11, cancellation could be swallowed or delayed, leading to confusing exception handling.
* **`asyncio.timeout(delay)` (Python 3.11+):**
  * An asynchronous context manager.
  * Can wrap multiple `await` statements and tasks uniformly.
  * Cleaner exception flow using standard `TimeoutError`:

```python
import asyncio

async def fetch_data():
    async with asyncio.timeout(2.5):
        data = await make_http_call()
        await save_to_database(data)
```

---

### Q21. What are Asynchronous Iterators and Asynchronous Generators?

**Answer:**
* **Asynchronous Iterator Protocol:**
  * Must implement `__aiter__(self)` returning an async iterator.
  * Must implement `__anext__(self)` returning an awaitable that yields values or raises `StopAsyncIteration`.
* **Asynchronous Generator:** An `async def` function containing one or more `yield` statements:

```python
import asyncio

async def paginated_user_stream(total_pages: int):
    for page in range(1, total_pages + 1):
        await asyncio.sleep(0.1)  # Simulates network fetch
        yield [f"user_{page}_{i}" for i in range(3)]

async def consume():
    async for page_items in paginated_user_stream(3):
        print(f"Received batch: {page_items}")

asyncio.run(consume())
```

---

### Q22. What are Asynchronous Context Managers (`__aenter__`, `__aexit__`)?

**Answer:**
* Enable resource allocation and deterministic cleanup around asynchronous operations using `async with`.
* Must implement:
  * `async def __aenter__(self)`: Acquires connection, lock, or resource.
  * `async def __aexit__(self, exc_type, exc_val, exc_tb)`: Releases resource, even if an exception occurs.

```python
class AsyncDatabaseSession:
    async def __aenter__(self):
        print("Acquiring DB connection from pool...")
        await asyncio.sleep(0.05)
        self.conn = "CONNECTED"
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Returning connection back to pool...")
        await asyncio.sleep(0.02)
        return False  # Propagate exceptions if any
```

---

## Section 3: Asyncio Synchronization, Networking & Advanced Patterns

### Q23. Detail `asyncio.Lock`, `asyncio.Semaphore`, and `asyncio.BoundedSemaphore`.

**Answer:**
* **`asyncio.Lock`:** Guarantees mutual exclusion among coroutines on a single event loop. Only one coroutine can hold the lock at any time.
* **`asyncio.Semaphore(value)`:** Maintains an internal counter decremented by `acquire()` and incremented by `release()`. Allows up to `value` concurrent coroutines.
* **`asyncio.BoundedSemaphore(value)`:** Same as `Semaphore`, but raises a `ValueError` if `release()` is called more times than its initial `value` (preventing developer release bugs).

```python
# Limit concurrent outgoing API calls to 10:
API_LIMITER = asyncio.Semaphore(10)

async def call_external_api(url):
    async with API_LIMITER:
        # Max 10 coroutines can execute this block concurrently
        return await http_client.get(url)
```

---

### Q24. How do `asyncio.Event` and `asyncio.Condition` differ?

**Answer:**
* **`asyncio.Event`:**
  * Manages a single internal boolean flag (`set()`, `clear()`, `is_set()`).
  * Coroutines call `await event.wait()` to pause until the flag becomes `True`.
  * Ideal for **one-to-many broadcast notifications** (e.g., notifying all worker tasks that cache warmup has completed).
* **`asyncio.Condition`:**
  * Combines an `asyncio.Lock` with an event predicate.
  * Coroutines acquire the condition lock, then wait (`await cond.wait()`) until another task mutates state and calls `cond.notify(n)` or `cond.notify_all()`.
  * Ideal for stateful coordination (e.g., waiting for an in-memory batch buffer to reach 100 items).

---

### Q25. Explain `asyncio.Queue` and how `put()`, `get()`, and `join()` implement backpressure.

**Answer:**
* **Backpressure:** Preventing fast producers from overwhelming slow consumers and exhausting system memory.
* By setting `maxsize` on `asyncio.Queue(maxsize=100)`, calling `await queue.put(item)` **suspends the producer** once the queue is full until consumers call `queue.get()`.
* **`queue.task_done()`:** Called by a consumer to signal that an item has been fully processed.
* **`await queue.join()`:** Blocks until every item added to the queue has received a corresponding `task_done()`.

```python
import asyncio

async def consumer(q: asyncio.Queue):
    while True:
        item = await q.get()
        print(f"Consumed: {item}")
        await asyncio.sleep(0.1)
        q.task_done()

async def main():
    q = asyncio.Queue(maxsize=5)  # Backpressure ceiling
    c_task = asyncio.create_task(consumer(q))

    for i in range(10):
        await q.put(i)  # Suspends if queue holds 5 items

    await q.join()
    c_task.cancel()
```

---

### Q26. What is `contextvars` (PEP 567) and why is it essential for request-scoped context in `asyncio` instead of `threading.local`?

**Answer:**
* **The Failure of `threading.local()` in `asyncio`:**
  `threading.local()` stores data isolated per **OS thread**. In an `asyncio` server, thousands of concurrent requests run on **the same OS thread**. If Request A writes `threading.local().user_id = 123`, Request B running concurrently on that same thread reads or overwrites Request A's data, causing catastrophic data corruption and security leaks.
* **`contextvars.ContextVar`:**
  Provides context-local storage that understands coroutine and task boundaries. When a new task is spawned (`asyncio.create_task`), it receives a shallow copy of the parent context. Changes made inside that task branch do not affect parent or sibling tasks.

---

### Q27. Why should you never execute synchronous blocking calls (e.g., `time.sleep`, `requests.get`, `open()`) inside an async event loop?

**Answer:**
* Because `asyncio` operates on a **single thread via cooperative scheduling**.
* The event loop can only switch tasks when a coroutine yields control via `await`.
* If a coroutine executes a synchronous blocking call like `time.sleep(5)` or `requests.get(...)`:
  1. The single OS thread halts inside that function.
  2. The event loop cannot run its selector loop.
  3. All other concurrent tasks, WebSocket heartbeats, and health-check probes freeze for 5 full seconds.

---

### Q28. How do you run blocking/synchronous code in `asyncio` without blocking the event loop?

**Answer:**
Offload the blocking synchronous work to a background worker thread via a thread pool:

1. **`asyncio.to_thread` (Python 3.9+ - Preferred):**
   ```python
   import asyncio
   import time

   def blocking_disk_io(path: str) -> str:
       time.sleep(2)  # Simulates blocking I/O
       return f"Data from {path}"

   async def main():
       # Runs blocking_disk_io on a separate thread from default ThreadPoolExecutor:
       result = await asyncio.to_thread(blocking_disk_io, "/tmp/large.bin")
       print(result)
   ```
2. **`loop.run_in_executor` (For custom executors or process pools):**
   ```python
   loop = asyncio.get_running_loop()
   result = await loop.run_in_executor(custom_executor, blocking_fn, arg1)
   ```

---

### Q29. How do you handle asynchronous file I/O? Why is standard `open()` blocking, and how does `aiofiles` work?

**Answer:**
* **Why `open()` is blocking:** Most operating systems (POSIX/Linux) do not have universal non-blocking file descriptor interfaces for local disk files in the same way they do for network sockets (`epoll` does not support regular disk files). Reading from disk puts the OS thread into an uninterruptible sleep state waiting for disk I/O.
* **How `aiofiles` works:** It offloads synchronous `read`/`write` filesystem system calls to an underlying thread pool (`ThreadPoolExecutor`), presenting an `async with` and `await` interface to the event loop.

```python
import aiofiles

async def read_file_async(path: str) -> str:
    async with aiofiles.open(path, mode='r') as f:
        return await f.read()
```

---

### Q30. What is `uvloop`? How does it differ from standard `asyncio` and why is it faster?

**Answer:**
* **What it is:** A drop-in replacement for the default CPython event loop, written in Cython on top of **`libuv`** (the high-performance C library powering Node.js).
* **Why it is faster:**
  1. Implemented in optimized C rather than pure Python.
  2. Direct interaction with low-level kernel system calls with zero Python object wrapping.
  3. Highly optimized memory buffer allocations.
* **Performance:** Typically makes `asyncio` networking 2x to 4x faster.
* **Usage:**
  ```python
  import uvloop
  uvloop.install()  # Must be called before asyncio.run()
  ```

---

### Q31. How do you handle signals (`SIGINT`, `SIGTERM`) and implement graceful shutdown in an `asyncio` application?

**Answer:**

```python
import asyncio
import signal

async def worker():
    while True:
        await asyncio.sleep(1)

def shutdown_handler(sig, loop, stop_event):
    print(f"Received shutdown signal {sig.name}...")
    stop_event.set()

async def main():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown_handler, sig, loop, stop_event)

    task = asyncio.create_task(worker())
    await stop_event.wait()

    print("Draining active tasks...")
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    print("Clean shutdown complete.")

asyncio.run(main())
```

---

### Q32. What is event loop lag, and how can you monitor or detect blocked event loops in production?

**Answer:**
* **Event Loop Lag:** The time difference between when a task was scheduled to run on the event loop and when it actually began execution.
* If a coroutine was scheduled with `loop.call_later(0.1, cb)`, but executes after 0.6 seconds, the event loop experienced **500ms of lag**, indicating a blocking synchronous call starved the loop.
* **Detection:**
  1. **Built-in Debug Mode:** `asyncio.run(main(), debug=True)` or `PYTHONASYNCIODEBUG=1`. Warns when any task execution exceeds `loop.slow_callback_duration` (default 100ms).
  2. **Heartbeat Metric:** Run an async background task that sleeps for 1 second and computes `lag = actual_time - expected_time`, emitting the metric to StatsD or Prometheus.

---

### Q33. How does `asyncio.subprocess` work, and how can you stream stdout/stderr asynchronously?

**Answer:**

```python
import asyncio

async def run_shell_command(cmd: str):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Stream stdout line-by-line as it produces output:
    async for line in process.stdout:
        print(f"[STDOUT]: {line.decode().strip()}")

    await process.wait()
    print(f"Process exited with code: {process.returncode}")
```

---

## Section 4: Multithreading & Thread Synchronization

### Q34. How do you create and manage threads in Python? Compare passing a target vs subclassing `threading.Thread`.

**Answer:**

1. **Passing a `target` callable (Recommended for most tasks):**
   ```python
   import threading

   def worker(name: str):
       print(f"Hello from {name}")

   t = threading.Thread(target=worker, args=("worker-1",))
   t.start()
   t.join()  # Wait for thread to terminate
   ```

2. **Subclassing `threading.Thread` (Recommended for complex, stateful workers):**
   ```python
   class DataIngestionThread(threading.Thread):
       def __init__(self, queue):
           super().__init__()
           self.queue = queue
           self._stop_event = threading.Event()

       def run(self):
           while not self._stop_event.is_set():
               # Custom polling/processing loop
               pass

       def stop(self):
           self._stop_event.set()
   ```

---

### Q35. What is a daemon thread (`daemon=True`)? What happens to daemon threads when the main program exits?

**Answer:**
* **Daemon Thread:** A background service thread. Python exits when only daemon threads remain alive.
* **Behavior upon exit:**
  * When all non-daemon threads finish, the Python interpreter terminates immediately.
  * **Daemon threads are killed abruptly mid-execution!**
  * Their `finally` blocks do **not** run, open file buffers are not flushed, and database connections are abandoned without cleanup.
* **Rule:** Never use daemon threads for tasks that perform critical writes to disk or databases.

---

### Q36. What is a Race Condition? Provide a code example demonstrating a race condition in Python threads.

**Answer:**
A race condition occurs when multiple threads concurrently read and write shared mutable state without synchronization, producing results dependent on thread execution timing:

```python
import threading

counter = 0

def increment():
    global counter
    for _ in range(100_000):
        # Non-atomic operation (read, add, write)
        counter += 1

threads = [threading.Thread(target=increment) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

print(f"Expected: 500,000 | Actual: {counter}")  # Actual is almost always < 500,000!
```

---

### Q37. Explain `threading.Lock` vs `threading.RLock` (Reentrant Lock). When is `RLock` necessary?

**Answer:**
* **`threading.Lock`:** A standard mutual exclusion lock. If a thread attempts to acquire a lock it **already holds**, it deadlocks with itself:
  ```python
  lock = threading.Lock()
  lock.acquire()
  lock.acquire()  # DEADLOCK! Thread hangs forever waiting for itself to release.
  ```
* **`threading.RLock` (Reentrant Lock):** Tracks the owning thread and a recursion level counter. The owning thread can acquire the lock multiple times without deadlocking. It must release it an equal number of times for other threads to acquire it:
  ```python
  rlock = threading.RLock()

  def outer():
      with rlock:
          inner()

  def inner():
      with rlock:  # Safe! Same thread can re-enter.
          print("Inside critical section")
  ```
* **When `RLock` is necessary:** In recursive algorithms or class methods where public methods call other public methods of the same class that both require synchronization.

---

### Q38. What is a Deadlock? What are the 4 Coffman conditions, and how can deadlocks be prevented in Python?

**Answer:**
* **Deadlock:** A condition where two or more threads are permanently blocked, each waiting for a lock held by the other.
* **The 4 Coffman Conditions (All 4 must hold for deadlock to occur):**
  1. **Mutual Exclusion:** Resources cannot be shared simultaneously.
  2. **Hold and Wait:** A thread holds one resource while waiting to acquire another.
  3. **No Preemption:** Resources cannot be forcibly taken from a thread holding them.
  4. **Circular Wait:** Thread A waits for Lock 2 held by Thread B; Thread B waits for Lock 1 held by Thread A.
* **Prevention Strategies:**
  1. **Lock Ordering:** Always acquire locks in a strict, globally consistent hierarchical order (e.g., acquire Lock 1 before Lock 2).
  2. **Lock Timeouts:** Never call unbounded `.acquire()`. Use `lock.acquire(timeout=5.0)` and handle failure.

---

### Q39. What is `threading.Semaphore` vs `threading.BoundedSemaphore`?

**Answer:**
* **`threading.Semaphore(value)`:** Manages an atomic integer counter.
  * `acquire()` decrements the counter. If counter is 0, it blocks.
  * `release()` increments the counter.
* **The Danger with standard `Semaphore`:** If buggy code calls `release()` more times than `acquire()`, the counter increases beyond its original capacity, violating concurrency limits.
* **`threading.BoundedSemaphore(value)`:** Checks whether the counter exceeds `value` on `release()`. If so, it raises a `ValueError`. Always prefer `BoundedSemaphore` in production code.

---

### Q40. How do `threading.Event` and `threading.Condition` work for thread-to-thread communication?

**Answer:**
* **`threading.Event`:** A thread-safe boolean flag.
  * Worker threads call `event.wait()`.
  * The coordinating thread calls `event.set()` to unblock all waiting threads, or `event.clear()` to reset.
* **`threading.Condition(lock)`:** Coordinates complex state-dependent actions:
  * Threads call `cond.wait()` which atomically releases the lock and blocks until signaled.
  * Mutating threads call `cond.notify()` (wakes one waiting thread) or `cond.notify_all()` (wakes all waiting threads).

---

### Q41. What is `threading.Barrier` and when is it used in concurrent workflows?

**Answer:**
* **`threading.Barrier(parties)`:** A synchronization primitive that blocks a fixed number of threads (`parties`) until all threads reach the barrier point:

```python
import threading

barrier = threading.Barrier(3)

def worker(i):
    print(f"Worker {i} doing phase 1 setup...")
    barrier.wait()  # Waits until all 3 threads call wait()
    print(f"Worker {i} starting phase 2 in sync!")

for i in range(3):
    threading.Thread(target=worker, args=(i,)).start()
```

---

### Q42. Explain `queue.Queue` in `threading`. Why is it thread-safe, and how do `task_done()` and `join()` coordinate producer-consumer flows?

**Answer:**
* **`queue.Queue`:** A multi-producer, multi-consumer FIFO queue.
* **Why it is thread-safe:** Its internal state is guarded by a `threading.Condition` and lock around standard deque operations.
* **`task_done()` and `join()` Mechanics:**
  1. Producer adds items: `q.put(item)`. Queue increments unfinished task counter.
  2. Consumer fetches item: `item = q.get()`.
  3. Consumer finishes processing item: calls `q.task_done()`. Queue decrements unfinished task counter.
  4. Producer waits for completion: `q.join()`. Blocks until unfinished task counter hits zero.

---

### Q43. What is `threading.local()`? How does it work and what are its memory leak gotchas in thread pools?

**Answer:**
* **What it is:** Creates an object whose attributes are distinct and private to each thread:
  ```python
  import threading
  my_data = threading.local()
  my_data.transaction_id = 901  # Unique to current thread
  ```
* **Memory Leak Trap in Thread Pools:**
  In a `ThreadPoolExecutor`, threads **do not terminate** after finishing a task; they are reused for subsequent tasks. If you attach large objects to `threading.local()` and do not clean them up (`del my_data.val`), that memory persists indefinitely on the thread, leaking RAM across requests.

---

### Q44. How does `concurrent.futures.ThreadPoolExecutor` work? Compare `submit()` + `as_completed()` vs `map()`.

**Answer:**
* **`executor.submit(fn, *args)`:** Submits a callable and returns a `Future` object immediately. Allows granular tracking, exception handling, and cancellation before execution.
* **`as_completed(futures)`:** Takes an iterable of `Future` objects and yields them **as soon as each finishes** (out-of-order).
* **`executor.map(fn, *iterables)`:** Similar to built-in `map()`. Returns results **strictly in the order** of the input iterable. If item 1 takes 10 seconds and item 2 takes 1 millisecond, `executor.map()` blocks until item 1 is ready.

---

## Section 5: Multiprocessing & Inter-Process Communication (IPC)

### Q45. How does `multiprocessing` bypass the GIL in Python? What are the trade-offs in memory and serialization?

**Answer:**
* **How it bypasses the GIL:** Rather than creating lightweight threads inside the same Python process, `multiprocessing` spawns distinct operating system processes. Each process runs its **own independent CPython runtime, heap, and GIL**.
* **Trade-Offs:**
  1. **Memory Overhead:** Spawning 16 worker processes duplicates the CPython runtime, loaded modules, and object overhead in each process.
  2. **Serialization (Pickling) Cost:** Objects cannot be shared via direct memory pointers. Every object sent to or returned from a child process must be serialized into bytes (`pickle`), transferred through an IPC pipe/socket, and deserialized in the other process.

---

### Q46. Explain the process start methods: `fork`, `spawn`, and `forkserver`. Why is `fork` dangerous in multi-threaded programs?

**Answer:**
1. **`fork` (Legacy Linux default):** Clones the parent process using the OS `fork()` syscall.
   * *Danger:* `fork()` copies the calling thread, but **does not copy other threads from the parent process**. If another thread in the parent process was holding a lock (e.g., inside an allocator, logging handler, or DB pool) at the moment of `fork`, that lock is copied into the child process in a **permanently locked state**. The child process deadlocks the instant it touches that resource.
2. **`spawn` (Default on Windows, macOS, and Python 3.14+ Linux):** Starts a fresh Python interpreter process. Inherits only necessary file descriptors. Completely safe from parent thread locks, but slower startup.
3. **`forkserver`:** A clean single-threaded server process is started at boot. Whenever a new process is needed, the server forks it, avoiding parent multi-threaded lock inheritance bugs while retaining fast startup.

---

### Q47. What is object pickling (`pickle`), and why must all data passed to `multiprocessing` workers be pickleable?

**Answer:**
* Because processes have **isolated memory spaces**. Process A cannot point to a memory address in Process B.
* To pass function arguments and return values across process boundaries, Python serializes objects into byte streams using `pickle`.
* **Objects that CANNOT be pickled:**
  * Open file handles, database connections, and network sockets.
  * Lambdas and dynamically generated functions.
  * Thread locks, generator objects, and complex closures.

---

### Q48. What IPC mechanisms does `multiprocessing` provide? Compare `Queue`, `Pipe`, `Value`, and `Array`.

**Answer:**
* **`multiprocessing.Queue`:** A multi-producer, multi-consumer queue built on top of an OS pipe, a background feeder thread, and locks. Automatically pickles and unpickles objects.
* **`multiprocessing.Pipe(duplex=True)`:** A direct point-to-point communication channel between two processes. Faster than `Queue` for dedicated pair communication.
* **`multiprocessing.Value` and `Array`:** Shared memory backed by C-level primitive types (e.g., integers, doubles) that reside in shared memory segments without pickle overhead. Guarded by an internal process lock.

---

### Q49. What is `multiprocessing.shared_memory` (Python 3.8+)? How does zero-copy shared memory work between processes?

**Answer:**
* **`shared_memory.SharedMemory`:** Allocates a raw POSIX/Windows shared memory block accessible across unrelated Python processes by name.
* **Zero-Copy Performance:** Allows wrapping the shared memory buffer directly in a `memoryview` or NumPy array:

```python
from multiprocessing import shared_memory
import numpy as np

# In Parent Process:
a = np.array([1, 2, 3, 4, 5], dtype=np.int64)
shm = shared_memory.SharedMemory(create=True, size=a.nbytes, name="shared_array")
shared_arr = np.ndarray(a.shape, dtype=a.dtype, buffer=shm.buf)
shared_arr[:] = a[:]  # Copy data once into shared memory

# In Child Process (Zero-Copy Read):
existing_shm = shared_memory.SharedMemory(name="shared_array")
child_arr = np.ndarray((5,), dtype=np.int64, buffer=existing_shm.buf)
print(child_arr[0])  # Reads directly from RAM without pickling!
```

---

### Q50. Compare `multiprocessing.Pool` and `concurrent.futures.ProcessPoolExecutor`.

**Answer:**
* **`multiprocessing.Pool` (Older API):**
  * Provides specialized batch methods: `apply()`, `apply_async()`, `map()`, `map_async()`, `imap()`, `imap_unordered()`.
  * Supports `chunksize` tuning directly.
* **`concurrent.futures.ProcessPoolExecutor` (Modern API):**
  * Conforms to the standard `Executor` interface (`submit()`, `map()`).
  * Returns `Future` objects compatible with modern asynchronous tools.
  * Better integrated with `asyncio` via `loop.run_in_executor()`.

---

### Q51. What is `multiprocessing.Manager`? How do server-managed proxy objects work, and what is their performance overhead?

**Answer:**
* **`multiprocessing.Manager()`:** Starts a dedicated background standalone server process.
* **How it works:** Shared objects (like `manager.dict()` or `manager.list()`) live entirely in the manager process. Other processes receive **proxy objects**.
* When a child process accesses `proxy_dict["key"] = val`, the proxy serializes the operation over an IPC socket to the manager server process.
* **Overhead:** **Very slow** compared to raw shared memory because every single read/write triggers IPC network/socket round-trips and serialization.

---

### Q52. What happens if a child process in a `ProcessPoolExecutor` terminates abruptly (e.g. OOM killed)? What is `BrokenProcessPool`?

**Answer:**
* If a worker process in a `ProcessPoolExecutor` is terminated by an external signal (e.g., Linux `SIGKILL` or kernel OOMKiller), it dies without sending an exception back over the pipe.
* The executor's management thread detects that the IPC channel closed unexpectedly.
* It transitions the pool into a broken state and raises **`concurrent.futures.process.BrokenProcessPool: A process in the process pool was terminated abruptly`**.
* All currently pending and future tasks submitted to that executor immediately fail.

---

### Q53. Why must `if __name__ == '__main__':` always guard process creation in Python, particularly with `spawn`?

**Answer:**
* Under the **`spawn`** start method (standard on Windows and macOS), a newly spawned child process starts by launching a fresh Python interpreter and **re-importing the main script from top to bottom**.
* If the code that creates new processes is not guarded by `if __name__ == '__main__':`, the re-imported script in the child process will execute the creation code again, spawning infinite child processes in an explosive fork bomb that crashes the operating system.

---

## Section 6: Production Architectures, Hybrid Patterns & Scenarios

### Q54. Scenario: Parallelizing a CPU-intensive data transformation pipeline that feeds into an async HTTP API. How do you combine `asyncio` with `ProcessPoolExecutor`?

**Answer:**
```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
import hashlib

def heavy_cpu_hashing(payload: str) -> str:
    # Pure CPU calculation - runs on separate core bypassing GIL
    for _ in range(500_000):
        payload = hashlib.sha256(payload.encode()).hexdigest()
    return payload

async def handle_api_request(executor: ProcessPoolExecutor, data: str):
    loop = asyncio.get_running_loop()
    # Offload CPU work to multi-core process pool without blocking event loop:
    result = await loop.run_in_executor(executor, heavy_cpu_hashing, data)
    return {"hash": result}

async def main():
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = await asyncio.gather(
            handle_api_request(executor, "payload_1"),
            handle_api_request(executor, "payload_2"),
            handle_api_request(executor, "payload_3")
        )
        print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Q55. Scenario: Fixing a database connection pool crash or deadlock when child processes are created via `fork`. Why can't connection pools be shared across processes?

**Answer:**
* **Root Cause:** A database connection pool wraps underlying OS network sockets and thread locks. When a process forks:
  1. The child process inherits the **exact same file descriptor numbers**.
  2. If both parent and child write or read from the same socket file descriptor concurrently, database packets interleave, causing TLS decryption failures and protocol desynchronization.
* **Architectural Fix:**
  Never initialize the connection pool in the parent process before forking. Either:
  1. Use the `spawn` start method (`multiprocessing.set_start_method("spawn")`).
  2. Call `pool.dispose()` or initialize the connection pool lazily inside the worker process's initializer function (`initializer=init_db_worker`).

---

### Q56. Scenario: Building a robust async worker with backpressure and bounded queues that drains gracefully upon receiving `SIGTERM`.

**Answer:**
```python
import asyncio
import signal

class GracefulQueueWorker:
    def __init__(self, maxsize: int = 100):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.shutdown_event = asyncio.Event()

    async def producer(self):
        item_id = 0
        while not self.shutdown_event.is_set():
            item_id += 1
            # Backpressure: Suspends when queue reaches maxsize
            await self.queue.put(f"item_{item_id}")
            await asyncio.sleep(0.01)

    async def consumer(self, worker_id: int):
        while True:
            try:
                # Wait for items with a short timeout to check shutdown flag
                item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await asyncio.sleep(0.05)  # Process work
                self.queue.task_done()
            except asyncio.TimeoutError:
                if self.shutdown_event.is_set() and self.queue.empty():
                    print(f"Worker {worker_id} exiting cleanly.")
                    break

    async def run(self):
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.shutdown_event.set)

        consumers = [asyncio.create_task(self.consumer(i)) for i in range(3)]
        p_task = asyncio.create_task(self.producer())

        await self.shutdown_event.wait()
        print("Shutdown triggered: Waiting for queue to drain...")
        p_task.cancel()
        await self.queue.join()  # Wait until all items are acknowledged
        await asyncio.gather(*consumers)
        print("All work drained. Clean exit.")
```

---

### Q57. Scenario: Implementing an async rate limiter with a sliding window token bucket across concurrent coroutines.

**Answer:**
```python
import asyncio
import time

class AsyncTokenBucket:
    def __init__(self, rate_per_second: float, capacity: int):
        self.rate = rate_per_second
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        async with self.lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # Wait until enough tokens regenerate
                deficit = tokens - self.tokens
                wait_time = deficit / self.rate
                await asyncio.sleep(wait_time)
```

---

### Q58. Scenario: Thread-safe dynamic Singleton / Connection Manager using double-checked locking in Python.

**Answer:**
```python
import threading

class DatabaseConnectionPool:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # 1. First check without acquiring lock (fast path)
        if cls._instance is None:
            with cls._lock:
                # 2. Second check inside synchronized block
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, dsn: str):
        if self._initialized:
            return
        with self._lock:
            if not self._initialized:
                self.dsn = dsn
                self._initialized = True
```

---

### Q59. Scenario: Diagnosing a memory leak in a long-running Celery worker or multithreaded daemon service.

**Answer:**
* **Diagnosis Procedure:**
  1. **Identify whether the leak is on-heap or off-heap:**
     * Compare process RSS memory (`ps aux`) with Python heap size via `tracemalloc`.
     * If `tracemalloc` tracks growing object counts, it is an on-heap Python leak (e.g., global lists, un-evicted LRU caches, cyclic references with custom `__del__`).
     * If `tracemalloc` is flat but RSS memory expands, it is an off-heap native leak (e.g., C library, `glibc malloc` fragmentation).
  2. **Snapshot Heap with `tracemalloc`:**
     ```python
     import tracemalloc
     tracemalloc.start()
     snap1 = tracemalloc.take_snapshot()
     # ... run 10,000 tasks ...
     snap2 = tracemalloc.take_snapshot()
     top_stats = snap2.compare_to(snap1, 'lineno')
     for stat in top_stats[:10]:
         print(stat)
     ```
  3. **Mitigation:**
     * In Celery: Set `--max-tasks-per-child=1000` to periodically recycle worker processes, releasing fragmented pages back to the OS.
     * Switch Linux memory allocator from `glibc` to `jemalloc` (`LD_PRELOAD=/usr/lib/.../libjemalloc.so`).

---

### Q60. Scenario: How to test concurrent and asynchronous code effectively with `pytest`, `pytest-asyncio`, and mock thread pools.

**Answer:**
```python
import pytest
import asyncio
from unittest.mock import AsyncMock

async def fetch_user_data(client, user_id: int):
    response = await client.get(f"/api/users/{user_id}")
    return await response.json()

# Testing coroutines using pytest-asyncio:
@pytest.mark.asyncio
async def test_fetch_user_data():
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.json.return_value = {"id": 101, "name": "Alice"}
    mock_client.get.return_value = mock_response

    result = await fetch_user_data(mock_client, user_id=101)
    assert result == {"id": 101, "name": "Alice"}
    mock_client.get.assert_called_once_with("/api/users/101")

# Testing race conditions and concurrency with deterministic locks:
@pytest.mark.asyncio
async def test_concurrent_access():
    lock = asyncio.Lock()
    counter = 0

    async def increment():
        nonlocal counter
        async with lock:
            temp = counter
            await asyncio.sleep(0.001)  # Force yield
            counter = temp + 1

    await asyncio.gather(*(increment() for _ in range(50)))
    assert counter == 50
```
