# Amazon SQS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

These notes are aimed at day-to-day use. They are separate from the longer senior write-up in `SNS_SQS.md`.

---

## Fundamentals

#### 1. What is Amazon SQS?

**Answer:** SQS is a managed message queue. Producers send messages. Consumers pull them, process them, and delete them. The queue buffers work so the producer does not wait for the consumer and a traffic spike does not fall on the database all at once. You do not run brokers.

---

#### 2. When do you use a queue instead of calling the next service over HTTP?

**Answer:** Use a queue when the work can finish later, when you need retries and a backlog, or when the consumer is slower than the producer. Use HTTP when the user is waiting for the result in the same request. A queue does not make a workflow faster. It makes it more tolerant of failure and uneven load.

---

#### 3. What is the difference between Standard and FIFO queues?

**Answer:**

| | Standard | FIFO |
| --- | --- | --- |
| Delivery | At least once. Duplicates can happen. | Exactly-once processing within the deduplication window. |
| Order | Best effort. Not guaranteed. | Strict order inside one message group. |
| Throughput | Nearly unlimited. | Lower, unless you enable high-throughput FIFO and use many group ids. |

Pick Standard unless you need order or deduplication. Your consumer must be idempotent on Standard queues.

---

#### 4. What is a message made of?

**Answer:** A body (text, up to 1 MiB), optional message attributes, and system fields such as a message id and a receipt handle. SQS does not understand JSON. Your producer and consumer agree on the body format. Attributes are useful for filtering and routing metadata without parsing the body. Billing counts a message in 64 KB chunks, so a 1 MiB body is many billable requests, not one.

---

#### 5. What is the message lifecycle?

**Answer:**

1. `SendMessage` stores the message.
2. `ReceiveMessage` returns it and starts the **visibility timeout**. Other consumers do not see it.
3. The consumer processes it and calls `DeleteMessage` with the **receipt handle**.
4. If the consumer crashes or times out, the message becomes visible again and another consumer can take it.
5. If this happens too many times, a redrive policy can move it to a **dead-letter queue**.

Messages that are never deleted expire after the retention period (default 4 days, maximum 14 days).

---

#### 6. What is long polling, and why is it the default you should set?

**Answer:** Short polling returns immediately, often with an empty response, and you pay for the API call. Long polling (`WaitTimeSeconds` up to 20) holds the request open until a message arrives or the timer ends. Set it on the queue or on each receive call. Workers should use long polling so they are not spinning and so new messages are picked up quickly.

---

## Visibility, retries, and DLQs

#### 7. What is the visibility timeout, and how do you pick a value?

**Answer:** It is how long a received message stays hidden. Set it longer than the worst-case processing time. If it is shorter, a second worker gets the same message while the first is still working. A common starting point is a few times the normal processing time. The maximum is 12 hours. For Lambda event-source mappings, the timeout must be longer than the function timeout.

---

#### 8. What if processing sometimes takes longer than the visibility timeout?

**Answer:** Call `ChangeMessageVisibility` while you are still working (a heartbeat) to extend the timeout. Do not set a 12-hour timeout “just in case”. A crashed worker would hide the message for 12 hours. Heartbeats keep the timeout short for failures and long for healthy slow jobs.

---

#### 9. What is a dead-letter queue, and what is `maxReceiveCount`?

**Answer:** A DLQ is a second queue for messages that failed too many times. The source queue’s redrive policy names the DLQ and a **maxReceiveCount** (often 3 to 5). Each time a message is received and becomes visible again, the receive count goes up. When it passes the max, SQS moves it to the DLQ. The DLQ should be the same type as the source (Standard or FIFO). Alarm on DLQ depth. It should be near zero.

---

#### 10. What is a poison message?

**Answer:** A message your code can never process, such as invalid JSON or a payload that always throws. Without a DLQ it is received, crashes the worker, and returns forever. Catch parse errors, delete or let the redrive policy move the message, and log the message id. Do not catch the error and leave the message invisible until it retries silently with no log.

---

#### 11. How do you redrive messages after you fix the bug?

**Answer:** SQS can redrive from the DLQ back to the source queue in the console, CLI, or SDK (`StartMessageMoveTask`). Fix the consumer first, then move the messages. Watch the source queue and the error logs. Moving them before the fix just cycles them back into the DLQ.

---

#### 12. How do you make a consumer idempotent?

**Answer:** At-least-once delivery means a message can be processed twice. Give each message a business id (order id, event id). Before doing the side effect, write that id to DynamoDB with a conditional put, or use a unique constraint in the database. If the id is already completed, delete the message and return. Idempotency is application code. SQS Standard will not do it for you.

---

## FIFO

#### 13. What are `MessageGroupId` and `MessageDeduplicationId`?

**Answer:**

* **MessageGroupId** (required on FIFO): orders messages that share the id. Different groups are processed in parallel.
* **MessageDeduplicationId:** if the same id is sent again within 5 minutes, SQS accepts the send but does not deliver a duplicate. You can instead turn on content-based deduplication and let SQS hash the body.

Use a high-cardinality group id (user id, order id) when you want parallelism. One group id for the whole queue means one consumer at a time.

---

#### 14. What happens to later messages in a FIFO group if one message fails?

**Answer:** SQS will not deliver the next message in that **same** group to anyone until the failed message is deleted or moved to the DLQ. Other groups continue. A single poison message blocks one group, not the whole queue, as long as you used more than one group id. This is why a DLQ on a FIFO queue is not optional in production.

---

#### 15. When should you not use a FIFO queue?

**Answer:** When you do not need order, when throughput must be unbounded, or when the only reason is “duplicates sound scary”. Duplicates are handled with idempotency on a Standard queue, which is cheaper to operate and scales further. FIFO is for payments, inventory adjustments, and workflows where order per entity matters.

