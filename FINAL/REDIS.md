For a backend engineer with **5 to 6 years of experience**, interviewers expect you to look past basic "key-value store" definitions. They want to see an understanding of **Redis internals, architecture trade-offs, concurrency models, data consistency, and production troubleshooting.**

Here are 20 interview questions tailored for your experience level, broken down by category, complete with concise, high-impact answers.

---

## Category 1: Core Internals & Data Structures

### 1. Redis is famously single-threaded, but it introduced multi-threading in version 6.0. Can you explain how this works and what problem it solves?

* **Answer:** Redis's core command execution engine remains **single-threaded**, which eliminates the need for CPU-expensive locks or context switching. However, as network bandwidth grew, the bottleneck shifted to network I/O (reading from and writing to sockets).
* In Redis 6.0+, **threaded I/O** was introduced. Main threads still execute commands sequentially, but background I/O threads handle parsing requests and formatting responses concurrently.

### 2. How do Redis Sorted Sets (ZSET) work under the hood?

* **Answer:** A `ZSET` uses a dual data structure: a **Hash Map** and a **Skip List**.
* The **Hash Map** maps members to scores, providing $O(1)$ lookup time to find a specific member's score.
* The **Skip List** maintains the members sorted by score, allowing $O(\log N)$ range queries, insertions, and deletions.
* For very small collections, Redis optimizes memory by using a compact **ziplist** or **listpack** instead.



### 3. When designing for memory efficiency, when would you use a Redis Hash vs. individual String keys?

* **Answer:** Individual string keys carry significant structural memory overhead (dict entries, Redis Object headers, expiry trackers). If you have millions of user profiles, storing them as individual strings (e.g., `user:100:name`) wastes gigabytes.
* Instead, grouping them into a **Hash** (e.g., key `users`, field `100:name`) is far more memory-efficient. Redis optimizes small hashes using `ziplist`/`listpack`, which uses tight, contiguous memory allocation.
* *Trade-off:* Sharding across multiple hashes is required if a single hash grows too large, as it cannot be split across cluster nodes.

### 4. What are HyperLogLogs, and what real-world backend problem do they solve?

* **Answer:** HyperLogLog (HLL) is a **probabilistic data structure** used to count unique elements (cardinality estimation) with an error rate of about 0.81%.
* Instead of storing millions of unique IDs (like user IDs for daily active users) in a Set, which takes megabytes or gigabytes of RAM, HLL uses a fixed maximum of **12 KB of memory** regardless of whether you count 100 or 10 billion items.

### 5. Explain Redis Streams. How do they compare to Pub/Sub?

* **Answer:**
* **Pub/Sub** is "fire-and-forget." If a subscriber is offline when a message is published, the message is permanently lost. It does not persist data.
* **Streams** are an append-only log data type (similar to Apache Kafka). Messages are **persisted** and can be replayed. Streams support **Consumer Groups**, allowing multiple workers to distribute the processing load safely, tracking which consumer has acknowledged which message.



---

## Category 2: Caching Patterns & Mitigation

### 6. What is a "Cache Stampede" (Thundering Herd), and how do you prevent it at scale?

* **Answer:** A cache stampede occurs when a highly popular cache key expires. Suddenly, thousands of concurrent backend threads find a cache miss and simultaneously hit the database to recalculate the same heavy query, frequently bringing the DB down.
* **Mitigation Strategies:**
1. **Mutex Locking:** Use a distributed lock (like Redlock) so only the first thread fetches from the DB; other threads wait or return a fallback.
2. **Probabilistic Early Expiration (XFetch):** Background workers recalculate and refresh the cache *before* it actually expires, based on a probability algorithm tied to read frequency.



### 7. Differentiate between Cache Penetration, Cache Avalanche, and Cache Breakdown.

