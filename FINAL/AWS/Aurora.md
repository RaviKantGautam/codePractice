# Amazon Aurora — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon Aurora?

**Answer:** Aurora is a MySQL-compatible and PostgreSQL-compatible relational database built for AWS. Compute (the instances you connect to) is separate from a shared **storage** layer that replicates across three Availability Zones. It is still SQL. Your driver, schema, and most of your queries stay the same as MySQL or PostgreSQL.

---

#### 2. How is Aurora different from RDS for MySQL or PostgreSQL?

**Answer:**

| | RDS | Aurora |
| --- | --- | --- |
| Storage | An EBS volume on the instance | Shared cluster storage, replicated across three AZs |
| Replicas | Separate copy of the data, async | Replicas read the same storage. Failover is faster |
| Scaling storage | You allocate and grow a volume | Storage grows automatically up to a large cap |
| Failover | DNS flip to a standby volume | Promote a reader, often quicker |
| Cost | Often lower for small steady databases | Often higher, aimed at higher availability and read scale |

Use RDS when a standard managed engine is enough. Use Aurora when you want faster failover, more readers, or storage that grows without planning a volume.

---

#### 3. What is a cluster, a writer, and a reader?

**Answer:** An Aurora **cluster** has one **writer** instance and up to 15 **reader** instances sharing the storage. The **cluster endpoint** always points at the current writer. The **reader endpoint** load-balances read-only connections across readers. An **instance endpoint** pins you to one instance, which you use for debugging, not for the app’s normal write path.

---

#### 4. Why can readers be added without copying the whole database?

**Answer:** Readers use the same cluster storage volume. You are not waiting for a full physical copy the way a classic RDS replica must catch up from scratch. A new reader still has to start the engine and warm caches, so it is not instant, but it is much faster than copying terabytes of EBS. Replication lag is usually small because the storage layer, not a separate binlog apply on a second disk, is the source of truth. Lag can still exist. Do not assume a read-after-write on the reader endpoint is safe.

---

#### 5. What should the application connect to?

**Answer:** Writes and read-after-write transactions go to the **cluster endpoint**. Scalable read-only queries go to the **reader endpoint**. Do not hardcode an instance endpoint in application config, or a failover will leave you pointed at a reader that rejects writes. Use the DNS names Aurora gives you and reconnect on failure.

---

#### 6. What is Aurora Serverless v2?

**Answer:** The instance scales capacity up and down in fine steps (ACUs) with the load, instead of you picking a fixed size and leaving it. You set a minimum and a maximum. It still lives in a cluster with the same endpoints. Use it for spiky or unpredictable load. A steady high load can be cheaper on a provisioned instance you reserved. Serverless does not remove the need for indexes or a connection strategy.

---

## Failover, reads, and global

#### 7. What happens on writer failure?

**Answer:** Aurora promotes a reader to writer and moves the cluster endpoint. The old writer is replaced. Clients see dropped connections and must reconnect and retry. A reader in another AZ is the failover target, so you want at least one reader in a different AZ from the writer. A cluster with only a writer has nothing to promote until Aurora creates a new instance, which is slower. Production clusters should have a reader.

---

#### 8. How is read scale different from write scale?

**Answer:** Add **readers** to scale read queries. There is still **one writer**. Writes do not fan out across readers. If the writer is the bottleneck, you tune SQL, raise the writer size, or change the design. Pointing the ORM at the reader endpoint for every query, including ones that just wrote, causes stale reads and occasional “cannot execute INSERT in a read-only transaction” if a write is sent to a reader by mistake.

---

#### 9. What is the reader endpoint’s limitation?

**Answer:** It balances connections, not transactions, and it does not know which reader is least lagged or least busy in a deep way. A connection that stays open stays on the instance it landed on. It is not a query router for read-after-write. For “I just inserted and must read it”, use the writer. For reports and list endpoints that tolerate a short delay, use the reader endpoint.

---

#### 10. What is an Aurora Global Database?

