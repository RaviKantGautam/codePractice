# Amazon MQ — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon MQ?

**Answer:** Amazon MQ is a managed message **broker**. It runs Apache ActiveMQ or RabbitMQ so applications can use standard protocols (JMS, AMQP 0-9-1, MQTT, STOMP, OpenWire) without you patching the broker OS yourself. You still design exchanges, queues, and consumers the way you would with those brokers.

---

#### 2. When would you choose Amazon MQ instead of SQS and SNS?

**Answer:** Choose Amazon MQ when an existing application already speaks JMS, AMQP, MQTT, or STOMP, or when you need broker features such as RabbitMQ exchanges and routing keys, or ActiveMQ virtual destinations, and you cannot change the clients. Choose SQS and SNS for new AWS-native work. They scale without a broker instance, and you do not manage engine versions and storage on a node.

---

#### 3. What is the difference between the ActiveMQ engine and the RabbitMQ engine?

**Answer:**

* **ActiveMQ:** JMS and protocols such as OpenWire, AMQP, STOMP, and MQTT. Familiar if the app uses Java Message Service.
* **RabbitMQ:** AMQP 0-9-1, with exchanges, bindings, and routing keys. Familiar if the app already uses RabbitMQ.

You do not mix them in one broker. Pick the engine your clients already use. Migrating from one to the other is an application change, not a console toggle.

---

#### 4. What do you still operate, if AWS manages the broker?

**Answer:** Engine version upgrades, instance size, storage, network placement (VPC subnets and security groups), users, and the messaging topology (queues, exchanges, topics). AWS handles the broker software install and a multi-AZ option. You still monitor queue depth, connections, and memory, and you still design consumers to be idempotent.

---

#### 5. What is a deployment mode?

**Answer:**

* **Single-instance:** one broker in one AZ. Fine for development. A failure or a maintenance window stops messaging.
* **Active/standby (ActiveMQ) or cluster (RabbitMQ):** nodes in multiple AZs. Failover takes clients to the standby. Use this for production.

Failover is not instant. Clients need reconnect and retry logic. In-flight work can be redelivered.

---

#### 6. How do applications connect?

**Answer:** Through a broker endpoint in your VPC, on the protocol port (for example AMQP 5671 or OpenWire with TLS). Security groups must allow the client security group to that port. You do not expose the broker to the public internet. Connection strings differ for the active endpoint versus a failover pair. Use the failover URI the console gives you so clients reconnect to the standby.

---

## Behavior that interviews ask about

#### 7. What does “the message is durable” require on RabbitMQ?

**Answer:** The queue must be durable, the message must be published as persistent, and you usually want a confirm from the broker before the producer forgets the message. A durable queue alone is not enough if the message is transient. Consumers should use manual acknowledgements. Auto-ack before the work finishes loses messages on a crash.

---

#### 8. What is the difference between an acknowledgement and SQS DeleteMessage?

**Answer:** On RabbitMQ or ActiveMQ, the consumer **acks** the delivery after processing. If the consumer disconnects without an ack, the broker redelivers. SQS uses a visibility timeout and an explicit delete. The idea is the same: do not ack or delete until the side effect is committed. Prefetch (QoS) limits how many unacked messages a consumer holds. A huge prefetch on a slow consumer looks like a stuck queue to everyone else.

---

#### 9. What is a dead-letter queue on a broker versus in SQS?

**Answer:** Both hold messages that could not be processed. On RabbitMQ you configure a dead-letter exchange and a policy (rejected, expired, or max length). On SQS it is a redrive policy with `maxReceiveCount`. On Amazon MQ you must configure the broker feature yourself. It is not automatic just because you created a broker. Alarm on the DLQ the same way you would for SQS.

---

#### 10. How do retries work?

**Answer:** The broker redelivers unacked messages. It does not implement Lambda-style retry counts unless you add a policy or the application tracks attempts. A poison message without a DLQ will be redelivered forever and can block a consumer that prefetches it. Set a retry limit in the app or a dead-letter policy, and always log the message id.

---

#### 11. What is prefetch, and why does it matter?

**Answer:** Prefetch is how many messages the broker will push to a consumer before it must ack. Prefetch of 1 spreads work fairly across slow and fast consumers. A very high prefetch piles messages on one consumer, so scale-out does nothing until that consumer acks. Start low for long jobs.

---

#### 12. How is ordering different from SQS FIFO?

**Answer:** A single RabbitMQ queue with one consumer is ordered. Competing consumers break any global order, because they ack at different speeds. Amazon MQ does not give you SQS FIFO message groups. If you need order per entity, partition by routing key onto queues consumed by one worker each, or use SQS FIFO. Do not promise global order once you scale consumers.

---

## Networking, security, and sizing

#### 13. Where should the broker live in the VPC?

**Answer:** Private subnets, ideally one per AZ for a multi-AZ broker. No public IP. Clients in the same VPC, or in peered networks, connect on the protocol port. Turn on **TLS**. Use the broker’s user accounts with permissions limited to the virtual host or queues that service needs, not one admin user in every app.

---

#### 14. How do you rotate broker passwords?

**Answer:** Amazon MQ can integrate with Secrets Manager for broker credentials on supported engines, or you rotate the user password in the broker and update the secret the app reads. Rolling restart of consumers picks up the new secret. Do not bake the password into the image. A restart of the broker is sometimes required for certain credential changes. Plan it on the active/standby pair so you are not surprised in production.

---

#### 15. What instance size limits you?

**Answer:** The broker instance has CPU, memory, and network caps, and storage for messages that are not consumed. A backlog of large persistent messages fills the disk and publishers block or the broker alarms. This is different from SQS, where AWS absorbs the backlog. Watch memory and disk. Scale the instance or add consumers before the disk fills. You cannot treat Amazon MQ as infinitely elastic.

