# Amazon DynamoDB — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is DynamoDB?

**Answer:** DynamoDB is a managed NoSQL key-value and document database. You choose a **partition key** (and an optional **sort key**). It stores items as attributes, scales horizontally, and does not require a server or a schema migration for every new attribute. It is not a drop-in replacement for SQL. You design the keys around the queries you will run.

---

#### 2. When would you choose DynamoDB instead of RDS?

**Answer:** Choose DynamoDB when the access pattern is known and simple: get an item by id, query a user’s items in time order, or write at a high rate with predictable keys. Choose RDS or Aurora when you need ad-hoc SQL, joins, and strong relational constraints. If you cannot name the queries up front, a relational database is safer. DynamoDB punishes a design that “will add filters later”.

---

#### 3. What is a partition key and a sort key?

**Answer:** The **partition key** decides which partition stores the item. A good key spreads traffic. The **sort key** orders items that share a partition key, so you can `Query` a range (all orders for one customer, newest first). Together they are the primary key and must be unique. A table with only a partition key can store one item per key value.

---

#### 4. What is the difference between GetItem, Query, and Scan?

**Answer:**

* **GetItem:** one item by full primary key. Cheapest and fastest.
* **Query:** all items with one partition key, optional sort-key condition. This is the workhorse.
* **Scan:** reads the whole table or index and filters afterward. It gets slower and more expensive as data grows. A production request path should not Scan.

If the only way to answer a question is Scan, the keys or indexes are wrong.

---

#### 5. What is eventual consistency versus strong consistency?

**Answer:** By default, reads are **eventually consistent**: a read immediately after a write might still see the old item, and it costs half a strongly consistent read. A **strongly consistent** read returns the latest committed item and uses more capacity. Use strong reads when the next screen must show the write. Use eventual reads for feeds and caches. Transactions and conditional writes are how you protect correctness, not only the read mode.

---

#### 6. What is an item, and what are the size limits you should remember?

**Answer:** An item is a set of attributes, like a JSON object, up to **400 KB**. A partition key value is limited in size, and a query returns pages (1 MB per page) so you paginate with `LastEvaluatedKey`. Do not store a file in an item. Store the file in S3 and save the key. A hot item that everyone updates (a global counter) will throttle no matter how large the table is.

---

## Indexes and capacity

#### 7. What is a GSI?

**Answer:** A **global secondary index** has its own partition key and sort key, and its own throughput. You use it to query by a different attribute (email, status). GSIs are eventually consistent with the base table. They consume write capacity when the base item is written. Project only the attributes you will read (`KEYS_ONLY`, `INCLUDE`, or `ALL`). `ALL` is easy and costs more.

---

#### 8. What is an LSI, and why is it less common?

**Answer:** A **local secondary index** shares the base table’s partition key and uses a different sort key. It must be created with the table. It is strongly consistent if you request that. Most new designs use GSIs because they are not stuck with the same partition key. Mention LSIs so you can read an existing table. Prefer GSIs unless you have a reason.

---

#### 9. What is on-demand versus provisioned capacity?

**Answer:**

* **On-demand:** you pay per read and write. Capacity adapts. Good for unknown or spiky traffic and for most new tables.
* **Provisioned:** you set read and write capacity units and can add **auto scaling**. Cheaper when traffic is steady and high. A table that exceeds provisioned capacity throttles.

Start on-demand unless you have a measured baseline and a cost reason to provision. Switching modes is possible but not something you do every hour.

---

#### 10. What is a read capacity unit and a write capacity unit?

**Answer:** Roughly, one write unit is one write per second of a 1 KB item. One strongly consistent read unit is one read per second of a 4 KB item. Eventually consistent reads cost half of that. Bigger items cost more units. On-demand hides the arithmetic until the bill arrives. A 200 KB item is not “one read”. Check item size when a table is more expensive than you expected.

---

#### 11. What is a hot partition?

