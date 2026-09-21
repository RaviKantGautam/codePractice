# Amazon RDS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon RDS?

**Answer:** RDS is a managed relational database. AWS runs the hardware, patching, backups, and failover for engines such as PostgreSQL, MySQL, MariaDB, SQL Server, and Oracle. You still design schemas, indexes, and SQL. You connect with the normal database port and driver. You do not SSH in and edit `postgresql.conf` on a box you own. You use parameter groups.

---

#### 2. When would you choose RDS instead of running the database on EC2?

**Answer:** Choose RDS unless you need a feature the managed service blocks (a specific extension, a custom build, or shell access to the data directory). RDS gives you Multi-AZ, automated backups, and patching. EC2 leaves all of that to you. For a typical backend, RDS or Aurora is the default. DynamoDB is the alternative when the access pattern is key-value at high scale and you do not need SQL joins.

---

#### 3. What is an instance class versus storage?

**Answer:** The **instance class** is CPU and memory (for example `db.m7g.large`). **Storage** is the disk: gp3, io1, or io2, with a size and IOPS. A slow query can be CPU, memory, or IOPS. Raising only the disk does not fix a query that needs a better index. Storage autoscaling can grow the disk when it is nearly full. It will not shrink it later.

---

#### 4. What is a DB subnet group, and why is the database private?

**Answer:** A subnet group is the set of subnets, in at least two AZs, where RDS may place the instance. Put it in **private** subnets. The application security group is allowed on the database port. The database should not have a public IP. A public RDS instance is a common breach finding, even with a password.

---

#### 5. How does the application authenticate?

**Answer:** A username and password from **Secrets Manager**, rotated, and read at startup. Some engines support **IAM database authentication** (short-lived tokens) so you do not store a password at all. The token is not a connection pool you can cache for hours. It expires. Do not put the master password in an environment variable in git.

---

#### 6. What are parameter groups and option groups?

**Answer:** A **parameter group** is the engine configuration (`max_connections`, logging, `work_mem`). An **option group** is for optional features, more relevant on Oracle and SQL Server. Changing a static parameter requires a reboot. Test parameter changes on a non-production instance. The default parameter group cannot be edited. Create your own and associate it.

---

## High availability and reads

#### 7. What is Multi-AZ?

**Answer:** RDS keeps a standby in another Availability Zone and replicates **synchronously**. You get one DNS endpoint. If the primary fails, RDS flips the DNS to the standby. Applications reconnect. They do not get a second writable database. Multi-AZ is for availability, not for scaling reads. The standby cannot be queried on classic RDS Multi-AZ (Aurora is different).

---

#### 8. What is a read replica, and how is it different from Multi-AZ?

**Answer:** A **read replica** is asynchronous. You read from its endpoint to scale read traffic. It can be in another region. It can be promoted to a standalone database. Replication lag means a read can miss a write that just committed. Multi-AZ is a standby you do not read. Use Multi-AZ for failover and replicas for read scale and for reporting queries that would hurt the writer.

---

#### 9. What should the application do during a failover?

**Answer:** Reconnect. The endpoint hostname stays the same, but the IP changes. Pools that cache the IP forever will keep calling the old primary and time out. Use a reasonably short DNS TTL behavior (the AWS drivers and RDS Proxy help), retry new connections, and do not cache the IP in your own code. In-flight transactions fail and must be retried if they are idempotent.

---

#### 10. What is RDS Proxy, and when do you need it?

**Answer:** RDS Proxy pools connections in front of RDS or Aurora. Use it when many short-lived clients (Lambda, spiky containers) would open more connections than the database allows. It also makes failover less painful because clients connect to the proxy. You do not need it for a single long-running service with a sane pool size. Pinning (session state) can reduce how much pooling you actually get. Avoid features that pin every connection if you adopted the proxy for scale.

---

#### 11. How do you scale writes?

**Answer:** RDS has one writer. You scale it up (bigger instance, more IOPS), improve queries, or split the application (sharding, a different store for some data). Read replicas do not take writes. Adding replicas does not raise write throughput. If write scale is the main problem, look at the schema and at Aurora, or at a design that does not send every write through one relational primary.

---

#### 12. What is storage autoscaling, and what is the catch?

**Answer:** When free space is low, RDS increases allocated storage. It prevents a full disk from taking the database down. It does not replace capacity planning, and you cannot shrink. A runaway log or a cartesian query that fills temp space can grow the bill. Alarm on free storage before autoscaling has to save you, and set a maximum storage cap.

---

## Backups and operations

#### 13. What is the difference between automated backups and a snapshot?

**Answer:** **Automated backups** enable point-in-time restore within the retention window (1 to 35 days). RDS restores to a **new** instance. A **snapshot** is a manual or copied backup you keep until you delete it. Both are stored in S3. Restoring always creates a new database. You do not roll the existing instance backward in place. Plan the cutover (rename, or change the app endpoint).

---

#### 14. What is point-in-time restore?

**Answer:** You pick a time inside the backup retention window. RDS replays logs onto the latest restorable backup and gives you a new instance at that second. Use it when someone drops a table and you need the data from five minutes before. The restore takes time. It is not instant undo on the live writer. Practice it. A backup you have never restored is unverified.

---

#### 15. How do you patch the engine with less surprise?

**Answer:** RDS uses a **maintenance window**. Minor versions can auto-apply if you allow them. Major versions are a planned upgrade with a restore test first. Multi-AZ reduces downtime for many patches because the standby is patched and then promoted, but you still get a short failover. Read the release notes for query-behavior changes. Do not upgrade production on a Friday because the window happened to be open.

---

#### 16. What CloudWatch metrics matter?

