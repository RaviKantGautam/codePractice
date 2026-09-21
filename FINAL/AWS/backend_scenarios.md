# Backend engineer scenarios — AWS

Scenario questions for a backend and cloud software engineer with 1–3 years of experience. Each one is a situation you would actually hit: an API, a worker, a database, or a deploy. The single-service notes stay in their own files. Use this file to practice explaining a design or an incident out loud.

---

## APIs and request paths

#### 1. Checkout must return in under a second, but charging the card and sending email can take longer and sometimes fail. How do you split the work?

**Answer:** The API writes the order as `PENDING` in RDS or Aurora and returns **202** with an order id. It publishes one event (SNS or EventBridge) or sends one SQS message. A worker charges the card and updates the row. Email is another consumer of the same event, with its own queue, so a mail outage does not block payment.

Do not call the card provider and the mail provider inside the user request. API Gateway will cut the call off at 29 seconds, and a slow dependency becomes a user-facing 504. The client polls `GET /orders/{id}` or receives a later notification. The worker is idempotent on `orderId`, because the queue can deliver twice.

---

#### 2. A partner uploads a 200 MB CSV through your public API. API Gateway returns 413 and Lambda never runs. What do you change?

**Answer:** Stop sending the file through API Gateway and Lambda. `POST /uploads` checks the caller, then returns a **presigned S3 PUT** scoped to a prefix, a content type, and a short expiry. The browser or partner uploads straight to S3.

An S3 event (or EventBridge) drops a message on SQS with the object key. A worker on ECS or Lambda reads the object, validates rows, and writes results. The API never holds the bytes. The 10 MB API Gateway limit and the Lambda payload limit are why the old path failed.

---

#### 3. The same hostname must serve `/users` from ECS and `/reports` from Lambda. Users also need HTTPS. How do you route it?

**Answer:** One **ALB** on 443 with an ACM certificate. A listener rule sends `/users/*` to an IP target group of Fargate tasks. Another rule sends `/reports/*` to a Lambda target group, or you front reports with API Gateway on a path only if you need API keys and usage plans.

Security groups allow the app port only from the ALB. Tasks sit in private subnets. Health checks hit a real ready endpoint. If reports run for minutes, the Lambda rule is the wrong synchronous path: return 202 and run the report on a queue, because users will not wait on a function timeout.

---

#### 4. After you move the service from EC2 behind an ALB into private subnets, the app cannot reach Stripe or the public S3 API. RDS still works. Why?

**Answer:** Private subnets have no internet route. RDS works because it is inside the VPC. Stripe needs a **NAT gateway** in a public subnet and a route to it. S3 should not hairpin through NAT if you can avoid it: add an **S3 gateway endpoint** so object calls stay on the AWS network.

Security groups must allow outbound HTTPS. If the app uses an instance role, confirm the private route to the S3 endpoint and that the endpoint policy still allows the bucket. The NAT gateway is the piece people forget when “it worked on a public EC2”.

---

#### 5. Two ECS tasks write the same user’s session to local memory. Sticky sessions are off. Users get logged out at random. What is the backend fix?

**Answer:** Do not turn stickiness on and call it done. Put the session in **DynamoDB** or ElastiCache, keyed by the session id in a cookie, so any task can read it. Then any task can die and the ALB can keep spreading traffic.

If you already shipped stickiness, it hides the bug until a deploy drains the task the user was pinned to. Stateless tasks plus a shared store match Auto Scaling and rolling deploys. The cookie should be `HttpOnly` and `Secure`. The task role can read and write only that table.

---

#### 6. A Lambda behind API Gateway works in the console test and times out only when the mobile app calls it. The function is in a VPC so it can reach Aurora. What is going on?

**Answer:** The console test does not use the mobile client’s path, and a function in a VPC has **no internet** unless there is a NAT gateway. If the handler also calls a public auth or push API, that call hangs until the Lambda timeout. Aurora still works because it is private.

Check the log for the last line before the timeout. Either add a NAT (and accept the cost) for the public call, or move that call out of the VPC function. Also confirm the Aurora security group allows the Lambda security group, and that the API Gateway integration timeout (29 seconds) is not what the client actually hit.

---

## Queues, events, and workers

#### 7. Orders are published once. Inventory, billing, and email must all react, and billing is down for an hour. Inventory must keep moving. How do you wire it?

**Answer:** The order service publishes to an **SNS** topic or an **EventBridge** bus. Each consumer has its **own SQS queue** subscribed to that event, with raw delivery and a filter if the bus carries more than one event type. Billing’s queue grows while billing is down. Inventory’s queue does not.

Do not subscribe billing’s HTTP endpoint directly to SNS. A down service then depends on SNS retries and can drop the event. A dead-letter queue on each consumer queue catches poison messages. Consumers are idempotent on `orderId`.

---

