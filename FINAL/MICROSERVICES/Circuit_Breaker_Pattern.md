# Circuit Breaker Pattern in Microservices — Detailed Study

Starting reference: [Circuit Breaker walkthrough](https://youtu.be/dJI2saoM5_k?si=lW1atKNTYgQX8osa)

This note is a mid-to-senior study of the **Circuit Breaker** pattern: why remote calls fail differently from in-memory calls, how the three-state machine stops cascading failure, how it composes with timeout / retry / bulkhead / fallback, and where to put it (application vs gateway vs service mesh).

Related local notes: `FINAL/MICROSERVICES/DISTRIBUTED_system.md` (fallacies of distributed computing, sync vs async), `FINAL/MICROSERVICES/Event-Driven_Architecture.md` (when you avoid the sync call chain entirely).

---

## 1. What problem it solves

A method call in the same process either returns or throws. A **remote** call (HTTP, gRPC, DB, payment API) can:

- fail immediately (connection refused, 5xx)
- hang until a timeout
- succeed but be **slow** (200 OK in 30 seconds)

Slow is often worse than dead. A dead dependency fails fast. A slow one holds **threads, connections, and sockets** while callers wait. In a microservice graph that looks like:

```
API Gateway → Order Service → Payment Service → Fraud Service
```

If Fraud is slow, Payment’s thread pool fills waiting on Fraud. Order then fills waiting on Payment. The gateway times out. One sick dependency takes down healthy services that only needed a thread.

That is **cascading failure**. Michael Nygard popularized the Circuit Breaker in *Release It!* (2007) as the software analogue of an electrical breaker: when current (failures) exceeds a safe level, **cut the circuit** so the rest of the building (the calling service) does not burn.

Martin Fowler’s summary: wrap the remote call in an object that counts failures. Past a threshold, **stop calling**. Return an error (or fallback) immediately. After a cool-down, try a few probes. If they work, close the circuit again.

The breaker primarily **protects the caller** (and the rest of the platform). It also **gives the sick dependency breathing room** by stopping a retry storm.

---

## 2. The three states (electrical naming)

In electricity, **closed** means current flows. Software kept that convention — it feels backwards in English.

```
                 failure rate / count >= threshold
        +--------------------------------------------------+
        |                                                  |
        v                                                  |
   +--------+     waitDuration elapsed      +-----------+  |
   |  OPEN  | --------------------------->  | HALF-OPEN |  |
   | fail   |                               | probe N   |  |
   | fast   | <---------------------------- +-----------+  |
   +--------+     probe failed                    |
                                                  | probes succeeded
                                                  v
                                            +----------+
                                            |  CLOSED  |
                                            |  normal  |
                                            +----------+
```

| State | What happens to traffic | Why it exists |
| --- | --- | --- |
| **Closed** | All calls go to the dependency. Outcomes are recorded in a sliding window. | Normal operation + health sampling |
| **Open** | Calls are **not** made. Immediate failure (`CallNotPermittedException` / fast 503) or a **fallback**. | Stop wasting caller resources; stop beating a dying service |
| **Half-Open** | Only a **limited** number of trial calls. Success → Closed. Any/too many failures → Open again. | Recover without flooding a service that just came back |

Half-Open is only entered **from Open**. There is no Closed → Half-Open shortcut. It is a recovery probe, not a warmup mode.

Microsoft’s extra point: Half-Open exists because a recovering service can often handle a trickle but not the full backlog. Dumping every waiting request at once can knock it over again.

---

## 3. What “failure” means (you must define this)

Not every exception should trip the breaker.

| Usually **record** (count toward open) | Usually **ignore** (business, not outage) |
| --- | --- |
| Timeouts | 4xx that mean “bad request / not found / conflict” |
| Connection failures | Domain validation errors |
| HTTP 5xx, 429 (throttling) from a dependency | Auth failures if they are the client’s bug |
| Thread-pool / bulkhead rejection (optional policy) | Expected “payment declined” |

Fowler: different errors can have **different thresholds** (e.g. trip faster on connection refused than on occasional timeouts).

Modern libraries also trip on **slow calls**: the HTTP 200 that took 8 seconds still starved your pool. Resilience4j: `slowCallDurationThreshold` + `slowCallRateThreshold`.

Minimum sample size matters. A 50% failure rate on **two** calls should not open the circuit. Use `minimumNumberOfCalls` (or equivalent) so you only evaluate after enough traffic.

---

## 4. How the trip is computed

Two common windows (Resilience4j model):

| Window | Measures | Fits |
| --- | --- | --- |
| **Count-based** | Last N calls | Steady traffic |
| **Time-based** | Calls in the last T seconds | Spiky / variable QPS |

Older / simpler breakers: **N consecutive failures** then open. That is easier to reason about but can miss a 40% error rate that never strings 5 failures in a row.

Open duration (`waitDurationInOpenState`, Fowler’s reset timeout): long enough for the dependency to recover, short enough that you do not serve fallbacks after it is already healthy. Too short → **flapping** (open/half-open/open). Too long → unnecessary degradation.

Half-Open: permit **several** probes, not one. A single lucky success can close the circuit onto a still-sick service. A single unlucky blip can also reopen it forever if you only allow one probe — tune `permittedNumberOfCallsInHalfOpenState`.

---

## 5. Circuit breaker is not retry, timeout, or bulkhead

These are **different knobs**. Production systems compose them; treating them as synonyms is a design smell.

| Pattern | Question it answers |
| --- | --- |
| **Timeout** | How long am I willing to wait for *this* call? |
| **Retry** | Was that a **transient** blip I should try again? |
| **Circuit breaker** | Is this dependency **currently unsafe to call at all**? |
| **Bulkhead** | Can one slow dependency exhaust **all** of my threads? |
| **Rate limiter** | Am I exceeding a quota / slamming a partner API? |
| **Fallback** | What do I return when I will not (or cannot) call it? |

**Retry vs breaker (Microsoft):** Retry assumes the next attempt might work. Breaker assumes further attempts are **likely to fail** and should stop. If you wrap retry *around* a breaker, retries must **stop** when the breaker is open — otherwise you retry a guaranteed fast-fail and amplify load on *yourself*.

**Dangerous combo:** Retry without a breaker during an outage = **retry storm** (thundering herd). Always pair retries with exponential backoff, jitter, idempotency, and a breaker.

**Timeout without a breaker:** every request still occupies a thread for the full timeout. The breaker is what stops you from even starting those doomed waits.

**Bulkhead (ship compartments):** cap concurrent calls **per dependency** (semaphore or dedicated thread pool). Even with a breaker, a burst of slow calls *before* the window trips can exhaust the shared Tomcat/gRPC pool. Netflix Hystrix made thread-pool isolation famous for this reason. Resilience4j defaults to lighter **semaphore** bulkheads; use thread pools when you truly need isolation.

Typical composition (Resilience4j default aspect order, inside-out):

```
Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( call ) ) ) ) )
```

Know the order. Retry outside the breaker means “retry until the breaker opens, then stop.” Timeout inside means a hung call becomes a recorded failure the breaker can see.

---

## 6. Fallback: fail fast is not the product

An open circuit is useless if the only outcome is a 500 to the user. Design **degraded** behavior:

| Fallback | When it is honest |
| --- | --- |
| Cached / stale read | Recommendations, profile extras, FX rates with a freshness SLA |
| Default / feature off | “Reviews unavailable”; hide the widget |
| Queue for later | Fraud check for low-value orders; email send |
| Alternate provider | Secondary payments, multi-region replica |
| Fail the user operation | Checkout when payment **must** succeed — do not fake a charge |

Never invent a successful payment in fallback. Never return empty inventory as “in stock.” Fallback is **graceful degradation**, not lying.

---

## 7. A concrete cascade (why interviews love this)

Order Service calls Payment; Payment calls Fraud.

**Without a breaker:** Fraud p99 jumps from 200ms to 30s. Payment threads block. Payment pool saturates. Order threads block on Payment. Gateway times out. Customers retry, making it worse.

**With a breaker on Payment → Fraud:** after the failure/slow threshold, Payment **stops calling Fraud**, returns a designed fallback (skip fraud under $X, or queue for review). Payment stays up. Order stays up. You have contained a **dependency outage** to a **feature degradation**.

Same idea for a DB shard, Redis, or a SaaS API. One breaker **per dependency** (and often per operation class). Do **not** share one breaker across unrelated hosts/shards — a dead shard A would block healthy shard B (Microsoft: resource differentiation).

---

## 8. Where the breaker lives

| Layer | What it isolates | Fallback | Typical tools |
| --- | --- | --- | --- |
| **Application** | Method / client / named dependency | Full business fallback | Resilience4j, Polly, `gobreaker`, `opossum` (Node), `failsafe` / `tenacity` (Python) |
| **API gateway** | Downstream cluster from the edge | Generic 503 / cached page | Kong, Spring Cloud Gateway, AWS API GW |
| **Service mesh** | Unhealthy **pods** (outlier detection), connection pools | Usually 503, no domain fallback | Istio/Envoy, Linkerd |

Istio **outlier detection** ejects a bad *instance* from the load-balancing pool. That is related but not identical to “stop calling the Payment *service*.” Mesh: language-agnostic, no code. App breaker: knows that “payment declined” is not an outage.

**Best practice in 2026:** mesh or platform for instance ejection + connection limits; **application** breaker + fallback for business-critical clients. They stack; they are not duplicates of the same control.

Hystrix (Netflix) defined the industry, then went **maintenance mode in 2018**. New JVM work uses **Resilience4j**. .NET uses **Polly**. Do not start a new service on Hystrix.

---

## 9. Configuration that actually bites

- **Timeout longer than the user’s patience, shorter than the dependency’s worst legitimate p99.** If the dependency’s timeout is 60s and yours is 60s, you still pin threads for a minute. The breaker cannot trip until those calls finish.
- **Open duration vs recovery time.** Match the likely repair (restart vs region failover). Offer **manual trip/reset** for ops (Fowler / Microsoft).
- **Concurrency.** The breaker itself must not become a global lock. Libraries use lock-free or striped counters; do not roll a synchronized singleton that serializes all traffic.
- **429 / Retry-After.** Treat throttling as a signal to open (or back off) rather than retry immediately — “accelerated circuit breaking.”
- **Serverless / cold start.** A burst of timeouts during scale-out can false-trip; raise `minimumNumberOfCalls` or ignore cold-start windows.
- **Event-driven paths.** Microsoft notes that brokers + DLQ often isolate failure without an HTTP-style breaker. You still want consumer **concurrency limits** (bulkhead) and **poison** handling. A breaker can still wrap the *side* HTTP call inside a consumer.

---

## 10. Observability (a silent open circuit is an outage you cannot see)

Log and metric every **state transition**. Alert on:

- `state = OPEN` (or open duration)
- failure rate and slow-call rate in the window
- not-permitted call count (traffic hitting an open breaker)
- fallback invocation rate
- bulkhead rejected count

Expose breaker state on health/actuator endpoints. Tie to **distributed traces** so “why was checkout degraded?” shows `circuit=open` on `fraudClient`, not a mysterious 503.

Ops should be able to **force open** (maintenance) and **force close** (false trip). Breaker flips are often the **earliest** warning of a deeper incident.

---

## 11. When to use it / when not to

**Use when:**

- You make remote calls that can fail or hang.
- A dependency outage would exhaust *your* threads or connections.
- You have a real fallback or can fail that feature without taking down the whole API.
- You need to protect SLOs from slow dependencies.

**Do not use when:**

- The resource is in-process (local map, local method) — overhead for no network.
- You are using it as a substitute for handling **business** exceptions.
- Transient faults are rare and a small retry policy is enough **and** the dependency is built for retries.
- Waiting for the open window would violate a hard latency SLO and you need a different architecture (queue, async, multi-region active-active).
- Platform already fails over at a layer that makes an extra app breaker redundant *and* you have no domain fallback to attach.

---

## 12. Mental model for interviews (one paragraph)

*Remote calls can hang and hold threads. If everyone keeps calling a sick service, the callers die too. A circuit breaker is a per-dependency state machine: Closed records failures; past a threshold it Opens and fails fast (or falls back); after a wait it Half-Opens and probes; success closes, failure reopens. It is not a retry. Combine timeout so failures are detected, bulkhead so one client cannot take all threads, retry only for transients and stop when the circuit is open. Hystrix is legacy; Resilience4j/Polly/mesh outlier detection are the current tools.*

---

## 13. Interview questions (5–6 year bar)

### Q1: Explain circuit breaker without the electrical metaphor first.

**Answer:** It is a proxy around a remote call that tracks recent outcomes. When the dependency looks unhealthy, the proxy **refuses to call it** and fails immediately (or serves fallback) so the caller does not block on timeouts and the dependency is not hammered. After a pause it allows a few test calls and resumes if they succeed.

### Q2: Closed / Open / Half-Open — what transitions?

**Answer:** Closed → Open when failure (or slow-call) rate in the window exceeds threshold (with a minimum sample). Open → Half-Open after `waitDuration`. Half-Open → Closed if probes succeed; Half-Open → Open if a probe fails. Never Closed → Half-Open.

### Q3: Why is a slow dependency worse than a crashed one?

**Answer:** Crash → fast errors, threads free. Slow → threads blocked until timeout. Thread pools and connection pools saturate; upstream services wait on you; the failure **cascades**. Breakers (and timeouts + bulkheads) exist largely for this case.

### Q4: Circuit breaker vs retry.

**Answer:** Retry: this *request* might work if I try again (transient). Breaker: this *dependency* is unsafe right now; stop trying. Use retry with backoff **inside** Closed, and **do not retry** `CallNotPermitted` / open-circuit errors.

### Q5: What is a bulkhead and why isn’t the breaker enough?

**Answer:** Breaker trips only after enough failures accumulate. Before that, concurrent slow calls can still exhaust the shared pool. Bulkhead caps concurrency **per dependency** so Payment slowness cannot steal all Order Service threads from Inventory.

### Q6: Should 404 trip the circuit?

**Answer:** Usually no. 404 is a business/miss result, not an outage. Record 5xx, timeouts, connection errors, often 429. Ignore domain exceptions. Mis-recording 4xx opens the circuit on legitimate traffic and **creates** an outage.

### Q7: One breaker for all outbound HTTP?

**Answer:** No. One unhealthy host/API would block unrelated calls. Scope by **dependency** (and sometimes by operation). Shard-aware: do not mix independent partitions into one failure counter.

### Q8: Hystrix vs Resilience4j vs Istio?

**Answer:** Hystrix is unmaintained; thread-pool-heavy. Resilience4j is the JVM default: decorators, sliding windows, slow-call trips, composable with retry/bulkhead, Micrometer. Istio ejects bad **pods** and limits connections; it does not implement “approve low-value orders without fraud.” Use both at different layers.

### Q9: How do you test a breaker?

**Answer:** Fault injection: force timeouts, 5xx, latency (Toxiproxy, Chaos Mesh, stub). Assert: after N failures, next calls fail fast without hitting the stub; after wait, probes pass; fallback invoked; metrics show OPEN. Also test that business 4xx does **not** open it.

### Q10: Fallback for payments?

**Answer:** You generally **cannot** pretend the charge succeeded. Fallback is “queue for retry,” “ask user to retry,” or “switch PSP.” Cached “approved” is a fraud and ledger bug.

### Q11: What is flapping and how do you stop it?

**Answer:** Rapid Open ↔ Closed because wait is too short, probe count is 1, or threshold is too sensitive. Increase open wait, require multiple half-open successes, raise minimum calls, add hysteresis (different open vs close thresholds if the library allows).

### Q12: Does a circuit breaker give you exactly-once or consistency?

**Answer:** No. It is a **liveness / isolation** tool. Data consistency is outbox, sagas, idempotency — different note. A breaker may cause **intentional** unavailability of a feature.

### Q13: Open circuit and the user retries — still a retry storm?

**Answer:** The *dependency* is protected. The *caller* still spends CPU on fast-fails. Rate-limit the API, return a clear “temporarily unavailable,” and backoff at the client/gateway so users do not refresh-hammer you.

### Q14: Can you circuit-break async / queue producers?

**Answer:** Yes — Fowler: the circuit can be “queue is full.” Same idea: stop accepting work that cannot be processed. Consumers still need timeouts on their own downstream calls.

### Q15: Name three metrics you would put on an on-call dashboard.

**Answer:** Breaker state (or open count) per dependency; failure/slow rate in the window; not-permitted / fallback rate. Optional: bulkhead rejections and client p99 vs timeout.

---

## 14. Further reading

- Michael Nygard — *Release It!* (original popularization)
- Martin Fowler — [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- Microsoft Learn — [Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) and [Retry pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)
- Microsoft — [.NET microservices: implement circuit breaker with Polly](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/implement-resilient-applications/implement-circuit-breaker-pattern)
- Resilience4j — [CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker)
- Istio — [Circuit breaking / outlier detection](https://istio.io/latest/docs/tasks/traffic-management/circuit-breaking/)