**Answer:** One primary region writes. Up to five secondary regions replicate with typical lag under a second, for local reads and for disaster recovery. Secondaries are read-only until you **fail over** or detach them. Use it when users in another region need low-latency reads or the business requires a regional DR plan. It is not Multi-AZ. Multi-AZ is inside one region. Global is cross-region. You pay for storage and instances in each region.

---

#### 11. What is backtrack?

**Answer:** On Aurora MySQL, backtrack lets you rewind the cluster to a time in the recent past without restoring a new cluster from a snapshot. It is for undoing a bad write quickly. It is not a backup you can keep for months, and it is not available on every engine edition. Point-in-time restore still matters for older recovery points and for restoring without rewinding production in place. Rewinding production rewinds every write after that time. You will lose those commits.

---

#### 12. How do backups work if storage is already replicated across AZs?

**Answer:** AZ replication protects you from hardware and AZ loss. It does **not** protect you from a bad `DELETE` or a bad deploy, because that change is replicated too. Aurora still takes continuous backups and supports point-in-time restore to a new cluster. Set a retention window and test a restore. Replication is not a backup.

---

## Operations

#### 13. What is Aurora’s storage bill based on?

**Answer:** You pay for the storage you **use**, not a pre-allocated 1 TB volume, plus I/O on some configurations (or a different I/O-optimized pricing choice where I/O is included). A forgotten debug table still costs money. Storage grows automatically. Shrinking is not as simple as growing. Deletes may not return space immediately the way you expect. Watch the volume bytes metric.

---

#### 14. What CloudWatch metrics are specific enough to mention?

**Answer:** `CPUUtilization`, `DatabaseConnections`, `FreeableMemory`, `AuroraReplicaLag`, `Deadlocks`, and volume bytes. On Serverless v2, also watch ACU utilization and whether you are pinned at the maximum. Replica lag on Aurora is usually low. If it grows, a reader is struggling or a long transaction is holding things up. Alarm on lag, connections, and serverless capacity stuck at max.

---

#### 15. How do parameter groups work on Aurora?

**Answer:** There is a **cluster** parameter group (applies to the cluster, including some engine settings) and a **DB** parameter group (applies to instances). The split surprises people who expect one RDS-style group. A change to a static parameter still needs a reboot of the instances. Test on a clone. Aurora can **clone** a cluster quickly because the clone shares storage and copies on write. Clones are the right place to try a parameter or a migration.

---

#### 16. What is a clone, and when do you use one?

**Answer:** A clone is a new cluster that shares the source data pages and only stores differences. It is fast even for large databases. Use it for a migration rehearsal, a heavy analytical query, or a test of an upgrade, without loading the production writer. It is not a backup. If you delete the source, you need to understand which volumes you still depend on. Do not point production traffic at a clone you created for an experiment.

---

#### 17. What is Aurora’s relationship to RDS Proxy?

**Answer:** RDS Proxy works with Aurora and is still the right tool when Lambda or a large task fleet would exhaust connections. Aurora does not remove connection limits. Each instance has a max connections value tied to its size. Serverless v2 raises capacity as load grows, which raises the connection ceiling, but a thundering herd of new Lambdas can still arrive faster than scaling. Pool in the app or put a proxy in front.

---

#### 18. How do engine upgrades work?

**Answer:** You upgrade within the MySQL-compatible or PostgreSQL-compatible major version path AWS supports. Read the version’s behavior changes. Use a clone or a blue/green style rehearsal. In-place upgrades involve a restart. Readers and the writer need a plan so the application reconnects. Do not jump major versions because a notice said “available” without running your test suite against a restored or cloned copy.

---

#### 19. What SQL behavior is not identical to upstream MySQL or PostgreSQL?

**Answer:** Most application SQL works. Some extensions, some storage-engine tricks (MySQL), and some replication settings do not exist, because Aurora replaced the storage engine. Check the Aurora compatibility notes before you depend on a feature you used on EC2. If you need an exotic extension, you may be on RDS or on self-managed PostgreSQL instead.

---

#### 20. How should IAM and database users be set up?

