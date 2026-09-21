# Amazon SNS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

These notes are aimed at day-to-day use. They are separate from the longer senior write-up in `SNS_SQS.md`.

---

## Fundamentals

#### 1. What is Amazon SNS?

**Answer:** SNS (Simple Notification Service) is managed pub/sub. A publisher sends one message to a **topic**. SNS pushes that message to every **subscription** on the topic: SQS, Lambda, HTTP, email, SMS, or a mobile push endpoint. Publishers do not know how many subscribers there are.

---

#### 2. When do you use SNS instead of SQS?

**Answer:** Use SNS when one event must reach **many** independent consumers. Use SQS when one worker pool pulls from a buffer. The usual production pattern is both: publish to SNS, and subscribe an SQS queue per service (fan-out). Calling SQS from every producer couples the producer to every consumer. SNS keeps that list on the topic.

---

#### 3. What is a topic, a subscription, and a message?

**Answer:** A **topic** is the named channel (standard or FIFO). A **subscription** binds one endpoint to that topic and can filter messages. A **message** has a body (up to 256 KB) and optional attributes. If the body is larger, store it in S3 and send the key. SNS is a notifier, not a file store.

---

#### 4. What delivery do subscribers get?

**Answer:** SNS retries HTTP and Lambda deliveries when the endpoint fails, with backoff, and can move failed deliveries to a **dead-letter queue** on the subscription. SQS subscriptions are durable once the message is in the queue: SNS’s job ends at a successful `SendMessage`. Email and SMS are best-effort notifications to humans, not a place to put data you cannot lose.

---

#### 5. What is the fan-out pattern?

**Answer:** One topic, several SQS subscriptions (orders, billing, email). A publisher emits “order placed” once. Each queue gets a copy and each service consumes at its own speed. If billing is down, billing’s queue grows. Orders and email keep moving. That isolation is why you put SQS between SNS and a worker instead of subscribing a fragile HTTP endpoint directly.

---

#### 6. Why not subscribe Lambda or HTTP directly to SNS?

**Answer:** You can, and it is fine for a low-volume function that is rarely down. If the function is throttled or the HTTP service returns 500, SNS retries and can eventually drop the message or land it in a DLQ. An SQS subscription absorbs the outage as a backlog and gives you a clearer age metric. Prefer SQS for anything you must not lose.

---

## Filtering, FIFO, and security

#### 7. What is subscription filter policy?

**Answer:** A filter on message **attributes** (or, if you enable it, on the body) so a subscription receives only matching messages. Example: an attribute `event` equals `order_placed`, so the refund service does not wake up for every event on a shared topic. Filters are a reason to send attributes, not only a JSON body. If you filter on the body, the syntax is more strict and you pay to evaluate it.

---

#### 8. What happens to a message that matches no subscription?

**Answer:** It is published successfully and delivered to nobody. SNS does not error. If every consumer uses a strict filter, a typo in an attribute silently drops the event. Log publishes, and alarm on subscriptions that stop receiving if you expect steady traffic. A catch-all subscription into an audit queue is sometimes worth it.

---

#### 9. What is an SNS FIFO topic?

**Answer:** A FIFO topic keeps order and deduplicates, and it can only subscribe **FIFO SQS** queues. You send a group id and a deduplication id, similar to SQS FIFO. Use it when ordered fan-out matters (status updates that must not be reordered per entity). Standard topics are the default for independent notifications.

---

#### 10. How do you stop a random principal from publishing to your topic?

**Answer:** The topic policy should allow `sns:Publish` only from known roles or from a specific service (`aws:SourceArn` for S3, EventBridge, and similar). Subscribers in another account need permission on the topic **and** on their queue. Encryption with a customer-managed KMS key requires the publisher and the subscriber principals to be allowed to use that key, or delivers fail with a KMS access error that looks like a mysterious drop.

---

#### 11. What must an SQS queue policy include for an SNS subscription?

**Answer:** `sqs:SendMessage` allowed for `sns.amazonaws.com`, with a condition that `aws:SourceArn` equals the topic ARN. Without it, the subscription stays pending or messages never arrive. Confirm the subscription state is `Confirmed`, not `PendingConfirmation`. Raw message delivery is a separate setting you usually want on for SQS.

---

#### 12. What is raw message delivery?

**Answer:** By default SNS wraps the payload in its own JSON envelope (type, message id, topic ARN, and your body as a string). **Raw message delivery** sends your body as-is to SQS or HTTP. Consumers that expect your event schema should turn raw delivery on. If you turn it on later, update the consumer. Old and new shapes will confuse a parser.

---

## Operations

#### 13. How do retries and dead-letter queues work on SNS?

**Answer:** For endpoint subscriptions (Lambda, HTTP), SNS retries failed deliveries. You can attach a DLQ to the **subscription**. Messages that exhaust retries go there. SQS subscriptions rarely need that path, because a successful send to SQS completes delivery. Watch `NumberOfNotificationsFailed` and the DLQ depth. A DLQ on the subscription does not replace a DLQ on the consumer queue.

---

#### 14. What is a delivery policy?

**Answer:** A retry policy on an HTTP or Lambda subscription: how many retries, the backoff, and the total time. Default retries are reasonable for a flaky endpoint and wrong for a dead one, because they delay the DLQ. Set a DLQ and a finite retry policy so failures become visible. Do not retry forever.

---

#### 15. How do you fan out to another region or account?

**Answer:** Subscribe a cross-account SQS queue (queue policy plus topic policy), or publish into a second-region topic from a subscriber you run. SNS topics are regional. There is no automatic global topic. Cross-region subscribers add latency and failure modes. Many teams publish once in the home region and let SQS consumers live there, and they replicate only when the consumer must be in another region.

---