**Answer:** `CPUUtilization`, `FreeableMemory`, `DatabaseConnections`, `FreeStorageSpace`, `ReadLatency` and `WriteLatency`, `DiskQueueDepth`, and `ReplicaLag` if you have replicas. Alarm on connections near the max, low free storage, high replica lag, and CPU that is pegged. A dashboard of CPU alone misses a connection leak. Also enable Performance Insights or slow-query logs when you are hunting one bad statement.

---

#### 17. How do you find a slow query?

**Answer:** Turn on the slow query log or Performance Insights. Look at the statement, the wait (IO, lock, CPU), and the plan (`EXPLAIN`). The fix is usually an index, a query change, or less work per request, not a larger instance. RDS will not index your tables for you. A missing index on a foreign key is a common reason a delete or a join takes down the writer.

---

#### 18. What is enhanced monitoring versus Performance Insights?

**Answer:** **Enhanced monitoring** is OS-level metrics (processes, memory split) at a fine interval. **Performance Insights** is database load: which queries and waits. Use Performance Insights when the question is “which SQL”. Use Enhanced Monitoring when the question is “is the OS out of memory”. CloudWatch is the alarm layer for both.

---

#### 19. How do encryption and network security work?

**Answer:** Encryption at rest is a KMS key set at creation time. You cannot turn it off later. Snapshots of encrypted instances are encrypted. In transit, use the engine’s SSL mode and require it in the parameter group if the engine supports forcing SSL. Security groups limit who reaches the port. Encryption does not stop a stolen application credential. That is IAM auth, rotation, and least privilege inside the database (an app user that is not the master user).

---

#### 20. What is the master user, and should the app use it?

**Answer:** The master user is the admin created with the instance. The application should use a separate user that can only `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on its schema. Migrations run with a different credential. If the app is compromised, the blast radius stays inside that schema. RDS IAM policies control who can delete the instance. Database grants control who can read the tables. You need both.

---

## Scenarios

#### 21. The app reports “too many connections” after a scale-out. What do you change?

**Answer:** Each new task opened a pool. Total connections are pool size times task count, and RDS has a max tied to memory. Shrink the pool, put **RDS Proxy** in front, or stop scaling tasks without a connection budget. Raising `max_connections` on a small instance can make the database slower or crash it. Fix the math first.

---

#### 22. A report query on the primary makes the API slow. Where should it run?

**Answer:** On a **read replica**, with the report user pointed at the replica endpoint. Accept replication lag, or run the report off-peak. If the report must be exact and up to the second, it has to hit the primary and it must be cheap. A replica in another region is for disaster recovery and local reads, not for a transaction that just wrote to the primary.

---

#### 23. Multi-AZ is on, and the AZ fails. What do users see?

**Answer:** A burst of errors while DNS flips and pools reconnect, typically a minute or two, sometimes longer. Writes that were in flight roll back. The application should retry idempotent operations and refresh connections. If the app cached the IP, the outage lasts until the process restarts. After failover, confirm the new primary is the one clients use and that replicas are still replicating.

---

#### 24. Someone ran `DROP TABLE` in production. How do you recover?

**Answer:** Point-in-time restore to a new instance at a time before the drop. Copy the table back, or cut the application over if the damage is wide. You cannot undo the drop on the live instance from a backup in place. This is why migrations are reviewed, why the app user cannot `DROP`, and why you have tested restore. The longer you wait, the more new data you have to reconcile.

---

#### 25. How do you run a migration without a long lock?

**Answer:** Prefer additive changes: new columns nullable or with defaults the engine can add without a full rewrite, new tables, backfill in batches, then switch reads, then drop the old column later. Test on a copy restored from a snapshot. A single `ALTER` that rewrites a huge table will block traffic. Some engines and versions have online DDL. Know which one you are on before you run it in the maintenance window.

---

#### 26. Dev and prod share one RDS instance to save money. Why is that a bad idea?

**Answer:** A test migration, a load test, or a `DROP` hits production. Security groups and passwords get shared. Backups are mixed. Separate instances, or at least separate clusters, are the baseline. Sharing is how a staging deploy deletes a real table. The cost of a small dev instance is cheaper than that incident.

---

#### 27. How would you connect a private ECS service to RDS?

**Answer:** Both in private subnets. The task security group is allowed inbound on the RDS security group. The task reads the endpoint and the secret from Secrets Manager using its task role. Connection string uses SSL. No public IP on the database. If tasks run in several AZs, the subnet group already spans those AZs, so failover does not strand the network path.

---

#### 28. Replica lag is growing during a batch job. What is happening?

**Answer:** The primary is writing faster than the replica can apply, often because of a large transaction, missing indexes on the replica’s replay, or a replica that is too small. Reads from the replica are stale. Stop sending the batch to the primary all at once, or pause replica reads for that feature. Lag is not a reason to fail over. Failing over does not fix a heavy write load.

---

#### 29. What is a blue/green deployment on RDS?

**Answer:** RDS can create a staged copy (green) that replicates from the current database (blue). You upgrade or change parameters on green, test it, then switch over. The application endpoint can follow the switch. Use it for engine upgrades with a rehearsal. It is not a substitute for application-level compatibility tests. Old connections still need to reconnect at switchover.

---

#### 30. What would you monitor and test before you call an RDS setup production-ready?

**Answer:** Multi-AZ if the business cannot wait to restore from backup, private networking, encryption, a non-master app user, automated backups with a tested restore, alarms on CPU, connections, storage, and replica lag, a connection budget that matches max tasks, and slow-query logging. Know the failover and the restore steps well enough to run them without inventing them during the incident.

---
