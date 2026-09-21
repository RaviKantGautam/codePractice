# AWS Lambda — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS Lambda, and what kind of work fits it?

**Answer:** Lambda runs your function in response to an event, without a server you manage. You provide a zip or a container image, a handler, memory, and a timeout. AWS runs it, scales the number of execution environments, and stops billing when the invocation ends (plus a short init period).

It fits event-driven work: HTTP handlers behind API Gateway or ALB, S3 or queue processing, cron, and glue between AWS services. It is a poor fit for long-lived connections, jobs over 15 minutes, or workloads that need a GPU or a custom kernel.

---

#### 2. What is a handler, an event, and the context object?

**Answer:** The handler is the function AWS calls. The **event** is the JSON payload from the trigger (API Gateway proxy request, SQS batch, S3 record, and so on). The **context** carries the request id, remaining time, and function identity. Your code should branch on the event shape and use the request id in logs so one invocation can be traced.

---

#### 3. Why must Lambda functions be stateless?

**Answer:** AWS may run two invocations on one environment or the next invocation on a different environment. Local memory and files in `/tmp` can survive across warm invocations, but you must not rely on them for correctness. Put durable state in DynamoDB, S3, RDS, or ElastiCache. Use the memory reuse only as a cache you can rebuild.

---

#### 4. How do memory and CPU relate?

**Answer:** You configure **memory** (128 MB through 10,240 MB). CPU and network bandwidth scale with that memory setting. You cannot set CPU alone. A function that is CPU-bound often gets faster, and sometimes cheaper, if you raise memory, because the billed duration drops. Measure duration and billed cost together.

---

#### 5. What is the maximum timeout, and what happens when it fires?

**Answer:** The maximum is **15 minutes**. When time runs out, Lambda stops the invocation and returns an error to the caller (or retries, depending on the event source). In-flight work is cut off. Set the timeout from the real p99 latency plus headroom, not the maximum, so a hung dependency fails fast. SQS visibility timeout must be longer than the function timeout.

---

#### 6. How can you deploy code to Lambda?

**Answer:**

* A **zip** uploaded directly (small packages) or from S3.
* A **container image** in ECR, up to 10 GB, when you need a custom OS library.
* **Layers** for shared dependencies, reused across functions.
* Infrastructure as code (CloudFormation, SAM, CDK, Terraform) so the function, IAM role, and trigger are one change.

Editing code in the console is fine for a spike, not for production.

---

#### 7. What is an execution role?

**Answer:** The IAM role Lambda assumes while running your code. It needs permission for the resources the function touches (for example `s3:GetObject`, `dynamodb:PutItem`, `logs:CreateLogStream`). Trust policy must allow `lambda.amazonaws.com`. Triggers that Lambda polls (SQS, streams) also need permissions on this role so Lambda can read and delete messages.

---

## Performance and concurrency

#### 8. What is a cold start?

**Answer:** A cold start is the extra latency when Lambda creates a new execution environment: download the package, start the runtime, and run your init code (imports, clients, secrets). The next invocations on that environment are warm and skip init. Cold starts are more noticeable with large packages, VPC networking, Java or .NET, and low-traffic functions. Init duration is billed.

---

#### 9. How do you reduce cold starts?

**Answer:**

* Cut package size and move heavy imports out of the cold path if you can.
* Initialize SDK clients **outside** the handler so warm invocations reuse them.
* Avoid a VPC when the function does not need private resources.
* Use **provisioned concurrency** for latency-sensitive functions so environments are pre-initialized.
* Prefer arm64 (Graviton) if your dependencies support it. It is often cheaper.

SnapStart (Java) snapshots the initialized environment. It is not available for every runtime.

---

#### 10. What is reserved concurrency versus provisioned concurrency?

**Answer:**

* **Reserved concurrency** caps how many executions of this function can run at once and guarantees that slice of the account limit. Extra invocations are throttled (429). Use it to protect a downstream database.
* **Provisioned concurrency** keeps a set number of environments initialized so those calls avoid cold starts. You pay even when they are idle.

Reserved limits throughput. Provisioned reduces latency. They solve different problems.

---

#### 11. What is the account concurrency limit, and what happens when you hit it?

