#### Q.1 what is the difference between soap and rest API?
Answer:
- SOAP is a protocol, whereas REST is an architectural style.
- SOAP usually uses XML, has strict standards, and supports WS-Security, transactions, and reliability.
- REST uses HTTP methods like GET, POST, PUT, DELETE and commonly works with JSON. It is simpler, lighter, and easier to scale.
- In interviews, say: use SOAP for enterprise-grade, formal integrations; use REST for web and mobile APIs because it is faster and easier to implement.

#### Q.2 What is the difference between REST and gRPC?
Answer:
- REST is HTTP-based and usually uses JSON. It is human-readable, easy to test with browsers and curl, and good for public APIs.
- gRPC uses HTTP/2 and Protocol Buffers (protobuf), which makes it faster, strongly typed, and efficient for internal microservices.
- REST is more flexible and easy for clients to consume; gRPC is better for high-performance service-to-service communication and streaming.
- In short: choose REST for external APIs and gRPC for internal service communication.

#### Q.3 what is the difference between stateful and stateless?
Answer:
- Stateful systems remember client context across requests. Example: a session on the server stores login state or shopping cart data.
- Stateless systems do not store client context between requests. Every request contains all required information.
- Stateless APIs are easier to scale, load balance, and recover from failures because any server can handle any request.
- Stateful systems can be simpler for user experience but are harder to scale and maintain.

#### Q.4 What is the advantages and disadvantages of using index in database?
Answer:
- Advantages: faster SELECT queries, improved sorting, grouping, joins, and searching on large datasets; helps enforce uniqueness.
- Disadvantages: extra storage space; slows down INSERT, UPDATE, and DELETE because indexes must also be maintained; too many indexes can reduce performance.
- Best practice: create indexes only on columns frequently used in WHERE, ORDER BY, JOIN, and UNIQUE constraints.
- In interviews, mention that indexes trade write performance for read performance.

#### Q.5 What is the difference between Kafka and RabbitMQ?
Answer:
- Kafka is a distributed event streaming platform designed for high throughput, durability, and replaying events. It is commonly used for logs, analytics, event-driven systems, and data pipelines.
- RabbitMQ is a message broker focused on message queues and routing patterns like work queues, pub/sub, and task distribution.
- Kafka is better for large-scale event streams and data processing; RabbitMQ is better for traditional message-based systems and task queues.
- Interview answer: Kafka is designed for streaming data at scale, while RabbitMQ is designed for reliable message delivery and queue-based communication.

#### Q.6 What is the difference between hashing and encryption?
Answer:
- Hashing is a one-way process. It converts input into a fixed-size value, and it is not meant to be reversed. It is used for password storage and integrity checks.
- Encryption is a two-way process. Data is transformed so it can be reversed with the correct key. It is used to protect sensitive data in transit or at rest.
- Example: passwords should be stored as hashes, not as plain text; credit card or API data should be encrypted.
- In interviews, say: hashing is for verification, encryption is for confidentiality.

#### Q.7 What is encoding and encode?
Answer:
- Encoding is the process of converting data from one format to another so it can be stored, transmitted, or processed correctly.
- Encode means to perform that conversion. For example, converting a string to UTF-8 bytes or converting binary into Base64.
- Decode is the reverse process, where the encoded data is converted back to its original form.
- In short: encoding is the concept, and encode is the action of applying it to data.

#### Q.8 Why list comprehension is faster in python?
List comprehensions are faster in Python primarily because the interpreter optimizes them at the bytecode level. They avoid the overhead of repeatedly looking up and calling the **append**() method on each iteration, which significantly reduces the number of operations required to build a list.

Here are the main reasons list comprehensions execute faster than traditional for loops:

- **Bytecode optimization** The Python interpreter compiles list comprehensions into a single LIST\_APPEND instruction, eliminating the need to repeatedly load the append attribute and call it as a function.
- **Reduced function call overhead** Traditional for loops must suspend and resume a function's frame to call list.append() for every element, which is a slow process that list comprehensions bypass entirely.
- **Memory pre-allocation** List comprehensions allocate memory for the entire resulting list upfront whenever possible, preventing the performance hit of dynamically resizing the list as it grows.
- **C-level implementation** Because Python's underlying list operations are written in C, the internal execution engine handles the looping logic directly, minimizing explicit loop control statements.

**Q.9** If access token is expired but we still have refresh token to generate new access token but during the creation of new access token, API got high request rate and suddenly all the user got logged out of the system? How to prevent this this issue in python (take any web framework django, flask or fastapi)?

Answer:

To prevent users from being logged out due to race conditions during token refresh, you should implement a concurrency control mechanism like a distributed lock or a short grace period for the old refresh token. When multiple requests hit your API simultaneously with an expired access token, they all attempt to use the refresh token at once. If your system uses refresh token rotation (where a new refresh token is issued each time), the first request invalidates the old token, causing the subsequent concurrent requests to fail and log the user out. Using a Redis-based lock or allowing a brief overlap window for the old refresh token ensures that only one new token pair is generated and shared among the concurrent requests.

Here are the primary strategies to solve this issue in Python frameworks like Django, FastAPI, or Flask:

**1. IMPLEMENT A REFRESH TOKEN GRACE PERIOD**

If you are using Refresh Token Rotation (a security best practice where a new refresh token is issued on every use), you must account for race conditions. If two requests arrive at the exact same time, the second one will see the refresh token as "already used" and treat it as a potential theft, triggering a forced logout.

The Fix: Instead of immediately invalidating the old refresh token, mark it as "consumed" but allow it to be used for a short grace period (e.g., 5 to 10 seconds). If a subsequent request presents the same token within that window, return the newly generated access token instead of throwing an error.

**2. USE A DISTRIBUTED LOCK (E.G., REDIS)**

When multiple requests from the same client hit the server, you can use a lock to ensure only the first request performs the actual token refresh.

```python
import redis

from fastapi import HTTPException

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def refresh_access_token(refresh_token_value):

    lock_key = f"lock:refresh:{refresh_token_value}"

    

    # Acquire a lock for this specific refresh token

    with redis_client.lock(lock_key, timeout=5, blocking_timeout=2):

        # 1. Check if the token was already refreshed by another thread

        if is_token_already_refreshed(refresh_token_value):

            return get_cached_new_token(refresh_token_value)

            

        # 2. Perform the actual refresh logic

        new_token_pair = generate_new_tokens(refresh_token_value)

        

        # 3. Cache the new token briefly for concurrent requests

        cache_new_token(refresh_token_value, new_token_pair)

        

        return new_token_pair
```

**3. CLIENT-SIDE REQUEST DEDUPLICATION**

While backend fixes are critical, the most efficient way to handle this is to prevent the client from sending multiple refresh requests in the first place.

**The Fix:** Implement an interceptor on your frontend (using Axios, Fetch, etc.) that pauses all outgoing API calls when a 401 Unauthorized error is detected. The client should queue subsequent requests, wait for the single token refresh to complete, and then replay the queued requests with the new access token.

**4. IMPLEMENT EXPONENTIAL BACKOFF**

If your API is genuinely experiencing a high request rate (HTTP 429 Too Many Requests), your backend should return a `Retry-After` header. Your client-side code must respect this header and use exponential backoff before attempting to refresh the token again, rather than immediately failing and logging the user out.

Q.10 What is the difference between thread and process?

[https://www.codesy.tech/interview-prep/5-os-interview-questions-resources
](https://www.codesy.tech/interview-prep/5-os-interview-questions-resources)