#### 8. A worker deletes the SQS message, then crashes before it commits the database update. The next day the user’s request is missing. What was the bug, and what is the fix?

**Answer:** The message was acknowledged before the side effect. On the retry there is nothing left to process. **Commit first, then delete.** If the process dies after the commit and before the delete, the message comes back and the idempotent consumer sees the row and skips it. That duplicate is safe. The lost update is not.

Use a transaction or a conditional write keyed by the message’s business id. Set the visibility timeout longer than the handler so a slow commit is not processed twice at the same time.

---

#### 9. During a deploy, the old and new workers both process the same payment message. The customer is charged twice. The queue is Standard SQS. What do you change in the worker and in the deploy?

**Answer:** Standard queues are at-least-once, and a rolling deploy runs two copies on purpose. The charge must be **idempotent**: a conditional write “payment for order X already captured” before calling the provider, or the provider’s own idempotency key. Catch **SIGTERM**, stop polling, and finish or return the message before the task is killed.

Also set the visibility timeout above the worst-case charge call. FIFO does not replace this if two different messages were sent for one click. Deduplicate at the API with the client’s idempotency key before you enqueue.

---

#### 10. A FIFO queue is used “so we never get duplicates”, and throughput collapses as you add consumers. There is one `MessageGroupId` for every event. What did the team misunderstand?

**Answer:** FIFO order is per **message group**, and one group is consumed by one worker at a time. A single group id turns the queue into a global lock. Duplicates are prevented only inside the deduplication window, and only when the deduplication id repeats. It is not a general exactly-once bus.

Use the entity id (account, order) as the group id so different users run in parallel, and still make the consumer idempotent. If you do not need order, use a Standard queue and spend the effort on idempotency. Adding tasks will not help until the group cardinality goes up.

---

#### 11. You already have RabbitMQ on Amazon MQ because a Java service speaks JMS. A new Python service needs the same “order placed” fact. Do you point Python at the broker?

**Answer:** Not if you can avoid it. Keep the Java service on Amazon MQ. Have it publish an SNS or EventBridge event (or let a small bridge do it) so the Python service consumes **SQS**. New code then uses the AWS SDK, a DLQ, and autoscaling, and it does not need AMQP connection handling.

A second consumer on the broker is justified only when that team must use JMS or AMQP. Two styles in one company is normal. Do not make the broker the platform standard just because it was first.

---

#### 12. A nightly job must remind users 24 hours after signup, and the flow has a payment step that must roll back if the receipt fails. Where does Step Functions fit, and where does a queue fit?

**Answer:** The **signup workflow** (reserve, charge, send receipt, compensate on failure) is a Step Functions state machine. Retries and the undo path stay in one definition. The execution name can be the user id so two API calls do not start two charges.

The “remind me tomorrow” wait can be a **Wait** state if this workflow owns it, or EventBridge Scheduler if it is just a single notification with no other steps. A queue is the right tool when many independent services only need the “user signed up” fact and each will fail on its own. Do not put the whole company inside one state machine, and do not implement compensation by hoping every queue consumer succeeds.

---

## Data

#### 13. The API reads a row it just wrote and sometimes gets nothing. The read path uses the Aurora reader endpoint. Writes use the cluster endpoint. Is the database broken?

**Answer:** No. Readers can lag. **Read-after-write** belongs on the **cluster (writer) endpoint**. Use the reader endpoint for lists and reports that can be a second behind.

Fix the repository so a request that just inserted uses the writer for the following read in that same flow. Do not “fix” it by sending every query to the writer, or you will waste the readers and overload the primary. Tell the interviewer you would confirm replica lag in CloudWatch only to explain the delay, not because lag is a defect.

---

#### 14. You scale the ECS service from 4 tasks to 40 and Aurora starts refusing connections. CPU on the database is not high. What broke?

**Answer:** Each task has a connection pool. Forty tasks times a pool of 20 is 800 connections, and the instance has a max well below that. The app is waiting on connection slots, not on query CPU.

Shrink the pool, set a hard ceiling of pool size times **max** tasks, and put **RDS Proxy** in front if the clients are spiky or include Lambda. Raising `max_connections` on a small instance makes the database less stable. The Auto Scaling max has to be part of the connection budget, or the next scale-out does this again.

---

#### 15. Product wants “all open orders” as the main screen. Someone adds a DynamoDB GSI with partition key `status`. What do you push back on?

**Answer:** `OPEN` is one key. Every open order lands on one partition, and that partition will throttle as the table grows. The screen should query by a high-cardinality key you actually have, usually `customerId`, and filter status within that customer’s items.

If the business truly needs a global open queue for operators, shard it (`OPEN#0` … `OPEN#N`) or keep that workflow in Aurora where a status index is normal. A low-cardinality GSI is a design bug, not a capacity setting. On-demand mode will not save a hot partition.

---

