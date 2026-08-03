# Database Interview Questions & Answers

> Interview prep covering DBMS fundamentals, storage, concurrency, indexing, SQL, query optimization, recovery, and distributed databases.

---

## Table of Contents

1. [General](#1-general)
2. [Storage Management](#2-storage-management)
3. [Concurrency Control](#3-concurrency-control)
4. [Access Methods](#4-access-methods)
5. [Operator Execution](#5-operator-execution)
6. [Query Planning and Optimization](#6-query-planning-and-optimization)
7. [Crash Recovery](#7-crash-recovery)
8. [Distributed Systems](#8-distributed-systems)
9. [SQL Related](#9-sql-related)
10. [Others](#10-others)

---

## 1. General

### What are the issues of traditional file-based systems that make DBMS a superior alternative?

**Problems with flat files / file-based systems:**

| Issue | Explanation |
|-------|-------------|
| **Data redundancy** | Same data stored in multiple files → wasted space, inconsistency |
| **Data inconsistency** | Updates in one file may not reflect in others |
| **Hard to access data** | Need to write new programs for every new query |
| **Data isolation** | Data scattered across formats/files; hard to combine |
| **Integrity problems** | Constraints (e.g. salary > 0) must be coded in every app |
| **Atomicity problems** | Partial updates on crash (transfer half-done) |
| **Concurrent access** | Multiple users can corrupt shared files |
| **Security** | Fine-grained access control is difficult |
| **No recovery** | Limited crash recovery / backup tools |

**DBMS advantages:** centralized control, ACID transactions, declarative SQL, concurrency control, recovery (WAL), security, integrity constraints, data independence, indexing & optimization.

---

### What are some examples of open source and commercial Relational DBMSs?

| Type | Examples |
|------|----------|
| **Open source RDBMS** | PostgreSQL, MySQL, MariaDB, SQLite, CockroachDB (source-available / open core variants), Firebird |
| **Commercial RDBMS** | Oracle Database, Microsoft SQL Server, IBM Db2, Amazon Aurora (managed, MySQL/Postgres compatible), SAP HANA, Azure SQL Database |

> Note: Some products blur lines (e.g. Aurora is AWS commercial service on open engines; Enterprise editions of Postgres vendors add paid features).

---

### How do you choose a database model?

Choose based on **data shape, access patterns, consistency needs, scale, and team skills**.

| Question | Prefer |
|----------|--------|
| Structured data, complex joins, strong consistency? | **Relational (SQL)** |
| Flexible / evolving schema, documents? | **Document (MongoDB, Couchbase)** |
| Key-value lookups at huge scale? | **Key-Value (Redis, DynamoDB)** |
| Social graphs, relationships-first? | **Graph (Neo4j, Amazon Neptune)** |
| Time-series metrics / IoT? | **Time-series (TimescaleDB, InfluxDB)** |
| Wide-column massive writes? | **Wide-column (Cassandra, HBase)** |
| Analytics / warehouse scans? | **Columnar (ClickHouse, BigQuery, Redshift)** |
| Multi-model needs? | PostgreSQL + extensions, or specialized polyglot setup |

Also weigh: ACID vs eventual consistency, ops complexity, cost, latency SLOs, and existing ecosystem (ORMs, tooling).

---

### What is ER modeling?

**ER (Entity–Relationship) modeling** is a conceptual design technique to model real-world data before physical tables.

**Components:**
- **Entity** — thing of interest (Employee, Order)
- **Attribute** — property (name, salary); can be simple/composite/multi-valued/derived
- **Relationship** — association (Employee *works_in* Department)
- **Cardinality** — 1:1, 1:N, M:N
- **Keys** — primary key uniquely identifies an entity instance
- **Weak entity** — depends on another entity for identity

**ER diagram → Relational schema:** entities become tables; relationships become FKs or junction tables; attributes become columns.

---

### What is NoSQL?

**NoSQL** (“Not Only SQL”) = non-relational / alternative data stores optimized for scale, flexibility, or specialized access patterns.

**Main families:**
1. **Document** — MongoDB, CouchDB
2. **Key-Value** — Redis, DynamoDB
3. **Wide-Column** — Cassandra, HBase
4. **Graph** — Neo4j, Neptune

**Typical traits:** flexible schemas, horizontal scaling, eventual consistency options, fewer joins, BASE-ish tradeoffs (vs strict ACID in classic RDBMS). Many modern NoSQL systems also offer strong consistency modes.

---

### What is ACID properties of transactions?

| Property | Meaning |
|----------|---------|
| **Atomicity** | All-or-nothing — commit fully or roll back fully |
| **Consistency** | Transaction takes DB from one valid state to another (constraints preserved) |
| **Isolation** | Concurrent transactions don’t see each other’s intermediate states (per isolation level) |
| **Durability** | Once committed, data survives crashes (via WAL / replication) |

Example: bank transfer debits A and credits B in one transaction — either both succeed or neither.

---

### What are the different levels of data abstraction?

Classic ANSI-SPARC / DBMS three levels:

| Level | Also called | What it hides |
|-------|-------------|---------------|
| **Physical** | Internal schema | How data is stored on disk (files, pages, indexes) |
| **Logical** | Conceptual schema | What data is stored and relationships (tables, types) — hides physical details |
| **View** | External schema | What end users/apps see — customized subsets of the logical schema |

**Data independence:**
- **Physical data independence** — change storage/indexes without changing logical schema
- **Logical data independence** — change logical schema without breaking all views/apps (harder)

---

## 2. Storage Management

### What is the difference between columnar and row-based databases?

| | **Row-based** | **Columnar** |
|--|---------------|--------------|
| Storage | Entire row together | Values of each column together |
| Best for | OLTP — insert/update/point lookups | OLAP — scans, aggregates on few columns |
| I/O | Reads whole row even if needing 1 column | Reads only needed columns |
| Compression | Moderate | Excellent (similar values adjacent) |
| Examples | PostgreSQL, MySQL InnoDB, Oracle (row heaps) | ClickHouse, Amazon Redshift, BigQuery, Snowflake; Postgres columnar extensions |

Hybrid systems exist (e.g. Oracle Hybrid Columnar Compression, SQL Server columnstore indexes).

---

### What are OLTP and OLAP and their differences?

| | **OLTP** | **OLAP** |
|--|----------|----------|
| Full form | Online Transaction Processing | Online Analytical Processing |
| Workload | Many short read/write transactions | Complex analytical queries |
| Ops | INSERT/UPDATE/DELETE + point SELECT | Aggregations, scans, joins over history |
| Data | Current operational data | Historical / consolidated |
| Normalize | Highly normalized | Often denormalized / star-snowflake |
| Latency | Milliseconds | Seconds to minutes OK |
| Examples | Banking app, e-commerce orders | Data warehouse, BI dashboards |

---

### What is normalization and de-normalization?

**Normalization** — organize tables to reduce redundancy and anomalies by applying normal forms (1NF → 2NF → 3NF → BCNF …).

**Benefits:** less duplicate data, fewer update anomalies, clearer integrity.  
**Cost:** more joins → potentially slower reads.

**Denormalization** — intentionally add redundancy (duplicate columns, summary tables) to speed reads / simplify queries.

**Used when:** read-heavy analytics, reporting, avoiding expensive joins; trade write complexity and consistency risk for read performance.

---

### What is Data Warehousing?

A **data warehouse** is a centralized repository optimized for analysis and reporting, typically fed from operational (OLTP) systems via ETL/ELT.

**Traits (Inmon / Kimball ideas):**
- Subject-oriented, integrated, time-variant, non-volatile
- Historical data, star/snowflake schemas, fact + dimension tables
- Separates analytics load from production OLTP

**Modern stack examples:** Snowflake, BigQuery, Redshift, Databricks; often with a lakehouse pattern.

---

## 3. Concurrency Control

### What are database locks and its types?

A **lock** restricts concurrent access to a data item so transactions don’t corrupt each other.

**By mode:**
| Lock | Allows |
|------|--------|
| **Shared (S)** | Multiple readers; no writers |
| **Exclusive (X)** | One writer; no other readers/writers |
| **Update (U)** (SQL Server) | Intent to upgrade to X; avoids some deadlocks |
| **Intent locks (IS/IX/SIX)** | Signal intent at higher granularity |

**By granularity:** row → page → table → database  
**By duration:** short (statement) vs long (transaction)  
**Optimistic vs pessimistic:** version checks vs locking upfront  
**Special:** advisory locks, predicate/gap locks (Postgres/InnoDB for phantoms)

---

### What is "lock escalation"?

**Lock escalation** = DBMS converts many fine-grained locks (e.g. thousands of row locks) into fewer coarser locks (page/table) to save lock-manager memory and CPU.

**Pros:** lower lock overhead  
**Cons:** reduces concurrency (blocks more sessions)

Engines differ (SQL Server escalates aggressively; Postgres typically does **not** escalate row→table the same way — it keeps row-level locks).

---

### What is "lock contention"?

**Lock contention** = multiple transactions compete for the same locks → waiting, queuing, timeouts, lower throughput.

**Causes:** hot rows (counters, inventory), long transactions, table locks, missing indexes (scan locks more rows), high isolation levels.

**Mitigations:** shorter transactions, proper indexes, row-level locking, optimistic concurrency, queue hot updates, lower isolation where safe, partitioning.

---

### What is "deadlock"?

**Deadlock** = two or more transactions each hold locks the others need → circular wait; none can proceed.

```
T1 locks Row A, wants Row B
T2 locks Row B, wants Row A
→ Deadlock
```

**DBMS response:** detect (wait-for graph) and **abort/victim** one transaction; app should retry.

**Prevention tips:** lock resources in consistent order; keep transactions short; avoid user interaction mid-transaction.

---

### What are isolation levels?

SQL standard isolation levels (weakest → strongest):

| Level | Dirty read | Non-repeatable read | Phantom read |
|-------|------------|---------------------|--------------|
| **Read Uncommitted** | Possible | Possible | Possible |
| **Read Committed** | No | Possible | Possible |
| **Repeatable Read** | No | No | Possible* |
| **Serializable** | No | No | No |

\*InnoDB Repeatable Read also prevents many phantoms via gap locks; Postgres RR uses snapshots (phantoms still possible in some definitions; Serializable uses SSI).

**Also common:** **Snapshot Isolation** (MVCC) — readers don’t block writers.

Higher isolation ⇒ stronger consistency, more locking/aborts, less concurrency.

```sql
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
BEGIN;
-- ...
COMMIT;
```

---

## 4. Access Methods

### What is hashing and its advantages and disadvantages?

**Hashing** maps a search key → bucket/slot via a hash function for O(1) average lookups.

**Used for:** hash indexes, hash joins, hash aggregation, partition distribution.

| Advantages | Disadvantages |
|------------|---------------|
| Very fast equality lookups (`WHERE id = ?`) | Poor for range queries (`BETWEEN`, `ORDER BY`) |
| Simple conceptually | Hash collisions / skew |
| Good for joins on equality | Dynamic growth (extendible/linear hashing) complexity |
| | Not ordered — no sorted scan |

**Static vs dynamic hashing:** fixed buckets vs growable directory/buckets.

---

### What is B+ tree and its advantages and disadvantages?

**B+ tree** = balanced multi-way search tree used by most RDBMS indexes.
- All actual keys/records in **leaf** nodes
- Leaves linked for ordered range scans
- Internal nodes store separators/guides only

| Advantages | Disadvantages |
|------------|---------------|
| Balanced → predictable logarithmic lookup | Extra I/O vs hash for pure equality in some cases |
| Excellent for **range** queries & sorting | Slightly more complex than hash |
| Supports equality + inequality | Page splits on inserts (write amplification) |
| High fanout → shallow trees | Hot spots on monotonically increasing keys (rightmost leaf) |

Default index type in PostgreSQL (`BTREE`) and InnoDB.

---

### What is the difference between clustered and non-clustered indexes?

| | **Clustered** | **Non-clustered (secondary)** |
|--|---------------|-------------------------------|
| Data order | Table rows stored in index key order | Separate structure pointing to rows |
| Count per table | Typically **one** | Many |
| Leaf contains | Full row (or primary data) | Key + pointer/row locator (heap TID or clustering key) |
| Best for | Range scans on PK / sort key | Alternate lookup paths |
| Examples | InnoDB PRIMARY KEY; SQL Server clustered index | Postgres indexes (heap + secondary); extra InnoDB indexes |

PostgreSQL: tables are heaps by default; `CLUSTER` can physically reorder once (not continuously maintained like InnoDB clustered PK).

---

## 5. Operator Execution

### What are correlated and non-correlated sub-queries?

**Non-correlated subquery** — independent of outer query; runs once.

```sql
SELECT name FROM employees
WHERE dept_id IN (SELECT id FROM departments WHERE location = 'Pune');
```

**Correlated subquery** — references outer query columns; conceptually re-executed per outer row.

```sql
SELECT e.name FROM employees e
WHERE e.salary > (
  SELECT AVG(salary) FROM employees e2
  WHERE e2.dept_id = e.dept_id
);
```

Optimizers may rewrite correlated subqueries as joins. Prefer joins/`EXISTS` when clearer/faster.

---

### What are different JOIN algorithms?

Physical algorithms the optimizer chooses:

| Algorithm | How it works | Best when |
|-----------|--------------|-----------|
| **Nested Loop Join** | For each outer row, probe inner | Outer small; inner indexed |
| **Block Nested Loop** | Outer buffered in blocks to cut I/O | Moderate sizes, no good hash/sort |
| **Index Nested Loop** | Inner probed via index | Selective joins with index |
| **Hash Join** | Build hash table on smaller side; probe with larger | Large equi-joins, unsorted |
| **Sort-Merge Join** | Sort both sides on join key; merge | Large joins; inputs already sorted/indexed |

Non-equi joins often limited to nested loop / merge variants. Check with `EXPLAIN (ANALYZE)`.

---

### What is stored procedure?

A **stored procedure** is a named routine stored in the database (SQL/PL) that can accept parameters, run procedural logic, and return results.

**Pros:** reuse business logic close to data, fewer round-trips, centralized security.  
**Cons:** harder versioning/testing, vendor lock-in, app-layer duplication debates.

```sql
-- PostgreSQL example (function)
CREATE OR REPLACE FUNCTION get_emp_count(d_id INT)
RETURNS INT AS $$
  SELECT COUNT(*)::INT FROM employees WHERE dept_id = d_id;
$$ LANGUAGE sql;
```

---

### What is a database trigger?

A **trigger** is procedural code that **automatically** runs on table events (`INSERT`/`UPDATE`/`DELETE`), BEFORE or AFTER (and INSTEAD OF on views).

**Uses:** auditing, derived columns, enforcing complex rules, replicating side effects.

**Caution:** hidden logic, hard to debug, can hurt performance and cause cascading surprises — prefer explicit app/service logic when possible.

```sql
CREATE TRIGGER trg_audit_salary
AFTER UPDATE OF salary ON employees
FOR EACH ROW
EXECUTE FUNCTION log_salary_change();
```

---

## 6. Query Planning and Optimization

### What is an execution plan?

An **execution plan** (query plan) is the DBMS’s chosen tree of operators to run a SQL statement: scans, seeks, joins, sorts, aggregates, etc., with estimated costs/rows.

```sql
EXPLAIN SELECT * FROM orders WHERE customer_id = 10;
EXPLAIN ANALYZE SELECT ...;  -- Postgres: actual timings/rows
```

Reading plans reveals missing indexes, bad join order, sequential scans, sorts/spills.

---

### What is query optimization?

**Query optimization** = choosing an efficient execution plan among alternatives.

**Steps (typical):**
1. Parse & validate SQL
2. Rewrite (view expansion, predicate pushdown, subquery unnesting)
3. Cost-based search (join order, access paths, join algorithms) using **statistics**
4. Produce plan → execute

Cost model uses table sizes, NDV (distinct values), histograms, index selectivity, memory (`work_mem`), etc.

---

### Mention a few best practices to improve query performance

1. **Index** columns used in `WHERE`, `JOIN`, `ORDER BY` (selectively)
2. Avoid `SELECT *` — fetch needed columns
3. Prefer **sargable** predicates (`col = ?` not `YEAR(col) = 2024`)
4. Keep statistics fresh (`ANALYZE`)
5. Use `EXISTS` / proper joins instead of inefficient correlated subqueries
6. Limit result sets (`LIMIT` / pagination); avoid large `OFFSET`
7. Prevent N+1 queries in apps (`JOIN` / batch / `select_related`)
8. Appropriate isolation; short transactions
9. Partition huge tables; archive cold data
10. Materialized views / summary tables for heavy aggregates
11. Review `EXPLAIN ANALYZE`; watch sorts spilling to disk
12. Normalize for writes; denormalize carefully for hot reads
13. Connection pooling; avoid ORM accidental cartesian products
14. Covering indexes for critical read paths

---

## 7. Crash Recovery

### What is Write-Ahead Log (WAL)?

**WAL** = all changes are written to a sequential **log** before corresponding data pages are flushed to disk.

**Why:**
- **Durability** — on crash, replay log to redo committed work
- **Atomicity** — undo uncommitted work using log records
- Sequential log writes are faster than random page writes

Used by PostgreSQL, InnoDB, SQL Server (transaction log), etc. Also enables point-in-time recovery and replication.

---

### What is a checkpoint?

A **checkpoint** is a point where the DBMS flushes dirty pages / syncs state so recovery knows it need not replay infinitely far.

- Marks a safe redo starting point in the WAL/log
- Shortens crash recovery time
- Happens periodically or under load/config thresholds

After crash: restore from last consistent state + **redo** from checkpoint through end of WAL + **undo** loser transactions.

---

## 8. Distributed Systems

### What is a distributed database?

A **distributed database** stores data across multiple physical nodes/locations but presents a unified logical database.

**Goals:** scalability, availability, geo-locality.  
**Challenges:** distributed transactions (2PC), consistency (CAP/PACELC tradeoffs), network partitions, clock skew, operational complexity.

Examples: CockroachDB, Google Spanner, Cassandra clusters, sharded Postgres (Citus), MongoDB replica sets/shards.

---

### What is database partitioning?

**Partitioning** = split one logical table into smaller physical pieces (**partitions**) by a key.

| Type | Rule |
|------|------|
| **Range** | `year < 2020`, `2020–2023`, … |
| **List** | region IN ('IN','US') |
| **Hash** | `hash(user_id) % N` |
| **Composite** | combine strategies |

**Benefits:** prune scans, manage retention (drop old partitions), parallel maintenance.  
Can be **within one server** (Postgres declarative partitioning) — not necessarily multi-node.

---

### What is database sharding?

**Sharding** = horizontal partitioning **across multiple database servers/nodes**.

Each shard holds a subset of rows (by user_id, tenant_id, etc.).

| Partitioning | Sharding |
|--------------|----------|
| Often one DB instance | Multiple instances |
| Admin/perf within DB | Scale-out architecture |
| Transparent SQL often | App or middleware routing common |

**Challenges:** cross-shard joins/transactions, rebalancing, hotspots, operational complexity.

---

## 9. SQL Related

### What are different types of SQL statements?

| Category | Purpose | Examples |
|----------|---------|----------|
| **DDL** | Define schema | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`* |
| **DML** | Manipulate data | `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `MERGE` |
| **DCL** | Control access | `GRANT`, `REVOKE` |
| **TCL** | Transactions | `COMMIT`, `ROLLBACK`, `SAVEPOINT` |

\*Some classify `TRUNCATE` as DDL (PostgreSQL/Oracle style — auto-commit, resets identity).

---

### What is the difference of DDL and DML?

| | **DDL** | **DML** |
|--|---------|---------|
| Full form | Data Definition Language | Data Manipulation Language |
| Acts on | Structure (tables, indexes, views) | Data rows |
| Typical | `CREATE TABLE`, `ALTER`, `DROP` | `INSERT`, `UPDATE`, `DELETE`, `SELECT` |
| Transaction | Often auto-commits (engine-dependent) | Fully transactional in most RDBMS |
| Rollback | May not be rollback-friendly | Usually rollbackable |

---

### What is the difference between scalar and aggregate functions?

| | **Scalar** | **Aggregate** |
|--|------------|---------------|
| Input | One value / row | Set of rows |
| Output | One value per row | One value per group (or whole set) |
| Examples | `UPPER()`, `LENGTH()`, `COALESCE()`, `ROUND()` | `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()` |
| Used with | Any SELECT list expression | `GROUP BY` / whole-table summary |

```sql
SELECT UPPER(name), LENGTH(name) FROM employees;           -- scalar
SELECT dept_id, AVG(salary) FROM employees GROUP BY dept_id; -- aggregate
```

---

### What is database VIEW?

A **VIEW** is a stored **named query** (virtual table). It doesn’t store data by default; runs the defining SQL when queried.

```sql
CREATE VIEW active_employees AS
SELECT id, name, dept_id FROM employees WHERE is_active = TRUE;

SELECT * FROM active_employees WHERE dept_id = 3;
```

**Uses:** security (hide columns), simplify complex joins, logical abstraction.

---

### What is the difference between VIEW and materialized VIEW?

| | **View** | **Materialized View** |
|--|----------|------------------------|
| Storage | No data stored (virtual) | Query result **stored** physically |
| Freshness | Always current | Stale until **refreshed** |
| Speed | As slow as underlying query | Fast reads; refresh cost |
| Use | Abstraction, security | Expensive aggregates/reports cache |

```sql
CREATE MATERIALIZED VIEW sales_monthly AS
SELECT date_trunc('month', sold_at) m, SUM(amount) FROM sales GROUP BY 1;

REFRESH MATERIALIZED VIEW sales_monthly;
```

---

### What is Common Table Expressions (CTE)?

A **CTE** (`WITH` clause) defines a temporary named result set for one statement — improves readability; can be recursive.

```sql
WITH dept_avg AS (
  SELECT dept_id, AVG(salary) AS avg_sal
  FROM employees
  GROUP BY dept_id
)
SELECT e.name, e.salary, d.avg_sal
FROM employees e
JOIN dept_avg d ON e.dept_id = d.dept_id
WHERE e.salary > d.avg_sal;

-- Recursive CTE (org hierarchy / graph walk)
WITH RECURSIVE subordinates AS (
  SELECT id, manager_id, name FROM employees WHERE id = 1
  UNION ALL
  SELECT e.id, e.manager_id, e.name
  FROM employees e
  JOIN subordinates s ON e.manager_id = s.id
)
SELECT * FROM subordinates;
```

---

## 10. Others

### What are the differences between DELETE and TRUNCATE commands?

| | **DELETE** | **TRUNCATE** |
|--|------------|--------------|
| Type | DML | DDL (mostly) |
| Scope | Selected rows (`WHERE`) | Entire table |
| Logging | Row-by-row (more log) | Minimal / page deallocate |
| WHERE | Yes | No |
| Triggers | Fires `DELETE` triggers | Usually does **not** |
| Rollback | Yes (in transaction) | Engine-dependent; often auto-commit |
| Identity/seq | Unchanged | Often reset |
| FK refs | Must respect FKs carefully | May fail if referenced |
| Speed | Slower on large tables | Much faster |

---

### What are the differences between PRIMARY KEY and FOREIGN KEY?

| | **PRIMARY KEY** | **FOREIGN KEY** |
|--|-----------------|-----------------|
| Purpose | Uniquely identify a row | Enforce referential integrity to another table |
| Nulls | NOT NULL (implicit) | Allowed unless also NOT NULL |
| Count | One PK per table | Many FKs possible |
| Uniqueness | Unique | Need not be unique |
| Example | `employees.id` | `employees.dept_id → departments.id` |

```sql
CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  dept_id INT REFERENCES departments(id)  -- FOREIGN KEY
);
```

---

### What is the difference between WHERE and HAVING clause?

| | **WHERE** | **HAVING** |
|--|-----------|------------|
| Filters | Rows **before** grouping | Groups **after** `GROUP BY` |
| Aggregates | Cannot use `SUM/AVG` directly | Can filter on aggregates |
| Timing | Pre-aggregation | Post-aggregation |

```sql
SELECT dept_id, AVG(salary) AS avg_sal
FROM employees
WHERE is_active = TRUE          -- filter rows first
GROUP BY dept_id
HAVING AVG(salary) > 50000;     -- filter groups
```

---

### What is functional dependency?

**Functional dependency (FD):** attribute set **X → Y** means each X value determines exactly one Y value.

Example: `employee_id → name, dept_id`  
If `employee_id` is known, `name` is determined.

FDs drive normalization (2NF, 3NF, BCNF): remove partial/transitive dependencies that cause anomalies.

---

### What are different normalization types?

| Form | Rule (interview-level) |
|------|------------------------|
| **1NF** | Atomic columns; no repeating groups |
| **2NF** | 1NF + no partial dependency on part of composite PK |
| **3NF** | 2NF + no transitive dependency (non-key → non-key) |
| **BCNF** | For every FD X → Y, X must be a superkey (stricter 3NF) |
| **4NF** | No non-trivial multivalued dependencies |
| **5NF** | Join dependency / lossless decomposition concerns |

Most OLTP designs aim for **3NF / BCNF**; warehouses often denormalize.

---

### What are different integrity rules?

| Rule | Meaning |
|------|---------|
| **Entity integrity** | Primary key unique and NOT NULL |
| **Referential integrity** | FK values must exist in parent (or be NULL) |
| **Domain integrity** | Values must match type/check/domain (e.g. age >= 0) |
| **User-defined integrity** | Business rules (triggers, CHECK, app logic) |
| **Key integrity** | UNIQUE constraints |

Actions on FK: `ON DELETE/UPDATE CASCADE | RESTRICT | SET NULL | SET DEFAULT`.

---

### What is DML Compiler?

In classic DBMS architecture, the **DML compiler** translates DML statements (SQL) into low-level instructions the query execution engine understands.

Pipeline sketch:
1. **Parser** — syntax check → parse tree  
2. **DML compiler / binder** — resolve names, types, permissions  
3. **Query optimizer** — choose plan  
4. **Code generator / executor** — run operators  

It works with the query evaluation engine and metadata (catalog/data dictionary).

---

### What is cursor?

A **cursor** is a DB object/pointer to iterate result rows one-by-one (procedural style), common in stored procedures.

```sql
-- Conceptual PL/pgSQL
DECLARE
  cur CURSOR FOR SELECT id, name FROM employees;
  r RECORD;
BEGIN
  OPEN cur;
  LOOP
    FETCH cur INTO r;
    EXIT WHEN NOT FOUND;
    -- process r
  END LOOP;
  CLOSE cur;
END;
```

**Pros:** row-by-row procedural control.  
**Cons:** usually **much slower** than set-based SQL — avoid in app code when a single SQL statement works.

---

### What is cardinality?

**Cardinality** has related meanings:

1. **Relationship cardinality (ER):** 1:1, 1:N, M:N — how many related instances  
2. **Column cardinality:** number of distinct values (NDV) — high vs low selectivity for indexes  
3. **Result cardinality:** estimated/actual number of rows a plan operator produces  

Optimizers rely heavily on cardinality estimates; bad stats ⇒ bad plans.

---

## Quick Cheat Sheet

| Topic | One-liner |
|-------|-----------|
| ACID | Atomic, Consistent, Isolated, Durable |
| Abstraction | Physical → Logical → View |
| OLTP vs OLAP | Transactions vs Analytics |
| Clustered index | Dictates physical row order (usually one) |
| WAL | Log first, then data pages |
| Checkpoint | Truncate recovery starting point |
| Shard | Horizontal split across servers |
| CTE | Named temp query via `WITH` |
| WHERE vs HAVING | Rows vs groups |
| Nested Loop / Hash / Merge | Main join algorithms |

---

*Sources: standard DBMS concepts (Silberschatz/Korth, CMU 15-445 style join algorithms), PostgreSQL/MySQL docs practices, SQL standard isolation levels.*
