# Amazon EventBridge — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon EventBridge?

**Answer:** EventBridge is a serverless event bus. Producers put **events** (JSON documents) on a bus. **Rules** match those events and send them to targets such as Lambda, SQS, SNS, Step Functions, API destinations, or another bus. It replaces the older CloudWatch Events API and is the default way AWS services emit “something happened”.

---

#### 2. What is an event?

**Answer:** A JSON object with fields such as `source`, `detail-type`, and `detail`, plus an account and time. AWS services use sources like `aws.ec2` or `aws.s3`. Your applications use a custom source string, for example `orders.service`. The `detail` object is your payload. There is a size limit (256 KB). Larger data stays in S3 and the event carries the key.

---

#### 3. What buses exist in an account?

**Answer:**

* The **default bus**, where AWS service events go.
* **Custom buses** you create for your own domains (`orders`, `billing`), so rules and permissions stay separate.
* **Partner buses** for SaaS integrations that send events into your account.

Do not put every custom event on the default bus if you want a clear permission boundary. A custom bus per domain is easier to reason about.

---

#### 4. What is a rule?

**Answer:** A rule has an **event pattern** (or a schedule) and one or more targets. When an event matches, EventBridge delivers it to each target. Rules do not remove the event from a queue you pull. Delivery is push. A bus can have many rules, and more than one rule can match the same event.

---

#### 5. How is EventBridge different from SNS?

**Answer:** SNS fans a message out to subscribers you listed, with simpler filtering, and it can send SMS, email, and mobile push. EventBridge matches a document against patterns, is the path for most AWS service events, supports archive and replay, schema discovery, and third-party buses. Use SNS when you want straightforward pub/sub or human notifications. Use EventBridge when services emit events and many independent rules decide who cares.

---

#### 6. How is EventBridge different from SQS?

**Answer:** SQS is a queue one set of workers pull from. EventBridge does not store a backlog for you to poll (unless the target is SQS). If a target fails, EventBridge retries and can send the event to a DLQ, but it is not a worker buffer. The durable pattern is an EventBridge rule whose target is an SQS queue, and workers consume the queue.

---

## Patterns, targets, and schedules

#### 7. What does an event pattern look like?

**Answer:** A JSON pattern EventBridge compares to the event. Example: `source` is `orders.service` and `detail-type` is `OrderPlaced` and `detail.status` is `PAID`. Matching is exact on the fields you specify. Unmentioned fields are ignored. A pattern that is too broad (`source` only) invokes targets for events you did not mean. Test patterns with the console’s sample event or a unit test of the pattern before you attach a production Lambda.

---

#### 8. What targets can a rule invoke?

**Answer:** Lambda, SQS, SNS, Step Functions, ECS tasks, API Gateway, API destinations (any HTTPS endpoint with a connection), Kinesis, and another event bus, among others. You can attach an **IAM role** the bus assumes for targets that need it. Up to five targets per rule is a common limit to design around. If you need more consumers, send to SNS or to a second bus and split there.

---

#### 9. What is an input transformer?

**Answer:** A mapping that reshapes the event before the target sees it. You might pass only `detail.orderId` into an SQS message or build a string for a legacy API. Use it so the consumer does not depend on the full EventBridge envelope. Keep it simple. Heavy transformation belongs in a Lambda, where you can test it like normal code.

---

#### 10. What is EventBridge Scheduler, and how is it different from a rate rule?

**Answer:** **Scheduler** is the service for “run this at this time”: one-off or recurring, with a flexible time window, a target, and a retry policy. Rules on a bus can also use a schedule expression (the old CloudWatch Events cron). Prefer Scheduler for new scheduled jobs. It is built for that and supports time zones and many targets. A rate rule is fine for a simple periodic trigger you already manage next to other rules.

---

#### 11. How do you emit an event from application code?

**Answer:** Call `PutEvents` with the bus name, source, detail-type, and a JSON detail. The SDK call is synchronous only for acceptance onto the bus, not for “all targets succeeded”. Check the response for failed entries. Batch up to 10 events per call. The producer’s IAM role needs `events:PutEvents` on that bus. Do not block a user request on every downstream consumer. Publish and return.

---

#### 12. What happens if a target fails?

**Answer:** EventBridge retries delivery. You can set a **dead-letter queue** (SQS) and a retry policy on the target. If you never set a DLQ, a failing Lambda can mean the event is retried and then dropped. For anything important, the target should be SQS (durable) or the rule target should have a DLQ. Alarm on that DLQ.

---

## Archive, schemas, and multi-account

#### 13. What are archives and replay?

**Answer:** An **archive** stores events from a bus that match a filter, for a retention period you choose. **Replay** sends those stored events back onto the bus (or a subset) as if they were new, for a time range. Use it to recover a consumer that was buggy, or to seed a new consumer. Replay can duplicate work. Consumers must be idempotent. It is not a message queue you browse by hand.

---

#### 14. What is the schema registry?

**Answer:** EventBridge can discover schemas from events on a bus and store them in a registry. You can download code bindings. It helps teams know the shape of `detail`. It does not enforce the schema on `PutEvents`. A bad producer can still publish a different JSON. Contract tests in CI are still your job. The registry is documentation that stays closer to the real events.

---

#### 15. How do you send events to another account?

**Answer:** Put a rule on the source bus whose target is the other account’s bus ARN. The target bus’s resource policy must allow the source account to `PutEvents`. Use this for a central audit account or for a platform bus. Do not share a production bus by giving every account broad IAM in the producer account.

---

#### 16. How do AWS service events arrive?