**Answer:** All items with the same partition key live on one partition, and each partition has a throughput ceiling. If one key (or one GSI key) gets a disproportionate share of traffic, that partition throttles while the rest of the table is idle. Fix the key so popular traffic spreads out (include a shard suffix only if you truly must and you can query all shards). A status attribute with only three values is a bad GSI partition key if everyone queries `STATUS = OPEN`.

---

#### 12. What are conditional writes?

**Answer:** A write that succeeds only if a condition is true, for example `attribute_not_exists(pk)` to create once, or `version = :expected` for optimistic locking. If the condition fails you get a conditional check exception and you retry or return a conflict. This is how you avoid lost updates without a traditional lock. It is the feature interviewers expect you to name for “two requests update the same item”.

---

## Streams, TTL, and safety

#### 13. What are DynamoDB Streams?

**Answer:** A time-ordered log of item changes (insert, update, delete) for about 24 hours. Lambda or another consumer reads the stream and reacts: update a search index, publish an event, or write an audit row. Records appear at least once. The consumer must be idempotent. Streams are not a queue you can replay next month. If you need longer retention, fan out to SQS, EventBridge, or S3 quickly.

---

#### 14. What is TTL?

**Answer:** A numeric attribute holding a Unix expiration time. DynamoDB deletes expired items in the background, usually within a couple of days of the time you set, not at that exact second. Do not use TTL as a precise timer. Use it for sessions, magic links, and any row that should not live forever. Expired items can still appear until deletion runs. Filter them in the application if that matters.

---

#### 15. What is a transaction?

**Answer:** `TransactWriteItems` and `TransactGetItems` apply several actions all-or-nothing, across items and tables, with a limit on how many actions and a higher capacity cost. Use them when two items must change together (debit and credit, order and inventory). They are not a reason to model a 15-table relational schema inside DynamoDB. If every request is a large transaction, the access pattern wants SQL.

---

#### 16. What is DAX?

**Answer:** DynamoDB Accelerator is a managed in-memory cache compatible with the DynamoDB API. It helps read-heavy items that are requested far more often than they change. It does not speed up writes, scans you should not be doing, or a hot partition’s write limit. Cache invalidation is mostly handled because DAX sits on the API, but a write-then-read consistency requirement still needs thought. Many apps do fine with on-demand DynamoDB and no DAX.

---

#### 17. What is point-in-time recovery?

**Answer:** PITR continuously backs up the table so you can restore to a second-level timestamp within the last 35 days, into a **new** table. Turn it on for production. It does not undo a bug in place. You restore, then copy what you need back. On-demand backups are the snapshots you keep on purpose. TTL deletes and application bugs are both reasons you want this on before the incident.

---

#### 18. What are global tables?

**Answer:** Multi-region, multi-active replication. An item written in one region appears in the others. Use them when users in two regions must read and write locally. Conflict resolution is last-writer-wins at the item level, so design writes so two regions do not blindly edit the same item. Global tables cost more and make IAM and streams slightly more interesting. They are not a backup.

---

#### 19. How do you secure a table?

**Answer:** IAM on the application role: `GetItem`, `PutItem`, `Query`, and `UpdateItem` on that table ARN and on the index ARNs (`/index/*`). Do not grant `dynamodb:*` on `*`. Encryption at rest is on by default. VPC endpoints keep traffic off the public internet for clients inside a VPC. The fine-grained IAM conditions can restrict which keys a role may touch. Use that for multi-tenant tables if the key starts with the tenant id.

---

#### 20. What is single-table design, in one practical sentence?

**Answer:** Store several entity types in one table, with a partition key and sort key that encode the access pattern, so one query returns the items a screen needs. It can cut round trips. It is harder to read and easier to get wrong. For a 1–3 year interview, say you would start with a clear key design for the known queries, add GSIs for the other lookups, and only collapse entities into one table when the access pattern and the team’s comfort justify it.

---

## Scenarios

#### 21. `Query` by email is impossible because the partition key is `userId`. What do you add?