**Answer:** Each region has an account-wide cap on simultaneous executions (the default is often 1,000 and can be raised). When the cap is hit, new invocations are throttled. One runaway function can starve the others. Reserved concurrency isolates a critical function so it keeps its own share, and isolates a risky function so it cannot take the whole account.

---

#### 12. What is a Lambda layer, and what should you not put in one?

**Answer:** A layer is a zip of libraries or files mounted into the execution environment, shared by several functions. Use it for a common internal SDK or a large binary. Do not use it as a way to hide application code you should version with the function, and do not pile so many layers that you cannot tell which version is deployed. The unzipped function plus layers must stay within Lambda’s deployment size limit (250 MB unzipped for zip deployments).

---

#### 13. What are versions and aliases?

**Answer:** Publishing a version freezes the code and config as an immutable number (`1`, `2`, …). `$LATEST` is mutable. An **alias** (for example `live`) points at a version, and you can shift the alias between versions or split traffic for a canary. Triggers and API Gateway stages should point at an alias, not at `$LATEST`, so a bad edit is not instantly in production.

---

## Events, retries, and VPC

#### 14. Which invocations are synchronous, and which are asynchronous?

**Answer:**

* **Synchronous:** the caller waits. API Gateway, ALB, and direct `Invoke` with `RequestResponse`. Errors return to the caller. Lambda does not retry for you.
* **Asynchronous:** S3, SNS, EventBridge, and `Invoke` with `Event`. Lambda retries twice (so up to three attempts) with backoff, then can send the event to a **dead-letter queue** or an **on-failure destination**.
* **Poll-based:** Lambda pulls from SQS, Kinesis, or DynamoDB Streams. Retry behavior follows the event source (SQS visibility timeout and redrive policy), not the async retry count.

---

#### 15. How should an SQS-triggered Lambda be configured so messages are not processed twice or lost?

**Answer:** Set the function timeout below the queue **visibility timeout**. If the function throws, the message becomes visible again and will be retried. Set a **max receive count** and a dead-letter queue. Keep the batch size modest, and use `ReportBatchItemFailures` so one bad record does not fail the whole batch. The function must be idempotent, because at-least-once delivery still applies.

---

#### 16. What changes when you attach a Lambda function to a VPC?

**Answer:** The function’s ENIs are placed in your subnets and security groups so it can reach private resources (RDS, ElastiCache, internal ALBs). It loses default internet access. To call public APIs or public AWS endpoints you need a NAT gateway or VPC endpoints. Cold starts used to be much worse. AWS has improved ENI reuse, but a VPC is still extra moving parts. Stay out of the VPC if you only talk to public AWS APIs.

---

#### 17. How do environment variables and secrets work?

**Answer:** Environment variables are part of the function configuration, encrypted at rest with a Lambda-managed key or a customer KMS key. They are visible to anyone who can call `GetFunctionConfiguration`. For database passwords, prefer Secrets Manager or Parameter Store, fetched during init and cached, with the execution role allowed to read only that secret. Rotating the secret requires a strategy to refresh warm environments (update the function or TTL the cache).

---

#### 18. What is `/tmp`, and how much can you store there?

**Answer:** `/tmp` is the only writable local disk. The default is 512 MB, and you can raise it up to 10 GB. It survives across warm invocations on the same environment and is not shared across environments. Use it for scratch files. Do not treat it as durable storage. You pay for ephemeral storage above the default.

---

#### 19. How does Lambda scale with SQS versus with API Gateway?

**Answer:** API Gateway can invoke as many concurrent executions as the account limit allows, one per request. SQS scaling adds execution environments gradually based on the queue depth, up to the function’s concurrency limit. A sudden flood of messages does not instantly become tens of thousands of parallel consumers. If you need a hard cap to protect RDS, set reserved concurrency.

---

## Operations and scenarios

#### 20. What logs do you get, and what should every function log?

**Answer:** stdout and stderr go to a CloudWatch log group `/aws/lambda/<function-name>`, one stream per environment. Log the request id (from the context), the event source, duration, and error type. Do not log full payloads that contain passwords or card data. A metric filter or an embedded metric on error count is more useful than reading streams by hand.