* **Answer:**
* **Cache Penetration:** Requests hit keys that *never exist* in the DB (e.g., malicious IDs like `-999`). Fix: Cache empty/null results with short TTLs, or use a **Bloom Filter**.
* **Cache Breakdown:** A single *hot key* expires, causing a surge to the DB. Fix: Mutex locking or permanent keys updated via background cron.
* **Cache Avalanche:** *Masses of keys* expire at the exact same time, or the Redis cluster goes down completely. Fix: Add random jitter/noise to TTLs (e.g., `300s + rand(1,30)`), and implement circuit breakers.



### 8. What are the common cache invalidation strategies (Cache-aside vs. Write-through vs. Write-behind)?

* **Answer:**
* **Cache-Aside (Lazy Loading):** Application queries cache; on miss, reads DB, writes to cache. *Pros:* Resilient to cache failure. *Cons:* Can have stale data if DB updates bypass the cache.
* **Write-Through:** App writes to cache; cache immediately synchronously writes to DB. *Pros:* Clean data consistency. *Cons:* High write latency.
* **Write-Behind (Write-Back):** App writes to cache; cache queues the data to asynchronously write to DB later. *Pros:* Ultra-fast writes. *Cons:* Data loss risk if Redis crashes before DB sync.



---

## Category 3: Distributed Systems & Locking

### 9. How do you safely implement a Distributed Lock using Redis? What are the flaws of Redlock?

* **Answer:** For a single node, use `SET key value NX PX 30000` (where `value` is a unique random string per thread to ensure a worker only deletes its *own* lock via a Lua script).
* For multi-node, the **Redlock** algorithm acquires locks across $N/2 + 1$ independent master nodes.
* *Flaws:* Industry experts (like Martin Kleppmann) point out that Redlock relies heavily on synchronized system clocks. If a node suffers a sudden garbage collection pause or clock jump, the lock can be released prematurely, leading to race conditions.

### 10. How does Redis Cluster partition data? What happens when you scale it out?

* **Answer:** Redis Cluster does not use consistent hashing; it uses **Hash Slots**. There are exactly **16,384 hash slots**.
* Every key is hashed using `CRC16(key) % 16384` to determine its slot. When you scale out by adding a node, slots are migrated from existing nodes to the new node. This resharding happens online **without downtime**, though slots currently undergoing migration might require client redirection via `ASK` or `MOVED` errors.

### 11. What are "Hash Tags" in Redis Cluster, and why are they necessary?

* **Answer:** In Redis Cluster, multi-key operations (like transactions or `MGET`) are forbidden if the keys map to different hash slots (and thus different nodes).
* **Hash Tags** force specific keys into the *same* slot. By wrapping a portion of the key in curly braces, Redis will only hash that specific part. For example, `{user100}:profile` and `{user100}:orders` are guaranteed to sit on the exact same cluster node.

---

## Category 4: Persistence, High Availability & Replication

### 12. Compare RDB and AOF persistence mechanisms. When would you use which?

* **Answer:**
* **RDB (Redis Database):** Point-in-time compact snapshots saved at specified intervals. *Pros:* Extremely fast recovery; no performance impact on main thread (uses `fork()`). *Cons:* Data loss between snapshots.
* **AOF (Append Only File):** Logs every write command received. *Pros:* Minimal data loss (can sync every second). *Cons:* Files grow massive; slower recovery; slight write performance impact.


* **Production Standard:** Use **both**. RDB for disaster recovery backups, AOF for minimizing data loss.

### 13. How does the `fork()` operation used in RDB snapshotting avoid running out of memory?

* **Answer:** When Redis triggers RDB, it creates a child process via the Linux `fork()` system call. This leverages the OS **Copy-on-Write (CoW)** mechanism.
* The child process shares the exact same memory pages as the parent master process. Memory is only duplicated *if* the parent process receives a write command and modifies a page.
* > **Warning:** If your Redis instance has a high write volume during an RDB snapshot, CoW can cause memory usage to spike up to double, potentially triggering the OS Out-Of-Memory (OOM) killer.



### 14. What is the difference between Full Synchronization and Partial Synchronization (PSYNC) in replication?

