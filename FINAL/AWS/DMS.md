# AWS DMS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

DMS here is **AWS Database Migration Service**, not a document-management product.

---

## Fundamentals

#### 1. What is AWS DMS?

**Answer:** DMS copies data from a **source** database to a **target** database. It can do a one-time load, ongoing replication (change data capture), or both. Typical uses are moving onto AWS, upgrading an engine, keeping a replica in another store, or feeding Redshift or S3. It is not a general application message bus. For that you still want SQS or Kafka.

---

#### 2. What are the main pieces?

**Answer:**

* **Source endpoint:** where data comes from (RDS, Aurora, a database on EC2, or an on-prem database over the network).
* **Target endpoint:** where data goes (RDS, Aurora, S3, Redshift, DynamoDB, and others).
* **Replication instance:** the compute that runs the task. It must reach both endpoints on their database ports.
* **Task:** the job that says full load, CDC, or both, plus table mappings and settings.

You can also run DMS Serverless so you do not size the replication instance yourself. The concepts are the same.

---

#### 3. What is full load versus CDC?

**Answer:**

* **Full load:** read the current tables and write them to the target. Good for a copy when the source can be quiet, or as the first step.
* **CDC (change data capture):** after the load, apply inserts, updates, and deletes as they happen, by reading the source’s log (binlog, WAL, and similar).
* **Full load plus CDC:** the usual migration. Load existing data, then catch up the changes that happened during the load, and stay in sync until cutover.

CDC needs the source logging configured correctly. A full load alone will miss every write that happens after it reads each table.

---

#### 4. What is AWS SCT, and how is it different from DMS?

**Answer:** The **Schema Conversion Tool** (and the newer conversion features in DMS) helps translate schema and code from one engine to another (Oracle to PostgreSQL, SQL Server to Aurora). DMS moves **data**. It can create target tables, but it will not redesign stored procedures and fix every incompatible type for you. Convert and review the schema first. Then migrate the data.

---

#### 5. When would you not use DMS?

**Answer:** When a native tool is better: RDS read replicas, Aurora cloning, or a simple `pg_dump` for a tiny database with downtime. When you need sub-second transactional coupling (DMS is asynchronous). When the source cannot enable the logging CDC requires and you cannot accept a full reload. And when the “migration” is really an event stream between microservices. That is application-level events, not a database log reader.

---

#### 6. What does “homogeneous” versus “heterogeneous” mean?

**Answer:** **Homogeneous:** same engine family, such as MySQL to Aurora MySQL, or PostgreSQL to PostgreSQL. **Heterogeneous:** different engines, such as Oracle to Aurora PostgreSQL. Heterogeneous migrations need schema conversion and careful type mapping (dates, numerics, empty strings versus nulls). Homogeneous is still not free. Collation, extensions, and sequences need a checklist.

---

## Running a task

#### 7. What must the replication instance be able to reach?

**Answer:** The source port and the target port, over the network path you actually have (VPC, VPC peering, VPN, or Direct Connect). Security groups must allow the replication instance. A task that fails immediately is often a security group, a subnet, or a DNS name that only resolves inside one network. The instance should sit in private subnets. You do not open the source database to the internet so DMS can reach it.

---

#### 8. What source settings does CDC usually require?

**Answer:** It depends on the engine, but the idea is stable: binary logging or logical replication turned on, a retention window long enough that DMS can stop and catch up, and a user that can read those logs. On MySQL, binlog retention and row-based logging matter. On PostgreSQL, logical replication slots matter, and an unused slot can fill the disk. Know the requirement for your engine before the migration weekend. A full load can succeed and CDC can fail if this was skipped.

---

#### 9. What are table mappings?

**Answer:** JSON that selects schemas and tables, renames them, and can filter columns. Use them so you do not copy a 2 TB audit table you do not need. Selection rules include tables. Transformation rules rename or drop columns. Start with an explicit include list, not “migrate the whole server” by accident.

---

#### 10. What is LOB handling, and why do people turn it down?