---

## Design and operations

#### 16. What is the claim-check pattern?

**Answer:** SQS messages have a size limit (1 MiB) and are billed in 64 KB chunks. SNS is smaller (256 KB). For a large file, upload the bytes to S3 and send only the bucket and key on the queue. The consumer reads S3. This also keeps one copy of the blob when several queues would otherwise each carry it.

---

#### 17. How does a delay work?

**Answer:** A **delay queue** hides every new message for a fixed number of seconds (up to 15 minutes). A per-message delay does the same for one send. Use it to wait for a database commit to be visible, or to retry later without a scheduler. It is not a cron. For “run at 18:00” use EventBridge Scheduler. FIFO queues support per-message group delays less often in designs. Check the queue type. Standard queues support delay seconds on send.

---

#### 18. What is a visibility timeout versus a delay?

**Answer:** Delay happens **before** the first receive. Visibility timeout happens **after** a receive. Both hide the message. Mixing them up leads to “the worker never sees new messages” (delay too high) or “two workers process the same message” (visibility too low).

---

#### 19. How do you scale consumers?

**Answer:** On Standard queues, add more pollers (more ECS tasks, more Lambda concurrency). They compete for messages. On FIFO, parallelism is capped by the number of in-flight **message groups**, not by how many tasks you run. Lambda’s SQS event source mapping scales concurrency based on queue depth, with a batch size you set. Reserved concurrency stops a flood of messages from taking down a database.

---

#### 20. What is batching?

**Answer:** `SendMessageBatch` and `ReceiveMessage` can handle up to 10 messages per API call. Batching cuts cost and raises throughput. The consumer must delete each one it finishes (`DeleteMessageBatch`) and must handle partial failures. With Lambda, report batch item failures so one bad message does not retry the whole batch.

---

#### 21. How do you secure a queue?

**Answer:** IAM on the producer and consumer roles: `sqs:SendMessage` for producers, `ReceiveMessage`, `DeleteMessage`, and `GetQueueAttributes` for consumers. A **queue policy** is required when another account or a service such as SNS or S3 must send to the queue. Encryption with SQS-managed keys (SSE-SQS) or KMS (SSE-KMS) protects the body at rest. Do not put secrets in the message if the consumer logs the body.

---

#### 22. What does the queue policy need for SNS fan-out?

**Answer:** The queue policy must allow `sqs:SendMessage` from the SNS topic ARN (`aws:SourceArn`). The topic subscription alone is not enough. If the policy is missing, the subscription is pending or messages are dropped, and the topic looks healthy. This is the most common SNS-to-SQS setup bug.

---

#### 23. Which metrics tell you the consumer is falling behind?

**Answer:** `ApproximateNumberOfMessagesVisible` (backlog), `ApproximateAgeOfOldestMessage` (how late you are), and `ApproximateNumberOfMessagesNotVisible` (in flight). Alarm on age, not only on depth. A queue of 100 messages that are an hour old is worse than 10,000 messages that are two seconds old. Also alarm on DLQ visible messages greater than zero.

---

## Scenarios

#### 24. Users double-click a button and two orders are created. The API sends one SQS message per click. What do you change?

**Answer:** Deduplicate at the API with an idempotency key the client sends, stored in DynamoDB, before you enqueue. If you use FIFO, a deduplication id equal to that key also helps for five minutes. The consumer should still treat the order id as idempotent. The queue cannot fix a producer that intentionally sends two different messages.

---

#### 25. After a deploy, every message is processed twice for a few minutes. Why?

**Answer:** Old and new workers overlapped, or in-flight messages became visible again because the old process was killed before it deleted them. Make processing idempotent and shut down cleanly: stop polling, finish or extend visibility, then exit. A visibility timeout shorter than processing makes this worse during deploys.

---

#### 26. Lambda times out at 30 seconds and the visibility timeout is 30 seconds. What goes wrong?

**Answer:** The function is killed at the same moment the message becomes visible. Another invocation starts while the first might still be finishing a write, or the message is received again and the failure count climbs. Set the visibility timeout to at least six times the function timeout when using the Lambda event source mapping, which is AWS’s guidance, so retries and the function do not overlap.

---

#### 27. You need strict order for updates to one account, and high parallelism across accounts. How do you configure FIFO?

**Answer:** One FIFO queue. `MessageGroupId` is the account id. Updates for one account stay in order. Different accounts are consumed in parallel. Use high-throughput FIFO if the account count and the send rate require it. Do not create one queue per account.

---

#### 28. A worker deletes the message and then crashes before saving the result. What is the outcome?

**Answer:** The message is gone and the work is lost. Delete only after the side effect commits. If the crash happens after the commit and before the delete, the message reappears and the idempotent consumer skips it. That is the safe direction. Deleting first is not.

---

#### 29. How would you connect an API to a slow thumbnail job?

**Answer:** The API stores the upload in S3, sends a message with the object key, and returns 202 with a job id. An ECS worker or Lambda consumes the queue, writes the thumbnail, and updates the job row. A DLQ catches bad images. The user polls the job id or gets a notification. The HTTP request does not wait for the thumbnail.

---

#### 30. What is a reasonable production setup for a Standard queue worker?

**Answer:** Long polling, visibility timeout above the worst-case handler, a DLQ with maxReceiveCount of about 5, SSE enabled, least-privilege IAM, producer and consumer in private subnets, alarms on oldest-message age and DLQ depth, and an idempotency key stored in the database. Redrive is documented so an on-call engineer can replay after a fix. Retention is long enough to survive a weekend incident (often 4 to 14 days).

---
