# Amazon Redshift — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon Redshift?

**Answer:** Redshift is a managed **data warehouse**. It stores data in columns and runs analytical SQL over large scans and aggregations (reports, dashboards, historical metrics). It is not the database your API uses for “get this user by id”. That stays on RDS, Aurora, or DynamoDB. Redshift is where you copy data to ask big questions.

---

#### 2. Why not run analytics on the production RDS instance?

**Answer:** Analytical queries scan millions of rows and compete with user transactions for CPU and IO. They also want a different shape of data (facts and dimensions, not normalized OLTP tables). Copy the data out (DMS, zero-ETL, or an ETL job into S3 and then Redshift) and let the warehouse handle the scans. The production database keeps short transactions.

---

#### 3. What is columnar storage, in practical terms?

**Answer:** A row database stores all columns of a row together. Redshift stores each column separately. A query that sums `amount` and groups by `region` reads those columns, not the email and address columns. That is why wide tables with a few columns in the `SELECT` are fast compared with the same query on OLTP storage. It is a poor fit for “fetch one row by primary key and update three columns”.

---

#### 4. What are the main pieces of a provisioned cluster?

**Answer:** A **leader node** accepts queries, plans them, and returns results. **Compute nodes** store the data and run the scans in parallel. You pick a node type and a count. Clients connect only to the leader endpoint (SQL, port 5439, PostgreSQL-like protocol). You do not connect to compute nodes.

---

#### 5. What is Redshift Serverless?

**Answer:** You do not pick node counts. You set a workgroup and a namespace, and capacity scales with the queries, within limits you can cap. Use it when usage is spiky or the team does not want to size a cluster. A steady, heavy warehouse can be cheaper and more predictable on a provisioned cluster with reserved nodes. The SQL is the same idea either way.

---

#### 6. How does data usually get into Redshift?

**Answer:** **COPY** from S3 is the standard bulk path: files in Parquet or CSV in a bucket, then a `COPY` command that loads them in parallel. JDBC inserts of one row at a time are slow and are not how you load a warehouse. Application databases get there through an ETL job, AWS DMS, or a zero-ETL integration where AWS offers it for that source. The S3 bucket and the cluster role need IAM so `COPY` can read the files.

---

## Design that affects speed

#### 7. What is a distribution style?

**Answer:** How rows are spread across compute nodes.

* **KEY:** rows with the same key land on the same node. Use it on the join key so a big join is local.
* **EVEN:** round-robin. Use it when there is no obvious key.
* **ALL:** a full copy on every node. Use it only for small dimension tables that you join often.
* **AUTO:** Redshift chooses and can change as data grows. A reasonable default when you are starting.

A bad key (one value for most rows) creates skew: one node does all the work and the query is as slow as that node.

---

#### 8. What is a sort key?

**Answer:** The order data is stored in, so filters and range scans can skip blocks. A sort key on `order_date` helps “sales for last month”. It does not help “user by email” the way a relational index does. You typically sort by the columns you filter on most in time-based fact tables. Sort keys are not primary keys. Redshift will not enforce uniqueness unless you do.

---

#### 9. What is skew, and how do you notice it?

**Answer:** Skew means one node or one slice holds far more rows than the others, usually because the distribution key is uneven (a nullable column, or a status with one dominant value). That node runs out of disk or dominates query time. Check table skew in the console or system views. Redistribute on a higher-cardinality key, or use `EVEN` / `AUTO` if there is no good key.

---

#### 10. Why is `SELECT *` a bad habit here?

**Answer:** Columnar storage’s win disappears if you read every column. `SELECT *` also breaks consumers when someone adds a column, and it moves more data to the leader. List the columns the report needs. Same for dumping a huge result to a single client. Write the result to S3 with `UNLOAD` if a downstream job needs the file.

---

#### 11. What is `UNLOAD`?

**Answer:** The reverse of `COPY`. It writes a query’s result to S3 in parallel files. Use it for exports and for handing data to another system. Do not pull millions of rows through an application server. Unload to S3 and let that system read the files.

---

#### 12. What are materialized views used for?

**Answer:** They store the result of a heavy aggregation so dashboards do not recompute it on every refresh. You refresh them on a schedule or incrementally where supported. They go stale between refreshes. Say that out loud in an interview so you do not promise live numbers from a view that refreshes nightly.

---

## Workload, security, and operations

#### 13. What is WLM?

**Answer:** Workload management queues queries so a heavy report does not take every slot and block a short interactive query. You assign memory and concurrency to queues, sometimes by user group. Serverless has different capacity controls but the idea is the same: protect short queries from long ones. A single queue with default settings is why “the dashboard is fast until the nightly job starts”.

---

#### 14. What is concurrency scaling?

**Answer:** On provisioned clusters, Redshift can add transient capacity when query concurrency exceeds the main cluster. You pay for the extra usage. It helps bursty BI tools. It does not fix a query that is wrong or a cluster that is too small for the steady load. Watch the bill if every user refresh triggers it.

---

#### 15. How do snapshots and backups work?

**Answer:** Redshift takes automated snapshots and can copy them to another region. You can restore a snapshot to a new cluster. Snapshots are for disaster recovery and for “the load job corrupted tables”, not for point-in-time row recovery inside an API. The source of truth is still the operational database. You can reload the warehouse from S3 if the pipeline is reproducible, which is often the better recovery story.

---

#### 16. How do you secure a cluster?

**Answer:** Private subnets, no public endpoint unless you have a strong reason, security groups that allow 5439 only from the BI or ETL security group, encryption at rest with KMS, and SSL for clients. IAM roles attached to the cluster allow `COPY` and `UNLOAD` only on the buckets you name. Database users and groups limit who can query which schema. Do not share the admin password with every dashboard.

