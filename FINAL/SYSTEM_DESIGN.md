# System Design Interview Questions & Answers

> Interview prep: distributed systems fundamentals, debugging scenarios, sharding pitfalls, failure isolation, performance tuning, observability, and resilience.

---

## Table of Contents

1. [Fundamentals](#1-fundamentals)
2. [Real Scenario Debugging (Q1–Q6)](#2-real-scenario-debugging-q1q6)
3. [Critical Data Disparity (Q7–Q12)](#3-critical-data-disparity-q7q12)
4. [System Failure Isolations (Q13–Q18)](#4-system-failure-isolations-q13q18)
5. [Performance Tuning (Q19–Q24)](#5-performance-tuning-q19q24)
6. [Production Observability (Q25–Q30)](#6-production-observability-q25q30)
7. [Production Failure Cases (Q31–Q36)](#7-production-failure-cases-q31q36)
8. [System Resilience & Scaling (Q37–Q40)](#8-system-resilience--scaling-q37q40)

---

## 1. Fundamentals

### How do you eliminate a single point of failure?

A **SPOF** is any component whose failure takes down the whole system.

**Eliminate by:**
1. **Redundancy** — multi-AZ / multi-region replicas for compute, DB, cache, brokers
2. **Load balancing** — no single app box; health-checked fleets
3. **Stateless services** — scale horizontally; sessions in Redis/DB, not local disk
4. **Leader election with quorum** — avoid one irreplaceable master without failover
5. **Multi-AZ databases** — primary + standby / multi-primary where appropriate
6. **DNS / anycast / dual LB** — redundant ingress
7. **Queue + consumers** — competing consumers, not one worker
8. **Chaos testing** — verify failover actually works

Trade-off: cost and complexity rise with redundancy.

---

### What is a heartbeat in distributed systems?

A **heartbeat** is a periodic “I’m alive” signal from a node to peers, a registry, or a monitor.

**Uses:**
- Service discovery TTL (Consul/etcd/K8s liveness)
- Failure detection (miss N heartbeats → mark dead)
- Lease renewal for locks/leadership

Too aggressive → false positives under GC/network blips. Too slow → long failover. Often combined with **phi-accrual** or exponential backoff detectors.

---

### What are sticky sessions?

**Sticky sessions (session affinity)** = load balancer always routes a user’s requests to the **same backend** instance (cookie or IP affinity).

**Why:** legacy apps keep session state in local memory.  
**Problems:** uneven load, painful deploys, instance death loses sessions.  
**Prefer:** externalize session (Redis) and keep APIs **stateless** — stickiness only as a temporary bridge.

---

### Strong consistency vs eventual consistency?

| | **Strong consistency** | **Eventual consistency** |
|--|------------------------|--------------------------|
| Guarantee | After a write completes, all readers see the latest value (linearizable/sequential variants) | Replicas converge given enough time without new writes |
| Latency | Often higher (coordination/quorum) | Lower reads/writes |
| Availability during partition | May refuse requests | Often stays available |
| Examples | Spanner, etcd, Postgres primary reads | DynamoDB eventual, Cassandra (tunable), DNS, caches |

Choose strong for money/inventory; eventual for feeds, counters, CDN caches — with conflict resolution (LWW, CRDTs, version vectors).

---

### Two nodes in different DCs both think they’re the leader (split-brain)

**Split-brain:** network partition → both sides elect a leader → divergent writes → data corruption.

**Prevent:**
- Quorum voting (`> N/2`) — minority cannot elect
- Odd number of voters / witness node
- Fencing tokens / epoch numbers — old leader’s writes rejected
- STONITH / lease-based leadership with short TTL
- Avoid dual-active writers across DCs without consensus

---

### What’s a quorum in distributed systems?

**Quorum** = minimum number of nodes that must agree for an operation to succeed.

Classic: for N replicas, reads/writes with R + W > N prevent stale reads overlapping writes.

**Leader election:** typically need majority (`floor(N/2)+1`).

Used in Raft/Paxos, Cassandra consistency levels (`QUORUM`), ZooKeeper ensembles.

---

### What is a circuit breaker pattern?

Stops calling a failing dependency after repeated errors — **fail fast** instead of cascading timeouts.

States: **Closed** (normal) → **Open** (reject calls) → **Half-Open** (trial requests).

```
Caller → Circuit Breaker → Payment API
              ↓ open
         return fallback / 503 quickly
```

Pair with timeouts, bulkheads, retries (with jitter), and fallbacks.

---

### What is event sourcing?

Persist **state changes as an append-only event log**; current state = replay/fold of events (often with snapshots).

```
OrderCreated → ItemAdded → PaymentCaptured → OrderShipped
```

**Pros:** audit trail, temporal queries, rebuild read models (CQRS).  
**Cons:** complexity, schema evolution, eventual read models, harder ad-hoc queries on raw events.

---

### Forward proxy vs reverse proxy?

| | **Forward proxy** | **Reverse proxy** |
|--|-------------------|-------------------|
| Sits in front of | **Clients** | **Servers** |
| Client knows | Proxy; destination may be hidden | Destination hostname; backends hidden |
| Uses | Corporate egress, filtering, anonymity | LB, TLS termination, caching, WAF (Nginx, ALB, Cloudflare) |

---

### Kafka vs RabbitMQ?

| | **Kafka** | **RabbitMQ** |
|--|-----------|--------------|
| Model | Distributed **log** / streaming | Smart **broker** message queue |
| Consumer | Pull; offset; replay | Push/pull; ack; often delete on consume |
| Throughput | Extremely high, partitioned | High; more routing flexibility |
| Routing | Topics + partitions; consumer groups | Exchanges (direct/topic/fanout/headers) |
| Replay | First-class | Limited (need plugins/patterns) |
| Best for | Event streaming, analytics, CQRS | Task queues, complex routing, RPC-ish workflows |

---

### What is Elasticsearch?

Distributed **search and analytics engine** on inverted indexes (Lucene). Great for full-text search, logs (ELK/OpenSearch), aggregations — **not** a primary transactional OLTP store.

Features: sharding/replicas, near-real-time search, analyzers, relevance scoring.

---

### WebRTC and SFU in multi-user Zoom-like calls?

**WebRTC:** browser APIs for real-time audio/video/data with NAT traversal (STUN/TURN) and peer connections.

**Mesh:** every participant sends to every other — doesn’t scale (N² streams).

**SFU (Selective Forwarding Unit):** each client uploads **once** to a media server; SFU **forwards** selected streams to others (no heavy re-encode). Scales better than mesh.

**MCU:** mixes/composes into one stream (CPU heavy on server). Zoom-like systems typically use SFU (sometimes hybrid) + simulcast/SVC layers for bandwidth adaptation.

---

### How many types of load balancing algorithms?

Common algorithms (interview list):

1. **Round Robin**
2. **Weighted Round Robin**
3. **Least Connections**
4. **Weighted Least Connections**
5. **IP Hash / Consistent Hash**
6. **Least Response Time / Least Latency**
7. **Random / Weighted Random**
8. **Sticky / Affinity-based**
9. **Resource-based** (CPU/memory aware)
10. **Geographic / latency-based (GSLB)**
11. **Maglev / ring hash** (L4 modern LBs)

Also L4 vs L7 distinction (connection vs request routing).

---

### Upload large files to S3 with multipart upload?

1. `CreateMultipartUpload` → get `UploadId`
2. Split file into parts (typically ≥ 5 MB except last; max 10,000 parts)
3. `UploadPart` each chunk in parallel (retries per part)
4. Collect ETags + part numbers
5. `CompleteMultipartUpload`
6. On failure: `AbortMultipartUpload` (avoid orphan parts / storage cost)

Clients: AWS SDK high-level transfer manager, `aws s3 cp` multipart under the hood. Use multipart for reliability, parallelism, and resumability on large objects.


---

## 2. Real Scenario Debugging (Q1–Q6)

### Q1. Checkout latency 3.2s — DB profile query 20ms, object mapping 1.5s. Fix?

**Bottleneck is CPU/serialization in app tier, not SQL.**

**Fix:**
- Profile ORM hydration (Django/SQLAlchemy/Hibernate) — too many fields/relations loaded
- Use DTOs / `values()` / projection queries — map only needed columns
- Avoid nested object graphs, reflection-heavy mappers, JSON parse/serialize loops
- Cache mapped DTO if stable; reuse buffer pools
- Check N+1 hidden in mapper; Jackson/Gson config; debug vs prod serializers
- Flamegraph the 1.5s path — often lazy loads triggered during mapping

**Don’t** scale DB first — evidence points to application mapping.

---

### Q2. Product listings slow under load. Cache hit 98%, but DB pools exhaust. Misconfigured?

**Classic: cache stampede / thundering herd / uncached code path still hits DB.**

Likely causes:
1. **Miss path stampedes** — 2% miss of huge QPS still floods DB; no singleflight/lock on populate
2. **Cache stores “null” poorly** or short TTL on hot keys → synchronized expiry
3. **Connection leak** on miss/error path (not returning connections)
4. **Read-through bug** — every request “checks” DB for validation despite cache hit
5. **Pool sized for hits, not miss bursts**; no shed load when pool waits

**Fix:** request coalescing (singleflight), soft TTL + jitter, serve stale, bounded pool wait + 503, fix leaks, separate pools for background vs online.

---

### Q3. Service A → B is fast, but A’s total time is 2×. Network negligible. Extra time?

Extra time is **inside A** after/before B:
- Sequential work that could be parallel (`profile` then `cart` then `B`)
- Serialization/deserialization of large payloads
- Sync logging / audit writes
- Thread pool queue wait
- GC pause
- Blocking on locks/connection pools
- Retry/timeouts misconfigured (wait full timeout rarely)

**Trace spans inside A** — not only A→B hop.

---

### Q4. Brief hang after Submit; heavy validation in logs. Optimize task or refactor flow?

**Refactor the user flow first (usually):** return **202 Accepted** / “submitted” quickly; run heavy validation **async** (queue); notify via webhook/poll/email.

Optimize the task too if cheap wins exist — but UX shouldn’t wait on heavy sync validation unless business-critical and fast enough for SLO.

**Why:** perceived latency and timeout risk; protects web tier under load (bulkhead).

---

### Q5. Critical background sync times out every day at 6AM. Other load low. Root cause?

**Time-correlated batch collision.**

Trace:
1. Cron calendar — what else runs at 06:00? (DB backups, vacuum/ANALYZE, ETL, billing, report jobs)
2. Cloud maintenance windows, snapshotting, index rebuilds
3. Lock waits (`pg_locks`, InnoDB status) — sync blocked on backup lock
4. Data volume spike Mondays / month-end
5. Quiet shared resource: warehouse export, S3 rate limits, DNS

**Method:** compare 05:50–06:20 metrics (DB IOPS, locks, CPU, network) across days; enable job-level tracing; stagger schedules; move sync to replica/warehouse.

---

### Q6. ‘Latest News’ slow — one simple JOIN, indexes look fine. Hidden issue?

Possibilities:
1. **`SELECT *` / wide rows** + large text/JSON columns pulled every time
2. **Implicit sort** (`ORDER BY created_at DESC LIMIT 20`) without supporting index → filesort on huge table
3. **ORM N+1 after the JOIN** (related images/authors)
4. **Cache bypass** or query not identical → never hits query cache
5. **Table bloat / outdated stats** → bad plan
6. **Hot partition / lock contention** from writers
7. **Application serializes huge graph** after fetch
8. **Cross-AZ / remote DB** latency amplified by chatty queries

Check `EXPLAIN ANALYZE`, payload size, and post-query CPU.


---

## 3. Critical Data Disparity (Q7–Q12)

### Q7. Shard by User ID; celebrity with 10M records triggers split. How re-shard?

**Hot key / celebrity problem** — hash(user_id) alone fails.

**Strategies:**
1. **Salting / secondary sharding:** `hash(user_id + bucket)` with N buckets for that user; fan-out reads
2. **Dedicated shard / cell** for mega-users
3. **Split entity:** shard posts by `post_id` while keeping user metadata elsewhere
4. Online migration: dual-write → backfill → cut reads → drop old
5. Consistent hashing ring with virtual nodes for smoother moves

Avoid naive “split shard in half” without a plan for routing celebrity traffic.

---

### Q8. User table sharded; batch JOIN across all shards kills everyone. Anti-pattern detection & isolation?

**Scatter-gather JOINs on OLTP shards are an anti-pattern.**

**Detection:**
- Query gateway tags / SQL proxy (ProxySQL, pgbouncer stats) — flag multi-shard fanout
- Require `shard_key` in query planner; reject cross-shard joins in online path
- Metrics: queries touching >K shards; alert

**Isolation:**
- Batch jobs use **analytics replica / warehouse** (Snowflake/BigQuery/Redshift) or offline export
- Separate connection pool + lower priority / night window
- Pre-aggregated tables, denormalized read models
- Kill switch for cross-shard queries

---

### Q9. 10 shards; total disk 30%, Shard #3 at 98%. Why uneven?

**Skewed shard key distribution:**
- Low-cardinality key (country, status)
- Sequential IDs without hash → time-based hotspot on “latest” shard
- Tenant/celebrity concentration
- Bug in shard map (most writes routed to #3)
- Hash collision range / bad range boundaries

**Fix:** hash sharding with virtual nodes; reshard hot ranges; salt keys; monitor per-shard size/QPS.

---

### Q10. Migrate 100M historical transactions into sharded schema — efficient non-blocking pipeline?

1. **Dual-write** new txns to old + new (or CDC)
2. **Bulk backfill** from snapshots in parallel workers partitioned by shard key ranges
3. Use **COPY / bulk ingest**, disable secondary indexes then rebuild, larger batches
4. **Throttle** to protect primary; run against read replica / export dump
5. **Checksum** per partition; shadow reads
6. Cut over reads gradually (feature flag %)
7. Keep pipeline **idempotent** (upsert by PK)

Non-blocking: never lock whole table; chunk by ID ranges; rate-limit.

---

### Q11. Auto-sharding; pool exhaustion; one shard targeted. Detect hot keys?

- Per-shard QPS / connection wait metrics
- Proxy/query logs: top keys by frequency (sampled)
- Application metrics tagged with `shard_id` + hashed key bucket
- Cache miss rate per key; lock contention on key
- Dynamic heat maps (Redis `HOTKEYS`-style sampling, or custom counters with decay)

**Mitigate:** local cache, salting, dedicated lane, rate-limit abusive key, move hot key.

---

### Q12. Primary DB sharded; global non-sharded lookups (product catalog) stay HA & fast?

**Don’t put global catalogs on user shards.**

Options:
1. **Separate catalog service/DB** — small, heavily replicated, cached
2. **CDN + edge cache** for read-mostly catalog
3. **Replicated reference data** to each cell/region (read-local)
4. Redis/Memcached with pub-sub invalidation
5. Search index (Elasticsearch) for browse; source of truth elsewhere

HA: multi-AZ replicas, cache fallbacks, stale-while-revalidate.


---

## 4. System Failure Isolations (Q13–Q18)

### Q13. Order service 5k RPS; payment gateway slows; whole system crashes. What is it?

**Cascading failure** (often via **thread/connection pool exhaustion** and timeout amplification).

Order workers block on slow payment → pools full → health checks fail → more retries → meltdown.

**Need:** timeouts, circuit breaker, bulkhead isolation, async payment + webhook, load shedding, fallback queue.

---

### Q14. A depends on B and C. B slow; A fails over 15 min and kills C. Why didn’t circuit breaker contain it?

Common reasons CB “failed”:
1. **Timeout too high** — threads stuck waiting; CB counts failures slowly
2. **CB only around B**, but retries still hammer B and hold resources needed for C
3. **No bulkhead** — shared thread/DB pool for B and C calls
4. **Retry storm** bypasses open state (different client instance / no shared CB state)
5. **Fail-open** misconfiguration
6. Half-open allows too much traffic

**Fix:** aggressive timeouts, per-dependency bulkheads, limit retries, shared CB state, fail fast to protect C.

---

### Q15. New deploy; traffic 2×; 20 pods at 95% CPU in 3 minutes?

Likely:
- Inefficient new code path / N+1 / busy loop
- Missing cache after deploy (cold cache stampede)
- GC thrashing from allocation spike
- Autoscale lag — capacity not ready
- Sync fan-out to dependencies

**Actions:** rollback, load test diff, flamegraph, warm caches before cutover, HPA with faster metrics, canary.

---

### Q16. Retry storm from mutual retries under load. Anti-retry storm strategy?

1. **Timeouts < caller patience**
2. **Limited retries** (0–2) + **exponential backoff + jitter**
3. **Idempotency** keys
4. Circuit breakers / bulkheads
5. **Retry-After** / token bucket for retries
6. Prefer **async** + queue over sync retry chains
7. Hedge requests carefully (can worsen storms)
8. Distinguish 429/503 (retry) vs 400 (don’t)

---

### Q17. Designed for 10M users; freezes at 1M concurrent; huge serialization overhead. Optimize object creation / GC?

- Avoid allocating per-request giant object graphs
- Reuse buffers; object pooling where safe (byte buffers)
- Binary protocols (protobuf) vs fat JSON
- Stream responses; paginate
- Reduce ORM entity materialization
- Tune GC (G1/ZGC), heap sizing; prefer fewer short-lived objects
- Intern/reuse constants; flyweight DTOs
- Offload serialization to specialized libs (jackson afterburner, orjson, etc.)

---

### Q18. 1M RPS endpoint; 98% cache hits; DB pools still exhaust. Missing config?

Same family as Q2:
- **No request coalescing** on miss
- Cache client talks to DB for **every** hit (e.g., write-through validation bug)
- **Connection not using pool correctly** on hit path (opening new connections)
- Background refresh stampedes
- Pool **maxWait** infinite → thread pileup

Often missing: **lock/singleflight around cache fill** + **fail-fast when pool saturated** + separate **read replica** for miss path.


---

## 5. Performance Tuning (Q19–Q24)

### Q19. Designed for 10M users, sub-100ms; 2× data growth → 5s latency; no code change. Look first?

**Data-dependent performance:**
1. Query plans changed — stats stale; seq scans appear
2. Index no longer selective; bloat
3. Working set exceeded **memory/cache** → disk I/O
4. Partition/shard imbalance from growth
5. Lock contention with larger tables
6. Pagination `OFFSET` deep pages

**First:** `EXPLAIN ANALYZE`, DB I/O, cache hit ratio, slow query log — not app code diff.

---

### Q20. Spring Boot 95% CPU; low RPS. Find thread/method in prod?

1. **Async profiler / py-spy / perf / JFR** — CPU flamegraphs (safe sampling)
2. `jstack` / thread dump multiple times — runnable hot stacks
3. APM code-level CPU profiles (Datadog/New Relic)
4. Check busy loops, regex catastrophic backtracking, JSON parse of huge payloads, excessive logging, crypto in hot path
5. Compare GC CPU vs application CPU

Prefer continuous profiling over guessing.

---

### Q21. Sharded primary; batch JOIN hits all shards; freezes system 10 min. Prevent?

Same as Q8: **forbid OLTP scatter-gather**; run analytics on warehouse/replicas; workload isolation (separate pools, queues, time windows); query admission control.

---

### Q22. Critical read slow; cache hit 95%; latency 1.2s; scaling DB doesn’t help. Hidden issue?

If DB scale doesn’t help, latency is **not primarily DB**:
- App-side serialization / huge payloads
- Downstream HTTP calls still on hit path
- Lock contention in app
- GC / CPU saturation
- Cache is remote and slow (cross-region Redis) — “hit” still 1.2s RTT × chatty gets
- Multiple sequential cache lookups

Profile **end-to-end spans**; check payload size and cache RTT.

---

### Q23. 1 of 10 API instances at 99% CPU; others 10%; LB is Round Robin. Cause?

Round Robin balances **requests**, not **CPU work**.

Causes:
- **Sticky sessions** somehow enabled (or long-lived connections pinned)
- **Unequal request cost** — heavy users hashed to one node (if not pure RR)
- **One pod got bad deploy** / memory leak / hot loop
- **Local cache asymmetry** — one node serving all misses after restart… (RR alone wouldn’t pin forever unless connection reuse / HTTP/2 to one backend)
- **Least-conn misreported** as RR; or DNS caching to one IP
- Background thread runaway on one instance only

Check: connection distribution, in-flight cost, that instance’s unique traffic/logs, HPA targets.

---

### Q24. Circuit breakers; A slows → B opens → C opens → total outage. Why?

**Cascading circuit opening / retry amplification:**
- Shared failure domains
- Overly sensitive thresholds
- Retries from A overload B → B opens → traffic shifts to C → C opens
- Lack of **fallback** / **shed load** / **priority queues**
- Tight coupling synchronous fan-out

**Design:** bulkheads, different thresholds, graceful degradation (cached responses), avoid synchronized retry, dependency isolation, chaos-test partial failure.


---

## 6. Production Observability (Q25–Q30)

### Q25. Background sync times out every morning 6AM — trace root cause?

*(Same class as Q5.)* Correlate cron/backup/ETL; lock graphs; per-job traces; resource saturation only in that window; stagger jobs; use replicas.

---

### Q26. Latest News slow; simple JOIN; indexes OK — hidden issue?

*(Same as Q6.)* Wide rows, sort without index, ORM N+1, bloat/bad plans, huge serialization, remote DB chatty pattern.

---

### Q27. Auto-sharding; pool exhaustion; specific shard targeted — detect hot keys?

*(Same as Q11.)* Per-shard metrics, sampled top-key counters, heat maps, cache miss spikes per key.

---

### Q28. Order service 5k RPS; payment gateway slow; whole system crashes — cascade pattern?

**Cascading failure** via blocked threads + retries + pool exhaustion + health-check death spiral.

Name it clearly in interview: *“cascade failure triggered by synchronous dependency with insufficient isolation (no bulkhead/circuit breaker/timeout).”*

---

### Q29. 1M RPS, 98% cached, DB pools exhaust — missing configuration?

*(Same as Q18/Q2.)* Missing **singleflight / lock on cache populate**, miss-path isolation, or a bug hitting DB on hit path; infinite pool wait.

---

### Q30. 1/10 instances 99% CPU; Round Robin — imbalance cause?

*(Same as Q23.)* Pinning/stickiness, hot connections, bad instance, uneven work per request, runaway thread on one pod.


---

## 7. Production Failure Cases (Q31–Q36)

### Q31. A depends on B and C; B slow; A retries sync to B and kills C. Misconfigured?

- Missing/too-weak **circuit breaker** on B
- **Shared thread/connection pool** (no bulkhead between B and C)
- **Unbounded retries** / no jitter
- Timeouts too large
- Retrying non-idempotent calls without limit

**Config fix:** per-dependency pools + short timeouts + CB + max 1 retry + shed load.

---

### Q32. New version; traffic 2×; 20 pods 95% CPU in 3 min. How to respond?

1. **Rollback / disable flag** immediately if SLO burning
2. Confirm traffic vs efficiency regression (compare CPU per request)
3. Flamegraph canary vs baseline
4. Check cold cache, migration locks, connection storms
5. Scale out **and** fix code; warming + gradual traffic shift next time

---

### Q33. 6AM sync timeout — trace without impacting live users?

- Use **read replicas** / shadows for diagnosis queries
- Sampled tracing on the job only
- Analyze historical metrics/logs (no heavy `DEBUG` on prod web path)
- Clone workload in staging with production-sized snapshot
- `pg_stat_activity` snapshots; avoid locking admin ops on primary peak

---

### Q34. Hang after Submit; heavy validation — optimize or refactor?

**Refactor flow to async** (primary); optimize validation (secondary). Return fast acknowledgment; process in worker; preserve UX and protect capacity.

---

### Q35. Sharded DB; batch JOIN freezes all shards 10 min — prevent?

Isolate analytics; warehouse; ban cross-shard OLTP joins; separate pools + admission control; chunked map-reduce style aggregation offline.

---

### Q36. Deadlocks only under high concurrent writes — identify transactions & tables?

**Postgres:** `pg_locks` + `pg_stat_activity`; `log_lock_waits`; deadlock details in logs (queries involved).  
**MySQL:** `SHOW ENGINE INNODB STATUS`; performance_schema.  
**App:** consistent lock ordering; shorter transactions; indexes to avoid lock escalation; retry deadlocked txns idempotently.

Capture: truncated SQL, wait graphs, table/index names, frequency by endpoint.


---

## 8. System Resilience & Scaling (Q37–Q40)

### Q37. Stateless API; heavy GC under load — minimize object creation?

- Slim DTOs; avoid autoboxing storms
- Reuse thread-local buffers carefully
- Pool expensive serializers; byte[] recycling
- Prefer streaming I/O
- Reduce temporary collections in hot paths
- Protobuf/msgpack
- Tune GC / heap; measure allocations per request (async profiler alloc mode)

Re-architect: move heavy transforms to async workers; cache serialized fragments.

---

### Q38. Event-driven service; message queue reaches critical (backlog trap)

When queue depth explodes:

**Risks:** lag SLO breach, disk full, rebalance storms, poison messages blocking partition, retry amplification.

**Controls:**
- Consumer autoscaling on lag
- Alert on depth/age
- DLQ + rate-limited retries
- Publisher throttling / backpressure (reject 429)
- Separate priority queues
- Idempotent consumers; fix slow handler
- Cap retention; scale brokers

Don’t “just add publishers” without consumer capacity.

---

### Q39. Instantly revoke one user’s JWT globally with low latency?

JWTs are normally **stateless** — revocation needs a side channel:

1. **Short-lived access tokens** (e.g. 5 min) + refresh tokens server-tracked — revoke refresh immediately; access dies soon
2. **Denial list** in Redis (user_id / jti) checked on each request — replicate globally (Redis Enterprise / regional caches + pubsub invalidation)
3. **Version claim** (`token_version`) in JWT; store version per user; bump on revoke; caches keep versions
4. Gateway enforces denylist near edge for low latency

Trade-off: pure JWT without lookup can’t revoke instantly — add a fast bloom/Redis check or keep TTL tiny.

---

### Q40. Non-reproducible race causing minor corruption — instrumentation with minimal impact?

1. **Sampled** detailed tracing when inconsistency detected (checksum mismatch)
2. Record **before/after versions** + request_id / actor / timestamp on writes (optimistic locking `version` column)
3. **Detect** with periodic validators / dual-read compare — not full logging always-on
4. Flight-recorder / continuous profiling at low CPU (<1–2%)
5. Deterministic logging of lock order only on conflict paths
6. Chaos / concurrency tests in staging with thread sanitizers where applicable
7. Emitting a metric when `update ... where version=` affects 0 rows (lost update signal)

Goal: capture evidence on rare path without logging every request.

---

## Quick Cheat Sheet

| Concept | One-liner |
|---------|-----------|
| SPOF | Redundancy + no single brains without failover |
| Heartbeat | Periodic liveness signal |
| Sticky session | Pin user to one instance (prefer external session) |
| Quorum | Majority agreement (`> N/2`) |
| Split-brain | Two leaders → fence with quorum/epochs |
| Circuit breaker | Fail fast to stop cascades |
| Kafka vs RMQ | Log/stream vs smart queue |
| SFU | Upload once; server forwards media |
| Cache 98% + pool empty | Miss stampede / hit-path DB bug / no singleflight |
| Mapping 1.5s | Fix app serialization, not DB |
| Celebrity shard | Salt / dedicated cell / re-key |
| Payment slow → outage | Cascade; add bulkhead+CB+timeout |
| Retry storm | Jitter, limits, CB, async |
| JWT revoke | Denylist / version / short TTL + refresh revoke |

---

*Related notes: `FINAL/MICROSERVICES/DISTRIBUTED_system.md`, `FINAL/API_DESIGN.md`, `FINAL/AWS/SNS_SQS.md`.*