**Answer:** Most services deliver to the **default** bus. You write a rule with `"source": ["aws.s3"]` or similar. Some services (a few S3 notifications, older integrations) still need you to opt in or to use their own notification config. S3 can send to EventBridge if you enable it on the bucket, which is preferable to wiring many bucket notification destinations by hand.

---

#### 17. What is an API destination?

**Answer:** A target that calls an HTTPS endpoint outside AWS. You store the URL and an authorization connection (API key, OAuth, or basic auth) in EventBridge. Use it to notify a SaaS tool without running a Lambda just to POST. The endpoint must be public and reliable. Put a DLQ on the target. For internal VPC services, prefer SQS or a Lambda in the VPC. API destinations do not run inside your subnet.

---

#### 18. What are global endpoints?

**Answer:** A global endpoint fails over `PutEvents` between two regions for applications that need a higher availability publish path. Consumers still exist in the regions you configure. This is an advanced setup. Most services should publish to one regional custom bus and only add a global endpoint when a regional EventBridge outage is an availability problem you have actually decided to pay for.

---

## Operations and scenarios

#### 19. A rule exists but the Lambda never runs. What do you check?

**Answer:** The event pattern against a real event (source and detail-type typos), that the event went to the **same bus** the rule is on, the Lambda resource policy allowing `events.amazonaws.com`, and the target DLQ. `PutEvents` succeeding only means the bus accepted the event. Also check that the rule is enabled. A common bug is publishing to a custom bus while the rule sits on the default bus.

---

#### 20. How do you avoid every team publishing a different shape for the same fact?

**Answer:** Agree on `source`, `detail-type`, and a version field inside `detail`. Document it in the schema registry or in the service repo. Additive changes only. A breaking change gets a new detail-type (`OrderPlacedV2`) and both are emitted until consumers move. EventBridge will happily deliver both shapes. It will not convert them.

---

#### 21. Consumers see duplicate events. Is the bus wrong?

**Answer:** Delivery is at least once. Retries, replay, and a producer that retried `PutEvents` after a timeout all create duplicates. Store the event id (EventBridge provides one) or your own idempotency key in DynamoDB and skip repeats. Do not assume a rule fires exactly once because it did so in a test.

---

#### 22. How would you migrate from SNS fan-out to EventBridge without a big bang?

**Answer:** Publishers start `PutEvents` and still publish to SNS. An EventBridge rule targets the same SQS queues (or targets SNS during the overlap). When consumers are healthy on the new path, remove the SNS publish. Keep idempotency because the overlap double-delivers. Patterns should match the new envelope so you do not drop events that used to be raw SNS bodies.

---

#### 23. You need to react when an EC2 instance stops and when your app places an order. Where do the rules live?

**Answer:** The EC2 rule listens on the **default** bus for `aws.ec2`. The order rule listens on a **custom** application bus. They are different buses. One Lambda can still be a target of both, but the patterns and permissions stay easier if the rules sit next to the events. Do not forward every AWS service event onto your application bus “just in case”. Forward the few you need.

---

#### 24. A new consumer must process the last seven days of orders. The old consumer did not store them. What feature do you use?

**Answer:** An **archive** that has been capturing those events, then **replay** onto a bus where only the new consumer’s rule matches (use a replay filter or a dedicated bus). If you never created an archive, EventBridge cannot invent history. The fallback is whatever the order service stored in its database. Turn on archives for events you may need to rebuild from.

---

#### 25. How do you secure who can publish and who can attach a rule?

**Answer:** `events:PutEvents` on the custom bus for producers only. `events:PutRule` and `events:PutTargets` restricted to the platform or the owning team. A bus resource policy for cross-account puts. Targets still need their own permissions (Lambda resource policy, SQS queue policy). Encrypt events with a customer-managed KMS key if the detail holds sensitive data, and allow the service and the targets to use the key.

---

#### 26. What is the latency you should expect, and what should you not use it for?

**Answer:** Delivery is typically seconds, not milliseconds, and it is not a transaction. Do not use EventBridge as the synchronous path of an HTTP request or as a lock. Do use it for “order placed, tell the rest of the company”. If a workflow needs timeouts, retries, and a result, EventBridge can start a Step Functions execution. The state machine, not the bus, owns the control flow.

---

#### 27. How do scheduled jobs pass different parameters per environment?

**Answer:** Scheduler (or a rule) can send a constant JSON input to the target. Keep that input in the same IaC stack as the schedule so dev and prod do not share a cron that points at prod. The target Lambda or ECS task reads config from the environment it runs in. Do not bake account ids into application code when the schedule input or the stack parameter already has them.

---

#### 28. What fails when the event is larger than the limit?

**Answer:** `PutEvents` rejects that entry. The rest of a batch can still succeed, so you must read the per-entry response. Store the payload in S3 and send a small event. Targets such as SNS and SQS have their own limits. A transformer that expands the payload can also fail delivery. Log the failed entry code. It is not always a Lambda error.

---

#### 29. How would you debug a single lost order event?

**Answer:** Start from the producer log: the `PutEvents` event id and whether that entry failed. Then check the bus (archive, if enabled) and the rule’s matched metrics or the target DLQ. Lambda logs should include the event id. Without an archive or producer logs, you cannot prove the event existed. Add the event id to every consumer log line before you need it in an incident.

---

#### 30. What is a practical default for application events on a backend team?

**Answer:** One custom bus per environment. Producers call `PutEvents` with a stable source and detail-type. Rules are small and owned by the consumer team. Important consumers are SQS queues, not only Lambda, with their own DLQs. An archive retains events for the period you might need to replay. Schemas are documented. Alarms fire on target delivery failures and on consumer queue age. Idempotency keys are stored by consumers.

---