---

#### 17. What is Redshift Spectrum?

**Answer:** Spectrum (and related external-table features) queries data **in S3** without loading it all into local disks, using an external schema and a data catalog (AWS Glue). Use it for cold history or data-lake files you do not want to pay to store twice. Joins between local tables and S3 are possible and can be slower. It is not a cache. Partition the S3 data (by date) or Spectrum will scan far more than you think.

---

#### 18. What file format should a pipeline write for COPY?

**Answer:** **Parquet** (or ORC) with a sensible row group size, partitioned by date in the S3 prefix. CSV works and is worse: larger, no column pruning, more parse cost. Compress files. Many medium files load better than one giant file or millions of tiny ones. A prefix per day matches both `COPY` and lifecycle policies that expire raw data later.

---

#### 19. How is vacuum and maintenance different from a beginner’s mental model of Postgres?

**Answer:** Updates and deletes in a columnar warehouse leave unsorted or deleted space. Redshift runs automatic maintenance on current generations, but large loads still need a pipeline that loads in sort-key order and avoids constant single-row updates. The pattern is append-only facts, or batch merges, not an ORM saving one entity at a time. If you treat Redshift like Postgres OLTP, performance falls apart.

---

#### 20. What does “PostgreSQL compatible” not mean?

**Answer:** Drivers and simple SQL often work. Many Postgres features do not: you will not use it as the app’s transactional database, and some functions, indexes, and extensions are absent or different. Check the docs before you paste a Postgres query and assume the planner will behave the same. Distribution and sort keys have no equivalent in a typical app schema.

---

## Scenarios

#### 21. A nightly COPY is slow and one node is at 100 percent disk. What is a likely cause?

**Answer:** Distribution skew, or the table is sorted in a way that forces a huge redistribute. Look at skew, the `COPY` file layout (too few files so only some slices work), and whether the distribution key is nullable and mostly null. Fix the key or the file count. Adding a node helps only if the data can spread.

---

#### 22. Analysts run a join between a 500-million-row fact table and a 200-byte-per-row country table, and it is slow. What distribution do you try?

**Answer:** `DISTSTYLE ALL` on the small country table so each node can join locally, and a **KEY** distribution on the fact table’s join column if that key is even. If the fact table is distributed on a different key, the join ships rows across the network. `ALL` on a large table would waste disk. It is only for small dimensions.

---

#### 23. The product team wants the checkout API to read inventory from Redshift. What do you say?

**Answer:** No. Redshift is for analytics, with higher and less predictable latency, and it is not designed for per-request primary-key reads and updates. Inventory for checkout stays on the transactional store. Redshift can receive a copy for reporting. If they need a fast aggregate at checkout, compute it in the OLTP database or a cache, not with a warehouse query on the request path.

---

#### 24. How would you lay out an S3 prefix for daily order events that Redshift loads?

**Answer:** `s3://bucket/orders/year=2026/month=09/day=21/` with Parquet files, a few hundred megabytes each rather than one file or thousands of tiny files. The load job `COPY`s that prefix into a staging table, then inserts into the fact table inside a transaction, then the job records success so a rerun does not double-load. Idempotent loads matter. A retried job that appends the same day twice will double the revenue chart.

---

#### 25. Two dashboards disagree because one refreshed during the load. What do you change?

**Answer:** Load into a staging table and swap or insert in a transaction so readers see the old day or the new day, not half of both. Schedule dashboard refreshes after the load job’s success signal. A materialized view refreshed at the end of the load gives a stable number. Do not let BI tools query the staging table.

---

#### 26. How do you give an engineer read access without giving them the ability to drop tables?

**Answer:** A database group with `SELECT` on the reporting schema only. ETL uses a different user that can write that schema. IAM controls who can modify the cluster. Database grants control the SQL. The master user stays off the dashboards and off laptops. Rotate passwords through Secrets Manager.

---

#### 27. A query that used to take 10 seconds now takes 10 minutes after a large load. What do you look at?

**Answer:** Statistics are stale, the new data is badly skewed, the sort order is wrong for the filter, or WLM is queuing behind a new heavy query. Run the query plan, check skew, and see if automatic analyze has not kept up. Also check whether someone removed the date filter and is scanning all history. The warehouse did not “wear out”. The data or the SQL changed.

---

#### 28. When would you query S3 with Spectrum instead of COPY?

**Answer:** When the data is cold, huge, and rarely queried, and you can partition it so a query skips most prefixes. Loading it would blow the cluster’s disk for little benefit. When the same data is queried every hour by many users, `COPY` into local storage (or a materialized result) is faster and often cheaper than rescanning S3. Spectrum is a tool for the lake, not the default for the hot fact table.

---

#### 29. How does Redshift fit with DMS?

**Answer:** DMS can replicate from a transactional database into Redshift for a near-continuous feed. Full load plus CDC is the usual task. You still design distribution and sort keys on the target. DMS does not design the warehouse. A nightly batch `COPY` from S3 is simpler if the business can tolerate day-old data. Pick the latency requirement before you pick the tool.

---

#### 30. What would you set up before analysts are allowed onto a new cluster?

**Answer:** Private networking, encryption, a reporting schema, groups with select-only access, a load role scoped to the data bucket, a documented `COPY` path that is idempotent, a snapshot retention and a cross-region copy if the data cannot be rebuilt, WLM or serverless limits so one query cannot consume everything, and a short note that this is not the production OLTP database. Then load one subject area and validate totals against the source before you add more.

---