**Answer:** Large objects (text and binary columns) can be copied inline up to a size limit, or looked up one by one, which is slower. A low limit truncates data. A high limit slows the load. Know your largest values. Truncating a document column is a silent data bug if you do not validate. For a first pass, measure max lengths. Do not accept the default without looking.

---

#### 11. What are the task startup modes after a stop?

**Answer:** You can resume CDC from a checkpoint DMS stored, or reload tables. Resume is what you want after a brief failure if the source logs are still available. If the logs expired, resume cannot invent the missing changes. You reload those tables or take a fresh full load. This is why source log retention must cover the longest outage you will tolerate.

---

#### 12. How do you cut over an application with limited downtime?

**Answer:** Run full load plus CDC until the replication lag is small. Stop writes on the source (or put the app in read-only). Wait until lag is zero and a validation check matches. Point the application at the target. Keep the source available to fall back for a defined window, but do not write to both unless you have a plan for conflicts. DMS does not do multi-writer. Practice this on a staging pair before the real cutover.

---

## Validation, limits, and operations

#### 13. How do you know the target matches the source?

**Answer:** Turn on **validation** on the task where the engine pair supports it. DMS compares rows and reports mismatches. Also run your own checks: row counts, checksums on critical tables, and the business queries you care about (max id, sum of today’s payments). Validation does not prove stored procedures or application behavior. Run the app’s integration tests against the target before cutover.

---

#### 14. What are common data mismatches?

**Answer:** Character set and collation differences, `NULL` versus empty string, timestamp time zones, numeric precision, boolean representations, and sequences or identity columns that do not match the source’s next value. Heterogeneous migrations hit these hardest. A row count can match while a decimal column is rounded. Check a sample of real rows, not only counts.

---

#### 15. What happens to sequences and auto-increment keys?

**Answer:** DMS copies the values that exist in the rows. The target’s sequence or identity counter may still be behind the max id, so the next insert collides. After cutover, set the sequence to max(id) + 1 before the app writes. This is a classic first-hour production incident. Put it on the cutover checklist.

---

#### 16. Can DMS replicate DDL?

**Answer:** It can replicate some DDL on some engine pairs, and it will miss or mangle others. Do not assume `ALTER TABLE` on the source appears correctly on a heterogeneous target. Prefer a controlled schema change process during migration: freeze schema, or apply reviewed DDL on both sides. Surprise columns in the middle of CDC are how tasks error at midnight.

---

#### 17. What CloudWatch metrics matter?

**Answer:** `CDCLatencySource` and `CDCLatencyTarget` (how far behind), `FullLoadThroughputRowsTarget`, task status, and storage on the replication instance. Alarm when CDC latency climbs and stays high, and when the task stops. A task in “running” with growing latency is not healthy. Also watch the source: a PostgreSQL slot that DMS is not consuming will grow WAL and can fill the source disk.

---

#### 18. Why would the source database run out of disk during CDC?

**Answer:** On PostgreSQL, a logical replication slot retains WAL until DMS reads it. If the task is stopped or the replication instance is undersized, WAL piles up on the **source**. On MySQL, binlogs are retained for the window you set and can fill disk too. Monitor source disk and replication slot size. A migration tool should not be allowed to take down the database you are copying from.

---

#### 19. How do you size the replication instance?

**Answer:** More tables, larger transactions, and LOBs need more memory and CPU. A small instance falls behind and the lag never catches up. DMS Serverless removes the guess for many migrations. If you pick an instance, watch CPU, memory, and latency during a production-like load, not only during a quiet test. Storage on the replication instance holds logs and swap. Fill it and the task fails.

---

#### 20. How does IAM and networking security look?

**Answer:** Endpoints store credentials in Secrets Manager or in the endpoint config. Prefer secrets. The replication instance role needs access to that secret and, for S3 or Redshift targets, access to the bucket. Security groups are least privilege between the instance and the two databases. Encrypt traffic with SSL to the endpoints. The application role that will use the target later is separate from the DMS user, which often needs broader read on the source and write on the target.