---

#### 16. What is a maintenance window?

**Answer:** AWS patches the broker during a window you set. On a single-instance broker, that is downtime. On active/standby, the standby is patched and a failover occurs. Clients must reconnect. Schedule the window when reconnects are acceptable, and make sure connection retry is tested. Skipping engine upgrades leaves you on a version AWS will eventually force you off.

---

#### 17. How do you monitor Amazon MQ?

**Answer:** CloudWatch metrics for message count, consumer count, CPU, memory, and disk. RabbitMQ also exposes its own management UI through a secured endpoint if you enable it. Alarm on queue depth and on low disk. Logs can go to CloudWatch Logs. A healthy consumer count of zero while depth grows means the app is down, not the broker.

---

#### 18. Can Lambda poll Amazon MQ?

**Answer:** Yes. Lambda has an event source mapping for Amazon MQ (RabbitMQ and ActiveMQ). Lambda invokes your function with a batch of messages. You still size the broker, and the function must be idempotent because redelivery exists. If you are starting from scratch and the only consumer is Lambda, SQS is usually simpler. Use the MQ event source when the publisher is already a broker client you cannot change.

---

## Migration and scenarios

#### 19. How would you migrate a self-managed RabbitMQ to Amazon MQ?

**Answer:** Stand up an Amazon MQ RabbitMQ broker in the VPC. Recreate vhosts, exchanges, queues, and bindings (definitions export/import helps). Point a test consumer at the new broker. Drain the old queues or mirror publishers to both during a cutover, then switch connection strings. Do not assume plugins you installed on your own server exist on Amazon MQ. Check the supported plugin and version list before you commit.

---

#### 20. A Java service uses JMS queues and topics. Which engine do you pick?

**Answer:** **ActiveMQ**, because JMS maps to it directly. RabbitMQ is not a JMS broker unless you add a different client. Keep the JMS connection factory pointed at the Amazon MQ OpenWire or AMQP endpoint Amazon documents for ActiveMQ, with the failover transport so standby works.

---

#### 21. Publishers block and consumers are running. What is a likely broker-side cause?

**Answer:** A queue hit a memory or disk alarm, so RabbitMQ blocks publishers (flow control). Or prefetch is huge and consumers are stuck on poison messages and not acking, so the broker will not take more. Check alarms, unacked counts, and disk. SQS would have accepted the publish. A broker has a finite buffer.

---

#### 22. You need fan-out to three services. How do you do that on RabbitMQ versus SNS?

**Answer:** On RabbitMQ, a **fanout** exchange bound to three queues. Each service consumes its queue. On AWS-native design, an SNS topic with three SQS subscriptions does the same. If the producer is already an AMQP client, use the exchange. If the producer is a new Lambda, prefer SNS or EventBridge and skip the broker.

---

#### 23. Messages were redelivered after a failover and the database row was written twice. What is missing?

**Answer:** Consumer idempotency. Failover redelivers unacked messages. The consumer should use a unique message id and a conditional write. Ack only after commit. This is the same class of bug as an SQS visibility timeout, with a different API.

---

#### 24. How do you decide the queue is the wrong tool after you are on Amazon MQ?

**Answer:** If you are rewriting the producers and consumers anyway, moving to SQS removes broker sizing, patching, and connection management. Stay on Amazon MQ if many applications you do not own speak AMQP or JMS to this broker. A hybrid (broker for legacy, SQS for new services) is normal. Do not grow a new platform on a broker only because it was the first messaging service in the account.

---

#### 25. What security group mistake locks every client out after a “nothing changed” deploy?

**Answer:** The broker allows the old client subnet CIDR, and the new tasks got a new security group or a new subnet. Protocols fail closed. Allow the **client security group** on the broker port, not a wide CIDR, and update it when the client moves. Also confirm TLS: clients still using plaintext to a TLS-only listener hang or reset.

---

#### 26. Can you use Amazon MQ across regions the way SQS works in one region?

**Answer:** Brokers are regional and live in your VPC. Cross-region is your problem: federation or shovel plugins where the engine supports them, or an application that publishes twice. There is no built-in multi-region queue like some other AWS messaging features. If you need a second region, design the bridge explicitly and test failover. Do not assume the standby AZ is a second region. It is not.

---

#### 27. How should a consumer shut down during a deploy?

**Answer:** Stop consuming, finish or nack in-flight messages, then close the connection. If you kill the process, unacked messages are redelivered to the new tasks. That is safe only if the work is idempotent. A long job should heartbeat or use a longer consumer timeout so the broker does not decide the consumer is dead mid-job.

---

#### 28. What is the cost shape compared with SQS?

**Answer:** You pay for the broker instance hours and storage all the time, even when traffic is zero. SQS charges mostly per request. A quiet workload is often cheaper and simpler on SQS. A steady high-throughput legacy RabbitMQ estate can be cheaper to lift onto Amazon MQ than to rewrite, which is the real reason to pay for a broker that sits idle at night.

---

#### 29. How do you back up broker state?

**Answer:** Amazon MQ takes recovery steps for the managed service, and you can use the engine’s definitions export so queues and exchanges are recreatable. Messages in flight are not a backup strategy. If the data must survive a deleted broker, your consumers should have written the business result to a database. Do not use the broker as the system of record.

---

#### 30. What would you tell an interviewer if they ask “SQS or Amazon MQ?” for a new Python service?

**Answer:** SQS, unless a requirement names AMQP, JMS, or an existing broker. A new Python worker can use the AWS SDK, a Standard queue, a DLQ, and long polling with less operational load. Recommend Amazon MQ only for protocol compatibility or a feature SQS does not have and that the design actually needs. Mention idempotency either way.

---
