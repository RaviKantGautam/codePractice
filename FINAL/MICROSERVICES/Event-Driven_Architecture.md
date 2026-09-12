# Event-Driven Architecture in Microservices — Detailed Study

Starting reference: [Event-Driven Architecture walkthrough](https://youtu.be/hrvx8Nv9eQA?si=RtkY-eHFqTj48XYn)

This note is a mid-to-senior study of **event-driven architecture (EDA)** as it is actually used in microservice systems: what the term hides, which patterns are independent of each other, where consistency breaks, and how production teams keep writes, events, and workflows aligned.

---

## 1. Why microservices force this conversation

A monolith can wrap “place order, reserve stock, charge card, send email” in one database transaction. Microservices typically apply **Database per Service**: each service owns its data. That independence is the point — independent deploy, scale, and failure domains — but it destroys the single ACID transaction.

The remaining options are:

| Approach | What it gives you | Why teams reject it as the default |
| --- | --- | --- |
| Two-phase commit (2PC / XA) | Strong consistency across resources | Locks, coordinator availability, poor fit across heterogeneous DBs and brokers |
| Synchronous RPC chain | Immediate answers | Cascading latency, cascading failure, tight temporal coupling |
| Event-driven + eventual consistency | Loose coupling, independent scale, resilience to producer downtime | Dual-write bugs, duplicates, delayed reads, harder debugging |

EDA is not “use Kafka.” It is a **communication and consistency strategy**: services publish **facts about what already happened**, other services react asynchronously, and the system converges rather than locking.

Use synchronous calls when the caller **must** have an answer in the same request (login, price quote, “is this username taken?”). Use events when the work can complete later, many consumers need the same fact, or the producer should not know who cares.

---

## 2. What “event-driven” actually means

Martin Fowler’s 2017 note is still the best starting point: people say “event-driven” while meaning **four different patterns**. Mixing them is the usual reason a team later says “EDA was a disaster.”

| Pattern | What it is | Source of truth | Typical payload |
| --- | --- | --- | --- |
| **Event Notification** | Thin signal: “something changed” | Producer’s DB / API | ID + maybe a link |
| **Event-Carried State Transfer (ECST)** | Fat event so consumers never call back | Producer’s DB; consumers hold local copies | Entity snapshot or delta |
| **Event Sourcing** | Persist every state change as an immutable event | The event log itself | Domain facts used to rebuild state |
| **CQRS** | Separate write model from read model | Write store + derived read stores | Often fed by events, but CQRS does not require events |

You can (and usually should) use EDA **without** event sourcing. Publishing `OrderPlaced` while storing the current order row in Postgres is ordinary EDA. Event sourcing is a **persistence** choice. CQRS is a **model-split** choice. Treat them as independent knobs.

---

## 3. The four Fowler patterns in practice

### 3.1 Event Notification

The producer emits a small message: `Order 42 was placed`. Consumers that need details call the producer’s API.

**Gains:** tiny schemas, producer does not leak its full model, easy to start.

**Costs:** an N+1 callback storm (one event, N consumers hitting the producer), hidden coupling to the producer’s API, and a hard availability dependency — if the producer is down, consumers cannot act even though they “received the event.”

Fowler’s warning: notification is easy to overuse until a **logical business flow** is spread across many handlers and is no longer visible in any one program. Debugging then requires tracing a live system.

### 3.2 Event-Carried State Transfer

The event carries enough state that consumers can update a **local projection** and keep working if the producer is down.

Classic Kafka shape: a **log-compacted topic** keyed by entity ID. New consumers read from offset 0 and reconstruct “latest state per key.” A null payload (tombstone) means delete.

**Gains:** lower producer load, lower latency for consumers, resilience to producer outages.

**Costs:** larger events, schema pressure, stale copies, and **PII / GDPR** pain because the same customer record now lives in many services.

This is the default flavor for most microservice EDA: “replicate the facts we need, do not call back.”

### 3.3 Event Sourcing

Every change is recorded as an event. Current state is **derived by replay** (plus snapshots for performance). Fowler’s analogy: git. The commit log is primary; the working tree is derived.

**Gains:** audit trail, time travel, reconstruct “what did this account look like at 3pm?”, hypothetical replay.

**Costs:** schema evolution across all history, awkward replay when events triggered **external** side effects (emails, card charges), operational complexity of snapshots and projections. Do not adopt this because it sounds advanced. Adopt it when **history is the product** (ledgers, trading, compliance).

Event sourcing is **not** the same as ECST. In ECST the producer still has a current-state database and events are a **replication bus**. In event sourcing the log **is** the database.

### 3.4 CQRS (Command Query Responsibility Segregation)

Writes and reads use different models. Strictly, CQRS does not require events. In microservices it is almost always paired with them: the write side commits, emits events, and **read models** (search indexes, dashboards, denormalized views) subscribe and catch up.

Use CQRS when read shape, scale, or latency **differs sharply** from the write model. Do not use it as a default for every CRUD service; you pay for duplication and read lag.

---

## 4. Events vs commands (the most expensive vocabulary mistake)

| | Event | Command |
| --- | --- | --- |
| Tense | Past: `OrderPlaced` | Imperative: `PlaceOrder`, `ReserveCredit` |
| Intent | A fact that already happened | An instruction someone is expected to carry out |
| Consumers | Zero to many; producer should not care | Usually one responsible handler |
| Failure | Consumer failure does not un-happen the fact | Sender often cares about success / compensation |

A **passive-aggressive command** is an “event” like `ChargeCustomer` that the sender expects exactly one service to execute. That is a command. Put it on a command channel, an orchestrator, or an RPC. Keep the word **event** for facts with unknown or many consumers.

A useful envelope:

- **Command** — “please do X”
- **Event** — “X happened”
- **Query** — “what is the current state of X?”

Choreography is event-heavy. Orchestration is command-heavy (the coordinator tells participants what to do, then reacts to replies or domain events).

---

## 5. The dual-write problem (the quiet killer)

Whenever a service must **update its database and publish to a broker**, those are two independent systems. There is no honest 2PC between Postgres and Kafka that you want in a microservice estate.

Failure modes:

1. **DB commit succeeds, broker publish fails** → rest of the world never hears about a real state change.
2. **Broker publish succeeds, DB rolls back** → ghost events, orders that do not exist.
3. **In-memory retry after crash** → the event was only in RAM; it is gone.

Anti-patterns that only relocate the bug:

- Reverse the order (Kafka first, then DB).
- Wrap the Kafka call inside a DB transaction (the broker write is not part of that transaction).
- Retry from memory without durable storage of the intent to publish.

**Correct idea:** make the first write durable and **depend** the second write on it. If the first write never commits, the second never starts. If the first write commits, a relay retries the second until it succeeds.

Canonical solutions (Confluent / industry practice):

1. **Transactional Outbox** — write business row + outbox row in one DB transaction; relay publishes later.
2. **Event sourcing** — the event *is* the write; a relay publishes the already-committed event.
3. **Listen-to-yourself** — write the event to the log first; a consumer of that log updates the DB. Fast, but the DB is eventually consistent even for the writer’s own reads.

---

## 6. Transactional Outbox (publisher-side reliability)

### Mechanism

```
BEGIN
  UPDATE / INSERT business tables
  INSERT INTO outbox (id, aggregate_id, type, payload, occurred_at)
COMMIT

Relay (poller or CDC) → broker ACK → mark published / delete / archive
```

Because both writes share one database transaction, you cannot persist an order without also persisting the intent to announce it.

### Relay styles

| Style | How | When it fits |
| --- | --- | --- |
| **Polling worker** | `SELECT … WHERE published = false ORDER BY id` | Simple, enough for moderate volume |
| **CDC (Debezium, Cosmos change feed, Postgres logical replication)** | Tail WAL / binlog / change feed | Higher throughput, lower extra load on OLTP, lower publish lag |

CDC is the modern default at scale: the service never talks to Kafka in the request path. Publication is a **consequence of the commit**.

### What outbox does **not** give you

Outbox gives **no lost events relative to committed state**. The relay may publish the same row twice if it crashes after broker ACK and before marking the row. Downstream still sees **at-least-once** delivery. Exactly-once *effects* require **idempotent consumers** (inbox, unique keys, upserts).

Operational habits: unique `event_id`, key messages by `aggregate_id` for ordering, archive or delete processed rows, and do not put the outbox in a different database than the business tables.

---

## 7. Inbox / Idempotent Consumer (consumer-side reliability)

Brokers retry. Relays retry. Networks duplicate. Design every handler as if the same event will arrive twice.

**Inbox pattern (exactly-once effect):**

1. Receive message with stable `event_id`.
2. In one local transaction: insert `event_id` into an inbox / `processed_messages` table **and** apply business changes.
3. Unique constraint on `event_id` → second delivery is a no-op.
4. ACK the broker only after that commit.

If you ACK before the DB commit, a crash can lose the effect. If you commit without recording the ID, a retry can double-apply.

Idempotency is also a **business** property, not only a table:

- Prefer **upserts** and “set status = Shipped” over “increment shipped_count”.
- Use **idempotency keys** on money moves and external APIs.
- Ignore stale versions (event version / aggregate version) when updates can arrive out of order across partitions.

Outbox + Inbox together are the production answer to “we need exactly-once processing.” The network still delivers at-least-once; **effects** happen once.

---

## 8. Delivery guarantees (say them precisely)

| Guarantee | Meaning | Typical how |
| --- | --- | --- |
| **At-most-once** | May lose messages; no duplicates | Fire-and-forget, no retry |
| **At-least-once** | Will retry until success; duplicates possible | Outbox, consumer nack/retry, Kafka default |
| **Exactly-once (broker)** | Broker-level EOS (e.g. Kafka transactions) | Narrow; does not automatically make *your* DB writes exactly-once |
| **Exactly-once *effect*** | Processing twice does not change outcome | Inbox + idempotent handlers |

Interview-safe sentence: *Kafka (and most brokers) give at-least-once to the application. We implement exactly-once business effects with outbox on publish and idempotent consumers on consume.*

---

## 9. Saga: multi-service workflows without 2PC

Chris Richardson’s definition: a saga is a **sequence of local transactions**. Each step updates one service and publishes a message that triggers the next. If a later step fails a business rule, the saga runs **compensating transactions** for completed steps.

This exists because **Database per Service** made a single ACID transaction impossible. 2PC is usually rejected for availability and operational cost.

### Compensation is not rollback

Compensation is a **new business action**: release reservation, issue refund, send “order cancelled.” You cannot un-send an email. You cannot un-charge a card without a refund flow. Put **irreversible** steps last. Compensations themselves fail — they need retries, idempotency, DLQ, and human escalation.

Sagas also **lack isolation** (the “I” in ACID). Concurrent sagas can observe dirty intermediate states (order PENDING, credit reserved but order later rejected). Countermeasures (semantic locks, commutative updates, “pending” states, versioning) are part of the design, not optional polish.

### Choreography vs orchestration

```
Choreography (events drive the next step)
  Order Service --OrderCreated--> Customer Service --CreditReserved--> Order Service
  Inventory, notifications, analytics subscribe independently

Orchestration (coordinator drives commands)
  Client → Order Service → Saga orchestrator
    → ReserveCredit → reply
    → ReserveStock  → reply
    → Approve or compensate
```

| | Choreography | Orchestration |
| --- | --- | --- |
| Coupling | Services know event contracts, not each other | Orchestrator knows the workflow and service APIs |
| Visibility | Flow is not in one program; hard to see | Workflow is explicit code / state machine |
| Failure handling | Compensation scattered | Central policy, retries, timeouts |
| Adding a step | New consumer | Change coordinator |
| Best fit | Simple linear fan-out, 2–3 services, independent side effects | 4+ steps, branching, SLAs, audit, human gates |
| Typical tools | Kafka / RabbitMQ / SNS | Temporal, Camunda, Step Functions, custom orchestrator |

**2026 consensus:** choreography for simple and secondary reactions (email, analytics, search index). Orchestration for the core money/inventory workflow. Hybrid is normal: orchestrate checkout; choreograph “order confirmed” fan-out.

A client that starts a saga via `POST /orders` still needs an outcome channel: wait until complete (slow), poll `GET /orders/{id}`, or push (websocket / webhook) when `OrderApproved` / `OrderRejected` lands.

### Durable execution (Temporal-style)

Modern orchestrators persist workflow progress so a crash does not lose “we already charged the card.” That is the saga state machine as a product: retries, timers, compensation, and resume-after-restart without you reinventing it in Redis.

---

## 10. How the core data patterns fit together

They are **not alternatives**. They stack.

```
Database per Service
        │
        ├── local ACID is enough if the invariant lives in one service
        │
        ├── Outbox ──────── reliable “this happened” to the bus
        │
        ├── Saga ────────── coordinate multi-service business process
        │                     (each saga step should publish via outbox)
        │
        ├── CQRS ────────── different read shape / scale
        │
        └── Event Sourcing ─ when audit/replay is a first-class requirement
```

| Situation | Pattern |
| --- | --- |
| One service owns the whole invariant | Local transaction only |
| Local write must be announced reliably | Transactional Outbox |
| Workflow spans services and needs compensation | Saga |
| Reads need a different model or scale | CQRS |
| History, replay, and audit are the product | Event Sourcing |
| Strong consistency is mandatory and availability can be sacrificed | 2PC (rare; isolate that invariant) |
| Need a hold-then-confirm semantic (seats, funds) | TCC (Try / Confirm / Cancel) — stronger than plain saga, still not XA |

---

## 11. Brokers: pick the mental model, not the logo

| System | Mental model | Retention | Replay | Best at |
| --- | --- | --- | --- | --- |
| **Apache Kafka** | Distributed log, pull, partitions | Time/size (days to forever) | Native | High-throughput streams, ECST, many independent consumers, analytics |
| **RabbitMQ** | Smart broker, queues, push, ACK then gone | Until consumed (mostly) | Limited | Task queues, complex routing, low-latency commands |
| **Apache Pulsar** | Compute/storage split, streaming + queue subscriptions | Time/size + tiered storage | Native | Multi-tenant, geo, mix of queue + stream |
| **NATS / JetStream** | Lightweight messaging; JetStream adds persist | Configurable | JetStream | Low latency, cloud-native, edge |
| **SNS + SQS / EventBridge / Pub/Sub** | Cloud fan-out + per-consumer retry | Platform-specific | Partial (archives) | Managed cloud-native EDA |

**Kafka vs queue in one sentence:** Kafka keeps history so new consumer groups can catch up; a classic queue deletes after ACK. If several teams must independently consume `OrderPlaced` years of design later, you want a log. If you need “do this job once” with priority and fancy routing, you often want a queue.

Ordering: Kafka guarantees order **per partition**, not globally. Key by aggregate ID (`order_id`) so one entity’s events stay ordered. More partitions = more parallelism = weaker global order.

---

## 12. Event design, contracts, and schema evolution

An event is a **public API** that outlives the producer deploy. Treat breaking changes like an HTTP v2.

### Envelope

Standardize metadata so routers and tracers do not parse the payload. [CloudEvents](https://cloudevents.io/) is the usual spec: `id`, `source`, `type`, `specversion`, plus `time`, `subject`, `dataschema`. `source + id` must uniquely identify a distinct occurrence so consumers can deduplicate.

```json
{
  "specversion": "1.0",
  "type": "com.shop.order.placed",
  "source": "/orders",
  "id": "A234-1234-1234",
  "time": "2026-08-26T06:01:00Z",
  "datacontenttype": "application/json",
  "data": {
    "order_id": "42",
    "customer_id": "c-9",
    "total_cents": 9999,
    "currency": "INR"
  }
}
```

Also carry `traceparent` / correlation IDs, `causation_id` (which event caused this one), aggregate version, and tenant ID when needed.

### Payload rules of thumb

- Name events as **business facts**, not table-row dumps (`OrderPlaced`, not `OrdersInsert`).
- Prefer **integration events** that are stable and slim over leaking internal CDC of every column — or isolate CDC topics with ACLs so only the platform consumes them.
- Do not use events as RPC.
- Version explicitly. Additive optional fields are usually safe; renames and type changes are not.

### Registry and compatibility

Use a schema registry (Confluent, Apicurio, Glue) with Avro/Protobuf/JSON Schema. Confluent’s default **BACKWARD** means a consumer with the new schema can read the previous version — **upgrade consumers before producers**. **BACKWARD_TRANSITIVE** if you need to rewind across *all* historical versions. Dual-publish `v1` and `v2` during migrations when many consumers cannot move together.

Document events with **AsyncAPI**. Treat schema PRs like API PRs: owner, compatibility check in CI, deprecation window.

---

## 13. Failure modes unique to EDA

**Poison pill.** One malformed message stuck at a Kafka offset blocks that partition for the whole consumer group. Pattern: limited retries → delayed retry topic → **dead letter queue (DLQ)** → advance the offset. Never retry forever on the same offset.

**Consumer lag.** The gap between latest produced offset and the consumer. Alert before it becomes a product incident (stale inventory, late fraud checks).

**Head-of-line blocking.** Slow poison or slow handler stalls everything behind it on that partition. Isolate slow consumers; scale partitions; keep handlers short (offload heavy work).

**Event spaghetti.** Chains longer than ~3 hops, 30 services listening to 30 topics, nobody can answer “who depends on `OrderPlaced`?” Enforce owned contracts, ACLs, and an event catalog.

**Eventual consistency UX.** User saves a profile, refreshes, sees old data. Mitigations: return the write result from the command API (read-your-writes), show “updating…”, poll until the projection catches up, never lie that a saga finished before it has.

**GDPR / delete.** ECST copies PII everywhere. You need tombstones, retention, and a deletion saga — not only a `DELETE` on the source table.

---

## 14. Observability (EDA dies without it)

Synchronous stacks fail as HTTP 500s. Event-driven stacks fail as **silence**.

Minimum set:

- Propagate **OpenTelemetry** trace context in message headers; use **span links** when a consumer starts a new trace (batch, delayed processing).
- Metrics: produce rate, consume rate, **consumer lag**, handler latency, retry count, **DLQ depth**, outbox backlog age.
- Logs: `event_id`, `aggregate_id`, `saga_id`, `causation_id`.
- For orchestrated sagas: a UI or query for **workflow instance state** (Temporal, etc.).
- For choreography: correlation IDs plus a documented event graph (EventCatalog / AsyncAPI).

LinkedIn-scale Kafka is not “install Kafka.” The hard part is schema registry, lag, mirroring, and operational tooling around the log.

---

## 15. Consistency: pick per invariant, not per architecture

| Model | What it promises | Typical EDA use |
| --- | --- | --- |
| **Eventual** | Replicas converge if writes stop | Search, recommendations, email, most read models |
| **Causal / per-aggregate order** | Happens-before inside one entity | Partition by aggregate ID; event-sourced streams |
| **Strong (linearizable / serializable)** | One globally agreed order | Isolated money movement, unique inventory reservation |

Do not make the whole estate linearizable. Isolate the invariant that loses money or violates regulation (ledger, stock reservation) and let everything else lag.

---

## 16. Worked example: checkout

**Goal:** place order, reserve inventory, charge payment, notify shipping. If payment fails, release inventory.

**Recommended shape:**

1. `POST /orders` creates `Order(PENDING)` and an `OrderCreated` **outbox** row in one transaction.
2. **Orchestrated saga** (Temporal or equivalent) for reserve → charge → confirm. Commands to Inventory and Payment. Compensations: `ReleaseInventory`, `RefundPayment`. Irreversible “send gift email” last, or outside the saga.
3. On `OrderConfirmed`, **choreograph** fan-out: email, loyalty, analytics, search index — each with inbox/idempotency.
4. Client polls `GET /orders/{id}` or waits on a completion event.

Sketch of the atomic write:

```text
create_order():
  BEGIN
    insert Order(status=pending)
    insert Outbox(type=OrderCreated, key=order_id, payload=...)
  COMMIT
  return order_id   # saga not finished
```

Inventory handler:

```text
on ReserveInventory(command):
  BEGIN
    if command_id in inbox: COMMIT; return already_done
    reserve stock (or fail)
    insert inbox(command_id)
    insert outbox(InventoryReserved or InventoryRejected)
  COMMIT
```

This is the whole game: **local ACID + outbox + saga + inbox**. Not 2PC.

---

## 17. When not to use EDA

- The user must see a **synchronous, correct** result and the invariant fits in one service.
- The team cannot yet operate a broker (lag, DLQ, schema, replay).
- You are about to emit events as disguised RPC.
- You need event sourcing only because a blog post said so.
- The domain is a simple CRUD app with one writer and one reader.

A **distributed monolith** (many services, shared DB, or every call still synchronous) plus a Kafka cluster is the worst of both worlds.

---

## 18. Decision cheat sheet

```
Need other services to react to a fact?
  no  → keep it local
  yes → is the consumer set known and is this an instruction?
          yes → command / orchestrator / RPC
          no  → domain event

Must the write and the announcement never diverge?
  yes → Outbox (or event sourcing / listen-to-yourself)

Does the business process span services with undo?
  simple fan-out → choreography
  complex / money / branching → orchestration (saga)

Do reads look nothing like writes?
  yes → CQRS projections from events

Is history itself the system of record?
  yes → event sourcing
  no  → current-state DB + events as integration
```

**Default production stack for a typical backend:** current-state DB, transactional outbox (CDC if you can), Kafka (or cloud equivalent) for facts, idempotent consumers, orchestrated saga only for the hard workflow, CQRS only where reads demand it.

---

## 19. Interview questions (5–6 year bar)

### Q1: Explain event-driven architecture without saying “loosely coupled.”

**Answer:** Services commit their own data, then publish a durable fact that other services apply on their own clocks. Callers do not wait for every downstream effect. Correctness is “the system converges,” not “one transaction locked every resource.” You pay with delay, duplicates, and operational complexity around the bus.

### Q2: Event sourcing vs “we publish events to Kafka.”

**Answer:** Publishing events is integration. Event sourcing means the event log **is** the write model and current state is a projection. Most Kafka microservice systems are **not** event-sourced; they are notification or ECST on top of CRUD databases.

### Q3: Why is dual-write the default production bug?

**Answer:** DB commit and broker send are not atomic. Crash between them and you get silent omission or ghost events. Outbox (or CDC of the commit) is the fix; retries in memory are not.

### Q4: Does Kafka exactly-once mean my Order table cannot double-insert?

**Answer:** No. Broker EOS does not replace an inbox table or idempotent upserts in **your** database. End-to-end exactly-once *effect* is an application property.

### Q5: Choreography vs orchestration — pick one for checkout with payment and stock.

**Answer:** Orchestrate the core (stock + payment + order status) so compensation, timeouts, and “where is this order?” are visible. Choreograph notifications and analytics off `OrderConfirmed`. Pure choreography for money flows becomes an implicit state machine nobody owns.

### Q6: How do you guarantee order of events for one aggregate?

**Answer:** Same partition key (`order_id`). Kafka only orders within a partition. Cross-aggregate or cross-partition order is not guaranteed; design handlers to tolerate that or sequence through an orchestrator.

### Q7: A consumer throws on a bad JSON payload. What happens?

**Answer:** If it retries the same Kafka offset forever, the partition stalls (poison pill). After bounded retries, send to DLQ, commit/advance offset, alert, fix, replay from DLQ.

### Q8: How do you version `OrderPlaced` when you need a new required field?

**Answer:** That is a breaking change. Add `OrderPlaced.v2` or dual-publish; keep v1 until all consumers migrate. Schema registry compatibility mode should fail the producer’s CI. Do not silently break old consumers.

### Q9: Why might you choose RabbitMQ over Kafka for a piece of the system?

**Answer:** Command/task semantics, complex routing, competing consumers, low latency at moderate volume, and “message gone after ACK.” Use Kafka when multiple teams need durable replay of the same business facts.

### Q10: What is a compensating transaction, and what cannot be compensated?

**Answer:** A forward business action that semantically undoes a previous local commit (refund, release hold). Things that already affected the outside world (sent email, shipped parcel, some regulatory filings) need a different business process, not a pretend rollback. Design those steps last or out of band.

### Q11: How do you make `POST /orders` feel synchronous if fulfillment is a saga?

**Answer:** Return `202` + `order_id` quickly after the local persist, then poll, websocket, or webhook on terminal state. Optionally wait a short time for fast-path success, but do not hold the HTTP request for warehouse confirmation.

### Q12: CQRS read lag — user just wrote, GET still old. Fixes?

**Answer:** Read-your-writes from the write API; session stickiness to a caught-up replica; wait for a version token; UI that distinguishes “accepted” vs “projected.” Do not pretend CQRS is strongly consistent.

### Q13: Outbox polling vs Debezium?

**Answer:** Polling is simple and extra DB load. Debezium tails the WAL so publish tracks commits with less OLTP chatter and usually lower lag. Both still produce at-least-once to the broker.

### Q14: How do you test an event-driven flow?

**Answer:** Contract tests on schemas (consumer-driven or registry compatibility). Component tests with a real broker or Testcontainers. Saga tests for compensation paths. Replay a recorded log against a projection. Chaos: kill relay after commit, duplicate delivery, out-of-order events, poison messages.

### Q15: When is 2PC still on the table?

**Answer:** Same data center, homogeneous resources, short transactions, and an invariant that cannot be compensated (some financial cores). Even then, isolate it. Do not 2PC Postgres together with Kafka as your microservice standard.

---

## 20. Further reading (primary sources used for this note)

- Martin Fowler — [What do you mean by “Event-Driven”?](https://martinfowler.com/articles/201701-event-driven.html) (notification, ECST, event sourcing, CQRS)
- Chris Richardson — [Pattern: Saga](https://microservices.io/patterns/data/saga.html)
- Wade Waldron / Confluent — [Understanding the Dual-Write Problem](https://www.confluent.io/blog/dual-write-problem/)
- Oskar Dudycz — [Outbox, Inbox, and delivery guarantees](https://event-driven.io/en/outbox_inbox_patterns_and_delivery_guarantees_explained/)
- Microsoft Learn — [Transactional Outbox with Cosmos DB](https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos)
- CNCF — [CloudEvents](https://cloudevents.io/)
- Garcia-Molina & Salem (1987) — original Sagas paper (long-lived transactions + compensation)

Related local notes: `FINAL/MICROSERVICES/DISTRIBUTED_system.md` (CAP/PACELC, sync vs async, distributed monolith).