**Answer:** Same idea as RDS. The app user is not the master user. Grants are limited to one schema. Passwords live in Secrets Manager, or you use IAM database authentication where it fits. Security groups allow only the app and the proxy. The cluster is in private subnets. Deleting a cluster is an IAM permission you do not give to the application role.

---

## Scenarios

#### 21. After a write, the next read from the reader endpoint sometimes misses the row. Is Aurora broken?

**Answer:** No. Readers can lag, even if the lag is usually small. Read-after-write must use the **cluster** (writer) endpoint. Use the reader endpoint for queries that can tolerate staleness. If the UI must show the row the user just saved, that read stays on the writer.

---

#### 22. Failover happened and writes fail with “read-only” for several minutes. What is the app doing wrong?

**Answer:** It is still connected to the old instance, or it cached the writer IP, or the connection pool is not discarding dead connections. The cluster endpoint now points at the new writer. Recreate connections on that error. RDS Proxy or a driver with failover support shortens this window. Retry the transaction if it is safe to retry.

---

#### 23. You expect a big sale for one hour and quiet traffic otherwise. How do you size the cluster?

**Answer:** Consider **Serverless v2** with a minimum that covers normal traffic and a maximum that covers the sale, plus at least one reader for failover. If you already know the peak, a provisioned writer sized for the sale is simpler and may cost less than a high serverless max you forget to lower. Load-test the failover and the connection count, not only the happy-path QPS.

---

#### 24. A reporting job is moved to the reader endpoint and the reader’s CPU stays at 100 percent, which slows failover capacity. What do you change?

**Answer:** Give the report its own reader and keep a separate reader for failover and user reads, or run the report on a **clone** so it cannot hurt the cluster. One reader at 100 percent CPU is a poor failover target. Aurora will still promote it if it is the only reader, and the new writer will be overloaded on minute one.

---

#### 25. Storage grew by 200 GB overnight and nobody added a feature. What do you look at?

**Answer:** A batch job writing logs into a table, a cartesian join creating temp data, binary columns, or a migration that copied a table and left the old one. Check volume bytes and the largest tables. Aurora will not alert you that a table is nonsense. It will bill the bytes. Drop or truncate only after you know the writer does not need the data, and remember PITR if you are wrong.

---

#### 26. How do you run a destructive migration with a way back?

**Answer:** Clone the cluster, run the migration and the app test suite against the clone, then run the real migration in a window with a recent restorable time noted. If it fails, point-in-time restore or backtrack (MySQL) is the path. Do not test by running the migration on production first. The clone is cheap compared with a bad `ALTER`.

---

#### 27. Multi-AZ RDS was “good enough”, and someone wants Aurora because it is newer. What do you ask?

**Answer:** What problem are we solving? Failover time, read scale, storage growth, or a global read region are real reasons. A small internal tool on a `db.t` instance is not one. Aurora costs more and has its own limits. Recommend it when those benefits show up in the requirements, and keep RDS when they do not.

---

#### 28. The reader endpoint has no readers behind it during a deploy that deleted the only reader. What happens to read traffic?

**Answer:** Reads through the reader endpoint fail or fall back poorly, and you also lost your fast failover target. Keep at least one reader. If you must replace it, add the new reader and wait until it is available before you delete the old one. Infrastructure changes to the cluster should be reviewed like application deploys.

---

#### 29. How would you design connection strings for a service that reads and writes?

**Answer:** Two datasources in the app: a writer pool on the cluster endpoint and a reader pool on the reader endpoint. The repository uses the writer for commands and for any query that must see its own write. The reader pool has a smaller statement timeout so a report cannot hold a connection all day. Both use SSL and the secret from Secrets Manager. Failover tests must show the writer pool recovers without a redeploy.

---

#### 30. What would you verify in a game-day test of Aurora?

**Answer:** Fail the writer and confirm the app reconnects to the cluster endpoint, writes succeed, and the time-to-recover matches what you told the business. Confirm a read-after-write path does not use the reader. Restore a point in time to a new cluster and run a query you know the answer to. Watch connections during the test so the recovery does not trip `max_connections`. Write down the steps. That document is the runbook.

---