---

#### 21. How do you trace a slow request across API Gateway and Lambda?

**Answer:** Enable **AWS X-Ray** (or OpenTelemetry) on the API and the function. The trace shows gateway time versus function init versus handler time versus downstream calls, if those clients are instrumented. Cold start shows up as initialization time. Without tracing, compare API Gateway latency with the Lambda `Duration` and `InitDuration` metrics for the same minute.

---

#### 22. A function works in the console test and times out when triggered by S3. What is different?

**Answer:** The console test uses the event you pasted and your user to start it. The real S3 event has a different JSON shape, and the execution role may lack `s3:GetObject` on that bucket. A timeout usually means the handler is trying to reach a host it cannot (VPC without NAT, or a security group). Check the log stream for that request id and the function’s VPC config.

---

#### 23. How do you do a safe production deploy of a Lambda function?

**Answer:** Publish a new version, point an alias at it with a small traffic weight (or use CodeDeploy’s canary/linear hooks for Lambda), and watch errors and duration. Roll the alias back to the previous version if the new one fails. `sam deploy` or CI that updates `$LATEST` and the alias in one step is fine if the alias is what production invokes. Never wire production at `$LATEST` if humans can edit the function in the console.

---

#### 24. Why would raising memory lower the bill?

**Answer:** Billing is memory configured times duration (and requests). If 1,024 MB finishes in 200 ms and 256 MB finishes in 1,200 ms, the larger setting can cost less per invocation and it returns faster. Always check both duration and `Billed Duration` after a change. CPU-bound code benefits the most. IO-bound code waiting on RDS may not.

---

#### 25. How do you share a database connection pool from Lambda without exhausting RDS?

**Answer:** A pool inside one execution environment is fine. Hundreds of environments each opening several connections is not. Cap reserved concurrency, keep the pool small (often one connection per environment for Lambda), and put **RDS Proxy** in front of the database so many Lambdas share a smaller set of database connections. Close or reuse connections across warm invocations. Do not open a new pool on every handler call.

---

#### 26. An async function fails three times and the event disappears. Where did it go?

**Answer:** Lambda’s default async retry is two retries after the first attempt. If all fail and you did not configure an on-failure destination or a dead-letter queue, the event is dropped. Configure a DLQ (SQS or SNS) or a destination (SQS, SNS, Lambda, EventBridge) before you rely on async invocations for anything you cannot lose. Also alarm on the `Errors` and `DeadLetterErrors` metrics.

---

#### 27. What is the difference between an ALB target and an API Gateway integration for Lambda?

**Answer:** Both can invoke Lambda synchronously with an HTTP request. API Gateway adds API keys, usage plans, request validation, and stages, and is the usual front door for a public API. An ALB fits when the function is one target next to EC2 or ECS targets behind a hostname you already run, including private ALBs inside a VPC. Payload and timeout limits differ. Match the integration timeout to the function timeout.

---

#### 28. How do you test a Lambda function locally and in CI?

**Answer:** Unit-test the handler with a fake event and a mocked AWS SDK. In CI, run those tests, then `sam local invoke` or the Lambda Runtime Interface Emulator for a container image if you need the runtime. An integration test in a dev account that invokes the deployed function with a known event catches IAM and VPC mistakes that mocks hide. Do not only “test” by clicking in the console.

---

#### 29. A function is throttled at 50 concurrent executions even though the account limit is 1,000. What is set?

**Answer:** **Reserved concurrency** on that function is 50, or another function has reserved most of the account and left an unreserved pool smaller than you think. Throttles show up as `429` on synchronous calls and as retries or age growth on SQS. Raise the reserved value, or remove it if the cap was only meant for a load test.

---

#### 30. When would you not use Lambda for a new backend endpoint?

**Answer:** When requests regularly run for many minutes, when you need WebSockets at very large scale with custom servers, when the dependency stack does not fit the runtime, or when a steady 24/7 container is cheaper and simpler than provisioned concurrency. A long-running worker that already lives on ECS, or a service that must listen on arbitrary TCP ports, should stay on ECS or EC2. Lambda is still a strong default for spiky HTTP and event glue.

---