---

## Scenarios

#### 21. Full load finished, CDC will not start, and the MySQL source uses statement-based binary logging. What is wrong?

**Answer:** CDC for MySQL wants **row-based** binlogs so DMS can see the row images. Statement-based logging is not a reliable source for this. Change the binlog format, make sure retention is long enough, and restart CDC. Also confirm the DMS user can read the binlog. The full load does not need any of this, which is why it succeeded.

---

#### 22. The task has been “running” for a day and lag is 14 hours. Can you cut over tonight?

**Answer:** Not until lag is near zero and stays there. Cutting over now loses 14 hours of writes or forces a long read-only window. Find why it is behind: instance too small, a huge transaction, network, or a table with LOB lookups. Fix that, let it catch up, then schedule cutover. A date on a calendar does not change replication lag.

---

#### 23. You are migrating PostgreSQL to Aurora PostgreSQL. Should you use DMS?

**Answer:** Often a native path is simpler: dump and restore, or logical replication, or Aurora’s own migration options, depending on size and downtime. DMS is justified when you want a managed full-load-plus-CDC path and a controlled cutover. It is still fine to use. Do not add it by habit for a 5 GB database you can restore in a maintenance window with `pg_dump`.

---

#### 24. The target is Redshift. What extra steps exist versus RDS?

**Answer:** DMS loads via S3 under the hood for Redshift targets, so the replication instance needs a role and a bucket path. Table design on Redshift (distribution and sort keys) is yours. DMS will not pick them well. After the load, set keys and run the warehouse’s maintenance expectations. CDC into Redshift is for feeding analytics, not for a second OLTP primary.

---

#### 25. A table has no primary key. What goes wrong in CDC?

**Answer:** Updates and deletes need a way to find the row on the target. Without a primary key or a declared unique key, DMS may mis-apply changes or refuse to replicate that table the way you expect. Add a key, or define the supplemental key DMS allows, before you trust CDC. Full load of a heap still works. Ongoing updates are the problem.

---

#### 26. How do you migrate only one schema and leave the rest?

**Answer:** Selection rules in the table mapping include that schema and exclude everything else. Test the task against a restored copy and read the table statistics to see what was copied. A default “all tables” task will copy scratch schemas, backups inside the database, and tables you forgot existed. Explicit include lists are the safe default.

---

#### 27. Writes continue on the source during full load. Will the target be consistent?

**Answer:** Only if CDC is on and you wait for it to catch up. A full load reads tables at different times, so the target is not one snapshot unless the source is frozen or CDC covers the gap. Do not point the app at the target at the end of the full load while CDC lag is non-zero and writers are still active. That is a split brain you created on purpose.

---

#### 28. How would you roll back a cutover that failed an hour later?

**Answer:** If the new target took writes, those writes are not on the old source. A simple DNS flip back loses them. The safe rollback is: stop writes, capture the delta from the target (or from application logs), and decide whether to reapply it to the source or fix forward. Plan this before cutover. “We will just point DNS back” is only valid if the target never accepted a write the source does not have.

---

#### 29. DMS is replicating into S3. What do you use the files for?

**Answer:** Parquet or CSV change files in a bucket, partitioned by time, for a data lake or for a later `COPY` into Redshift. This is a feed, not a database you can `SELECT` from. Schema changes still need a consumer that understands them. Set a lifecycle policy so CDC files do not grow forever, and make the folder layout something the analytics job can load idempotently.

---

#### 30. What belongs on a migration checklist for a production cutover?

**Answer:** Schema reviewed on the target, source logging and retention confirmed, task in full load plus CDC with lag near zero, validation or checksums passed, sequences reset, app integration tests pointed at the target, a read-only window agreed, a rollback plan that accounts for new writes, source disk alarms for logs or slots, and someone watching CDC latency during the freeze. After cutover, stop the task only when you are sure you will not fall back to replication. Leaving a slot running forever can still fill the old primary’s disk.

---