#### 16. Two checkout requests read a DynamoDB balance of 100 and both write 90. You lost an update. What do you add?

**Answer:** A **conditional write**. Read a `version` (or the current balance) and update only if it still matches: set balance to 90 and version to N+1 where version is N. If the condition fails, re-read and retry, or return a conflict.

A blind `PutItem` always overwrites. Transactions help when two different items must move together (wallet and ledger). A condition on one item is enough for this bug. The same idea in RDS is a transaction with a row lock or an update that checks the old value.

---

#### 17. A reporting query on the primary Aurora instance makes checkout slow every afternoon. The report must not block orders. Where does it go?

**Answer:** Run it on a **reader**, or on an Aurora **clone** if it is heavy enough to make a reader a bad failover target. Checkout stays on the writer. If the report can be an hour old, build it in **Redshift** or from S3 and do not touch the transactional cluster at all.

A reader at 100 percent CPU is a poor node to promote in a failure. Give the report its own reader or a clone. Accept replica lag. If finance says the number must include the last second of writes, the query has to be cheap enough for the writer, which this one is not.

---

#### 18. You must move a PostgreSQL database to Aurora with little downtime. Developers suggest pointing DMS at production and cutting DNS when the full load finishes. What is missing?

**Answer:** A full load is not one snapshot. Tables are copied at different times, so the target is inconsistent unless **CDC** runs and catches up. Cut over only when CDC lag is near zero, the app is briefly read-only, validation or checksums match, and sequences are set to `max(id)+1`.

Also watch the source disk. A PostgreSQL replication slot that DMS is not reading will fill the **source** with WAL. Practice the cutover, and do not plan rollback as “flip DNS back” if the new database already took writes the old one does not have.

---

#### 19. The service stores invoice PDFs on the root EBS volume of an EC2 instance in an Auto Scaling group. A scale-in deletes the instance. Invoices are gone. What should have stored them?

**Answer:** **S3**, with the invoice id and the object key in RDS or DynamoDB. EBS root volumes are tied to one instance in one AZ, and an Auto Scaling group creates a new volume from the AMI every launch. `DeleteOnTermination` then deletes the only copy.

EFS would only be reasonable if several instances must append to the same files as a filesystem. PDFs are objects. Turn on versioning or replication if a bad deploy must not be able to erase them, and do not put the only copy on a disk the ASG is allowed to terminate.

---

## Deploy, identity, and incidents

#### 20. A deploy rolls out a new ECS image. For two minutes the ALB returns 502 and then recovers. The tasks look `RUNNING`. What is the backend bug?

**Answer:** The process is not listening yet, or it is being killed before in-flight requests finish. `RUNNING` only means the container started. The target group health check is what the ALB uses.

Set a health-check grace period, a health path that returns 200 only when the app can serve, and a **deregistration delay** so old tasks drain. In the app, trap **SIGTERM**, stop accepting new work, and exit before `stopTimeout`. A minimum healthy percent of 100 and a max of 200 keeps the old tasks until the new ones are healthy. The 502 is the ALB failing to get a response from a target that is already dying or not ready.

---

#### 21. Production must run the exact image that passed staging. The pipeline builds again on the prod branch and the digest is different. Why is that a problem, and what do you change?

**Answer:** A second build can pull a newer base image or dependency, so staging never tested the bytes you shipped. Build **once** in CodeBuild, tag the image with the git SHA, and pass that URI in the artifact to the staging deploy and the production deploy.

Turn on tag immutability in ECR. Do not deploy `latest`. A manual approval, if you want one, sits between the two deploy actions and does not trigger a rebuild. CodeDeploy or the ECS action only changes which task definition points at that digest.

---

#### 22. The app on Fargate can read S3 in dev and gets `AccessDenied` in prod. The bucket policy looks the same. The code uses the AWS SDK with no access keys. What do you compare?

**Answer:** The **task role** on the prod service, not the execution role (that role pulls the image and writes logs). Then the bucket policy, a KMS key policy if the bucket uses SSE-KMS, and a VPC endpoint policy. CloudTrail on the denied `GetObject` shows the principal that was actually used.

Dev and prod should not share a role. The prod role needs `s3:GetObject` on the prod bucket only. A missing `kms:Decrypt` looks like an S3 deny. The SDK without keys is correct. It is using the task role from the container credentials endpoint.

---

#### 23. Someone changed a security group in the console and the next CloudFormation deploy reverted it. The service broke again in the same way. How do you stop the loop?

**Answer:** The template is the source of truth. The console edit was **drift**. Put the required rule in the template and deploy that. Tell the team a hotfix in the console will be undone on the next pipeline run.

If the change was an emergency, the follow-up is the same day: update the template so prod matches what you intended. A stack policy and a change set stop a later deploy from replacing the database while you are editing the security group. CloudTrail shows who made the console call. That is useful. It does not replace the template.