* **Answer:**
* **Full Sync:** Occurs when a replica connects for the first time or loses track. The master creates an RDB snapshot file, sends it over the wire to the replica, which clears its old data and loads the RDB.
* **Partial Sync (PSYNC):** Occurs after a brief network disconnection. The master maintains an in-memory replication backlog buffer. If the replica reconnects and its replication offset is still inside this buffer, the master only sends the missing delta commands, avoiding an expensive RDB generation.



---

## Category 5: Memory Management & Eviction

### 15. What happens when Redis reaches its `maxmemory` limit? Explain Volatile-LRU vs Allkeys-LRU.

* **Answer:** Redis will invoke its configured `maxmemory-policy`. If set to `noeviction`, it returns out-of-memory errors for write commands.
* Otherwise, it evicts keys:
* `volatile-lru`: Evicts the Least Recently Used keys, but *only* from the pool of keys that have an explicit TTL expiration set.
* `allkeys-lru`: Evicts Least Recently Used keys across *any* key, regardless of whether it has an expiry set.



### 16. How does Redis handle key expiration under the hood?

* **Answer:** Redis doesn't spin up a dedicated thread for every expiring key. Instead, it combines two strategies:
1. **Passive Deletion:** When a client attempts to access a key, Redis checks its expiry. If expired, it deletes it and returns nil.
2. **Active Deletion:** Every 100 milliseconds, Redis samples 20 random keys with TTLs. It deletes all expired keys found. If more than 25% of the sampled keys are expired, it repeats the process to aggressively clean memory without blocking execution.



### 17. What is memory fragmentation in Redis, and how do you resolve it without a restart?

* **Answer:** Fragmentation occurs because the underlying memory allocator (like jemalloc) allocates memory in fixed chunks. When Redis frequently overwrites or deletes keys of varying sizes, it leaves physical gaps that the OS sees as allocated, but Redis cannot use efficiently.
* **Fix:** Check `info memory` for `mem_fragmentation_ratio`. If it's high (e.g., > 1.5), you can enable **Active Defragmentation** at runtime using `CONFIG SET activedefrag yes`. Redis will start moving data keys into contiguous blocks on the fly.

---

## Category 6: Performance Tuning & Troubleshooting

### 18. You notice a sudden latency spike in your application's Redis metrics. How do you troubleshoot this?

* **Answer:**
1. Run the `SLOWLOG GET` command to check if any expensive algorithms (like `KEYS`, `SMEMBERS`, or large Lua scripts) are blocking the single thread.
2. Check system metrics for **CPU usage** (if it's hitting 100% on a single core) and **Memory Swapping** (if memory is leaking to disk swap, latency tanks).
3. Check `latency doctor` or use the command line tool `redis-cli --latency` to isolate if the issue is network-bound.
4. Verify if a large **RDB fork** or **AOF rewrite** is occurring concurrently.



### 19. Why is the `KEYS` command banned in production environments, and what is its alternative? What are the trade-offs of the alternative?

* **Answer:** `KEYS pattern` is an $O(N)$ blocking operation that scans the entire keyspace database sequentially. In production databases with millions of keys, it will freeze the entire single-threaded Redis engine for seconds.
* **Alternative:** Use `SCAN` (or `HSCAN`, `SSCAN`). It is a cursor-based iterator that returns small chunks of data per call without blocking.
* *Trade-off:* The client has to make multiple network round trips using a loop, and because it's a stateless cursor, keys added or removed during the scan iteration might be missed or duplicated.

### 20. How do Redis Lua scripts ensure atomicity, and what are the limitations/dangers of executing them?

* **Answer:** Lua scripts are atomic because Redis executes the entire script within its single main command thread. No other client commands can run middle-execution, acting like a transactional block.
* *Dangers:* If a Lua script contains an infinite loop, or processes a massive dataset, it will block the entire Redis instance. Other clients will time out, forcing you to use `SCRIPT KILL` (only works if no writes were performed) or `SHUTDOWN NOSAVE` to salvage the system.