**Answer:** A GSI whose partition key is `email`. The application queries the index, not a Scan with a filter. Remember the GSI is eventually consistent and has its own throttling. If email can change, the update writes the base item and DynamoDB updates the index. Handle the case where two users try to claim one email with a conditional write or a separate uniqueness pattern.

---

#### 22. The table is on-demand and one customer’s partition returns throttling errors. How is that possible?

**Answer:** On-demand still isolates busy partitions. One key receiving a huge share of writes can exceed a partition’s limit even when the table’s overall traffic is fine. Spread the key, queue the writes, or break a hot item into shards. Raising account limits does not fix a single hot key.

---

#### 23. Two requests read a balance of 10 and both write 9. The balance is wrong. What was missing?

**Answer:** A **conditional write** on a version number or on the expected balance (`balance = 10`), or a transaction. A blind `PutItem` overwrites. Optimistic locking: read version 7, write “set balance = 9 only if version = 7”, and bump the version. On conflict, re-read and retry.

---

#### 24. A Lambda processes the stream and times out halfway. Will records be lost?

**Answer:** The stream iterator retries if the function fails, and records stay in the stream until they expire (about 24 hours). You can get duplicates. You can lose them only if the function succeeds in Lambda’s eyes without finishing the work, or if you fall behind until records expire. Make the function idempotent, alarm on iterator age, and set the batch size and parallelization so age stays low.

---

#### 25. You need to list “all open orders”, and status is a GSI partition key. Why will this hurt later?

**Answer:** Almost every open order shares one partition key value, `OPEN`. That GSI partition becomes hot and queries get more expensive as the business grows. Better models: query orders by customer (partition key `customerId`), or maintain a small number of shards, or store “open” as a sort-key prefix under a key you can query in bounded chunks. A status with low cardinality is a poor partition key.

---

#### 26. How do you migrate a relational table to DynamoDB without a big-bang rewrite?

**Answer:** Write new data to both stores (or use DynamoDB as the new write path and keep RDS until reads move). Backfill old items with a job that reads RDS and `BatchWriteItem`s into DynamoDB. Cut reads over per endpoint once the keys support that endpoint. Do not try to mirror every SQL report. Reports may stay on RDS or move to a warehouse. Verify item counts and a sample of keys before you stop the old path.

---

#### 27. The item you need would be 2 MB. What do you change?

**Answer:** Put the blob in **S3** and store the bucket, key, and metadata in DynamoDB. If the large piece is many attributes you always fetch together, split entities so the hot path stays small. The 400 KB limit is hard. Compression rarely saves a design that is storing documents that belong in S3.

---

#### 28. How do you paginate a Query for an API?

**Answer:** DynamoDB returns `LastEvaluatedKey` when more items match. Send it back as the next request’s `ExclusiveStartKey`. Encode it opaquely in the API’s page token. Do not use an offset. Limit the page size. A FilterExpression is applied **after** the limit is read, so a page can come back empty even when more matches exist. Loop until you fill the page or the key is absent, or filter in the key design so you do not rely on FilterExpression.

---

#### 29. What do you alarm on?

**Answer:** `ThrottledRequests`, `SystemErrors`, consumed capacity if you are provisioned, and stream `IteratorAge` if you have a stream. User-facing 500s caused by throttling should page someone. A table with PITR off in production is a review comment, not a metric. Cost alarms matter on on-demand tables because a Scan bug can spend real money.

---

#### 30. How would you model “orders for a customer, newest first, get one order by id”?

**Answer:** Table partition key `customerId`, sort key `orderId` or an `orderDate#orderId` if the main list is by time. `Query` the customer id for the list, with a descending scan and a limit. Get one order with the customer id plus the sort key if the client has both. If the API only has `orderId`, add a GSI with partition key `orderId`. Use a conditional write on create so a retry does not duplicate the order. That is enough for an interview. You do not need a single-table diagram unless the interviewer pushes.

---