---

#### 24. Users report 500s. CPU on the tasks is low. CloudWatch shows ALB target 5xx and Aurora `DatabaseConnections` at the max. What do you look at first, and what do you not do?

**Answer:** Look at the error the app logged (connection timeout or “too many connections”) and the recent deploy or scale-out. This is a **connection budget** problem, not a CPU problem. Do not scale the ECS service further. More tasks will open more connections and make it worse.

Mitigate by reducing tasks or pool size, failing fast, and adding RDS Proxy if you do not already have it. Page on 5xx and on connections near the max, not on CPU. Afterward, set Auto Scaling max to a number the database can serve.

---

#### 25. You need to know whether a human or the pipeline stopped the production tasks during an incident. Metrics only show that the desired count dropped. Where do you look?

**Answer:** **CloudTrail**, event names such as `UpdateService` or `StopTask`, in the cluster’s region. The user identity is either the pipeline role or a person’s assumed role, with a source IP and time. ECS events tell you the scheduler stopped tasks because a deploy or a health check asked it to. CloudTrail tells you who called the API.

CloudWatch explains the symptom (running count, 5xx). It does not name the caller. If the principal is `AWSServiceRoleForApplicationAutoScaling`, it was a scaling policy, not a person.

---

#### 26. A canary shifts 10 percent of Lambda traffic to the new version and the error alarm fires. Some clients still call the function’s version ARN from an old config. What do they see after CodeDeploy rolls back?

**Answer:** Callers that use the **alias** go back to the old version. Callers that hardcoded a version ARN stay on whatever version they pinned, including the bad one, because rollback only moves the alias.

Production configs, API Gateway integrations, and event source mappings should use the alias. The canary did its job for the 10 percent. The follow-up is to find the leftover version ARN in CloudTrail or in the client config and point it at the alias so the next rollback actually covers them.

---

## Design choices

#### 27. A new internal service is a Python HTTP API, a worker, and a relational database. Traffic is spiky and the team is small. What do you pick from this list, and what do you leave out?

**Answer:** **ECS on Fargate** for the API and the worker, behind an internal **ALB**. **Aurora PostgreSQL** or RDS for the data. **SQS** between the API and the worker. **ECR** for the image. **CloudWatch** alarms on 5xx, latency, queue age, and database connections. **CodePipeline** plus CodeBuild to build once and roll the service.

Leave out EKS unless you already run Kubernetes. Leave out Amazon MQ unless something speaks AMQP. Leave out Redshift until there is a reporting problem. Leave out a public API Gateway if the only callers are inside the VPC. Say why you skipped them. That is the senior part of a 1–3 year answer.

---

#### 28. The worker must process files that several tasks will read at the same time, and the files are a directory of small documents the code opens by path. S3 would force a rewrite. What storage do you use, and what do you watch?

**Answer:** **EFS**, with an access point per service so each task sees only its directory and writes as a known user. Mount targets in every AZ where Fargate runs. The task security group is allowed on port 2049.

Watch throughput and `PercentIOLimit`. A tree of tiny files is the workload EFS is worst at. If latency shows up, keep the shared durable files on EFS and local scratch on the task’s ephemeral disk. Do not put a database on this mount. If the rewrite to S3 is small, S3 is still the simpler long-term store.

---

#### 29. You have one week to add “email me when my report is ready” without taking down the report worker when the mail provider errors. How do you add it?

**Answer:** The worker already writes the report to S3 and marks the job row done. It also publishes a small “report ready” event. A **new** SQS queue, subscribed to that SNS topic or EventBridge rule, feeds a small mail sender. If the provider returns 500, only that queue backs up. The report worker has already finished.

The sender is idempotent on report id so a retry does not email twice. A DLQ holds addresses that will never succeed. You do not add the mail call inside the report transaction. A failed email would otherwise retry the whole report.

---

#### 30. An interviewer says: “Design the path of one paid order, from the mobile app to the database, and tell me what happens when billing is down.” How do you structure the answer?

**Answer:** Walk one request, then one failure.

The app calls **API Gateway** or an **ALB**. The API on **ECS Fargate** writes an order row to **Aurora** as `PENDING` and publishes `OrderPlaced` to **SNS**. It returns 202. Three queues are subscribed: inventory, billing, email. Billing’s consumer charges the card and updates the row to `PAID`. The API image came from **ECR** via **CodePipeline**. **CloudWatch** alarms on API 5xx and on the age of the billing queue.

When billing is down, its queue grows and the oldest-message alarm fires. Inventory and email still drain. Nothing is lost, because the event is in SQS, not in an HTTP call to billing. When billing returns, the consumer drains the backlog idempotently. You mention a DLQ if a message can never be charged. You do not draw ten more services. You show that you know where the data lives, who retries, and what the user is told while the order is still `PENDING`.

---