#### 16. Can SNS guarantee that every subscriber got the message?

**Answer:** No. A publish returns when SNS accepts the message, not when every consumer finishes work. SQS subscribers then have their own at-least-once behavior. Design consumers to be idempotent. If you need a workflow that waits for all branches, use Step Functions, not “hope every queue deleted the message”.

---

#### 17. How do message attributes affect filtering and cost?

**Answer:** Attributes are the simplest filter keys (`event_type`, `tenant`). You can have a limited number of attributes, and each has a size limit. Do not stuff the whole payload into attributes. Body filtering can match JSON fields but is easier to get wrong. Prefer a small set of attributes that match how subscriptions are split.

---

#### 18. What is the difference between SNS and EventBridge?

**Answer:** SNS pushes a message you published to a list of subscribers, with simple filters. **EventBridge** routes event documents that match patterns, across many AWS services, SaaS partners, and custom buses, with archive and replay. Use SNS for straightforward fan-out, SMS, email, and mobile push. Use EventBridge when you want a central event bus, content-based routing, or third-party events. They can be combined: EventBridge rule target is an SNS topic.

---

#### 19. How do you test a topic without emailing real users?

**Answer:** Subscribe a test SQS queue and publish a message. Read the queue. Do not subscribe your personal email to a production topic. For HTTP, point a dev subscription at a dev endpoint with a filter so production events do not reach it. Separate topics per environment are safer than one topic with a careful filter.

---

#### 20. What CloudWatch metrics matter?

**Answer:** `NumberOfMessagesPublished`, `NumberOfNotificationsDelivered`, and `NumberOfNotificationsFailed`, plus SQS age on each subscriber queue. A publish rate with a failed-delivery rate means subscribers are rejecting messages. A publish rate with a flat consumer queue means the filter or the queue policy is wrong. Alarm on failed notifications and on subscriber DLQ depth.

---

## Scenarios

#### 21. Billing never hears about new orders, but the email service does. Both are subscribed. What do you check?

**Answer:** The billing subscription filter (maybe it expects `order_created` and the publisher sends `order_placed`), the billing queue policy, the subscription confirmation state, and KMS permissions if the topic is encrypted. The email subscription succeeding only proves the publish reached SNS. Each subscription fails independently.

---

#### 22. A Lambda subscribed to SNS is invoked three times for one event. Is that a bug?

**Answer:** It can be retry behavior. If the function throws, SNS retries. If the function also talks to SQS or a database without idempotency, you get duplicate side effects. Return success only after the work commits, and make the work idempotent. Check `NumberOfNotificationsFailed` and the function error metric before you blame SNS for inventing messages.

---

#### 23. You need SMS for one-time passwords and a queue for the same “user signed up” event. How do you model it?

**Answer:** One topic for `user_signed_up` is wrong for OTPs, because OTP SMS is a direct notification, not a business event fan-out. Call SNS SMS (or Amazon Pinpoint) from the auth service for the OTP. Publish a separate `user_signed_up` event to a topic that fans out to SQS consumers (analytics, CRM). Do not mix a high-priority SMS path with a best-effort analytics subscription on one message that might be filtered or delayed.

---

#### 24. Producers in account A must notify consumers in account B. What do you set up?

**Answer:** Topic in account A. Queue in account B. Topic policy allows B’s queue (or account) to subscribe and allows A’s producers to publish. Queue policy allows the topic ARN to `SendMessage`. Subscribe the queue to the topic. Turn on raw message delivery. Test with one message and a consumer in B before you open it to production traffic.

---

#### 25. Messages arrived in SQS wrapped in an SNS envelope and the worker threw on JSON parse. What changed?

**Answer:** Raw message delivery was off, so the body is SNS’s wrapper and the actual payload is a string in the `Message` field. Either enable raw delivery and keep the worker’s parser, or parse the envelope. Agree on one shape. A deploy that toggles raw delivery without updating the worker causes exactly this exception, and those messages will poison the queue until they hit the DLQ.

---

#### 26. How do you version events so a new field does not break old consumers?

**Answer:** Additive changes only: new JSON fields, not renamed ones. Put a `version` attribute on the message. Consumers ignore unknown fields. A breaking change is a new event name or a new topic, and both versions publish until old consumers are gone. SNS will not translate schemas for you.

---

#### 27. An HTTP subscriber times out often and delays the topic. Does that block SQS subscribers?

**Answer:** No. Delivery to each subscription is independent. A slow HTTP endpoint does not block an SQS subscription. It does waste retries and can fill that subscription’s DLQ. If you do not need the HTTP endpoint, delete the subscription. Do not leave a dead endpoint subscribed to a busy topic.

---

#### 28. How would you audit who published a message?

**Answer:** CloudTrail logs `Publish` calls (management events, and data events if you enable them for SNS). The message id in the publish response should be logged by the producer. SNS itself is not an audit log of the payload. If you must keep the event, subscribe an audit queue that nothing deletes from except a retention job, or archive the event in S3.

---

#### 29. When would you choose a separate topic per event type instead of one topic with filters?

**Answer:** Separate topics when the publishers, permissions, or criticality differ (payments versus marketing). One topic with filters when many event types share publishers and you want one place to subscribe. Too many topics is an operations burden. One giant topic without attributes forces every consumer to parse and discard most messages.

---

#### 30. What is a solid default for “order placed” in a microservice backend?

**Answer:** A standard SNS topic. Publishers are the order service’s IAM role. Subscriptions are one SQS queue per consumer service, raw delivery on, filter on an `event` attribute, queue policy locked to the topic ARN, KMS if the payload is sensitive, and a DLQ on each consumer queue. Consumers are idempotent. Alarms exist on notification failures and on each queue’s oldest message age.

---
