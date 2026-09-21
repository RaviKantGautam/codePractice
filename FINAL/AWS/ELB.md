# Elastic Load Balancing — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Elastic Load Balancing, and which balancer do you pick?

**Answer:** ELB distributes traffic across targets in one or more Availability Zones.

| Balancer | Use |
| --- | --- |
| **Application Load Balancer (ALB)** | HTTP and HTTPS. Path and host routing, redirects, OIDC, Lambda targets. Default for APIs and websites. |
| **Network Load Balancer (NLB)** | TCP, UDP, TLS. Millions of connections, static IPs, very low latency. |
| **Gateway Load Balancer** | Appliances (firewalls, IDS), not application traffic. |
| **Classic Load Balancer** | Legacy. Do not use for new systems. |

---

#### 2. What are listeners, rules, and target groups?

**Answer:** A **listener** is a port and protocol on the load balancer (443 HTTPS). **Rules** on an ALB send matching requests (host, path, header) to a **target group**. A target group is a set of instances, IPs, or Lambda functions plus a health check and port. One ALB can route `/api` to one service and `/billing` to another.

---

#### 3. When would you choose an NLB over an ALB?

**Answer:** Choose an NLB when the protocol is not HTTP (raw TCP, MQTT, SMTP), when you need a static IP per AZ or an Elastic IP, when you are fronting PrivateLink, or when latency must stay extremely low and you do not need path routing. Choose an ALB for almost every HTTP API, because routing, auth headers, and HTTP health checks are built in.

---

#### 4. What is the difference between internet-facing and internal?

**Answer:** An **internet-facing** load balancer has public addresses and sits in public subnets with a route to an internet gateway. An **internal** load balancer has private addresses and is only reachable inside the VPC (and over peering or Transit Gateway). Backend microservices should be internal. Only the edge API should be internet-facing.

---

#### 5. Why does an ALB need a subnet in at least two Availability Zones?

**Answer:** AWS requires two AZ subnets so the load balancer can survive an AZ problem and so targets in those AZs can be registered locally. Each AZ you enable gets a load balancer node. Cross-zone load balancing (on by default for ALB) sends traffic to targets in other AZs as well. If you enable only one AZ, you have a single failure domain and the API will not let you create the ALB that way.

---

#### 6. What is cross-zone load balancing?

**Answer:** When it is on, each load balancer node can send traffic to healthy targets in every AZ, not only its own. ALB enables this by default. NLB has it off by default (you can turn it on). With it off, an AZ that has fewer targets receives the same share of connections and overloads those targets. Turn it on unless you have a reason to keep traffic inside the AZ.

---

## Health checks and routing

#### 7. How do health checks decide if a target gets traffic?

**Answer:** The load balancer calls a path (ALB) or a TCP port (NLB) on an interval. After enough consecutive successes the target is healthy. After enough failures it is removed from rotation. The check should hit an endpoint that proves the app can serve, not only that the process is listening. A health URL that always returns 200 while the database is down will keep sending users to a broken task.

---

#### 8. What is the difference between an ELB health check and an ASG or ECS health check?

**Answer:** The load balancer stops sending traffic when its own check fails. The Auto Scaling group or ECS service **replaces** the target only if you configured it to use the ELB health status. If you do not, a wedged instance stays in the group forever, unhealthy but never replaced. Set the ECS health-check grace period or the ASG grace period long enough for boot, or new targets get killed before they listen.

---

#### 9. What is a deregistration delay?

**Answer:** After you remove a target (a deploy, a scale-in), the load balancer stops sending new requests and waits this long (default 300 seconds) so in-flight requests can finish. Then the target is gone. Your process must stay alive for that window. If ECS `stopTimeout` is shorter than the delay, the task is killed while the ALB still considers it draining, and clients see errors.

---

#### 10. What are sticky sessions, and why are they a last resort?

**Answer:** Stickiness pins a client to one target using a cookie (ALB) or the client IP (NLB). Use it only when the app stores session state in memory. It unbalances scale-out: one target stays hot, and a deploy or a crash logs that user out or fails their next call. Prefer a shared session store (Redis, DynamoDB) or no server session at all (JWT or similar), and leave stickiness off.

---

#### 11. How does ALB path-based routing work for two microservices?

**Answer:** One listener on 443. Rule priority 10: path `/orders/*` forwards to the orders target group. Priority 20: path `/users/*` forwards to the users target group. A default rule returns 404 or forwards to a frontend. Priorities are numeric. The first match wins. Host-based rules (`api.example.com` versus `admin.example.com`) work the same way and are how many teams share one ALB.

---

#### 12. What is an ALB target type of `instance` versus `ip` versus `lambda`?

**Answer:**

* **instance:** registers EC2 instance ids. Used with instance security groups and bridge-mode ECS.
* **ip:** registers IP addresses. Required for Fargate and for awsvpc ECS tasks, and for targets outside the VPC (via IP).
* **lambda:** one Lambda function as the target. The ALB invokes it synchronously per request.

A common outage is an awsvpc service registered into an `instance` target group. The types must match how the task gets its address.

---

## TLS, security, and headers

#### 13. Where should TLS terminate?

**Answer:** Usually at the ALB. You attach an ACM certificate to the 443 listener, and the ALB talks HTTP to the targets inside the VPC (or HTTPS again if policy requires encryption in transit the whole way). ACM renewal is automatic for DNS-validated certs. You do not install certificates on every instance. An NLB can pass TCP through and let the app terminate TLS, which you do when the app needs the client certificate.

---

#### 14. What security groups do you set on the ALB and on the targets?

**Answer:** The ALB security group allows 443 from the internet or from the caller CIDR. The target security group allows the app port **only from the ALB security group**, not from `0.0.0.0/0`. If targets are open to the world, anyone who finds the task IP bypasses WAF rules and authentication you enforced only on the listener.

---

#### 15. What headers does an ALB add, and which ones can a client spoof?

**Answer:** The ALB sets `X-Forwarded-For`, `X-Forwarded-Proto`, and `X-Forwarded-Port`. It appends the real client IP to `X-Forwarded-For`. A client can send its own `X-Forwarded-For`, so do not trust the leftmost value for security decisions. Use the rightmost address the ALB added, or the ALB’s forwarded header behavior you configured. Security decisions belong in IAM, signed tokens, or mTLS, not in a header the browser can set.

---

#### 16. How do you put authentication in front of a service without writing it in every app?

**Answer:** An ALB listener rule can use **OIDC** or **Cognito**. The ALB redirects unauthenticated users, then forwards requests with identity headers (`x-amzn-oidc-identity` and a JWT in `x-amzn-oidc-data`). The app still must validate that header for sensitive actions if the target can be reached another way. This is a convenient edge login, not a full authorization framework inside the service.

---

#### 17. What is AWS WAF’s relationship to an ALB?

**Answer:** You associate a WAF web ACL with the ALB (or with CloudFront, API Gateway, or AppSync). WAF runs before the request hits your rules: rate limits, managed bot rules, geo match, and IP block lists. It does not replace application authorization. Put WAF on the public ALB, not on every internal microservice.

---

#### 18. What is connection draining versus a 502 from the ALB?

**Answer:** Draining is the deregistration delay. A **502 Bad Gateway** means the ALB could not get a valid response from the target: nothing is listening, the target closed the connection, the app crashed mid-response, or the target type/port is wrong. A **504** means the target accepted the connection but did not respond before the ALB idle or request timeout. Check target health, app logs, and the idle timeout if uploads or long polls are involved.

---

## Timeouts, scaling, and NLB details

#### 19. What timeouts matter on an ALB?

**Answer:** The **idle timeout** (default 60 seconds) closes a connection with no bytes. Raise it for long polls, server-sent events, or slow uploads, and raise the client and server timeouts together. ALB does not have a separate “request processing timeout” as short as API Gateway’s 29-second integration timeout. Very long requests are still a design smell. The target’s own timeout and the deregistration delay must agree with the idle timeout.

---

#### 20. How does an NLB preserve the client IP?

**Answer:** With instance target groups, an NLB can pass the original source IP through (preserved client IP), so security groups and logs see the client, not the load balancer. The target security group must allow the **client** CIDR, not only the NLB. With IP target groups, you often see the NLB address instead, and you turn on proxy protocol if the app needs the real client address. This is a frequent reason “the NLB health check works but clients time out”: the security group allows the VPC but not the internet client.

---

#### 21. Does a load balancer scale by itself?

**Answer:** Yes. ALB and NLB scale with traffic. You do not set an instance size for the load balancer. You do pay for LCUs (capacity units) based on connections, bytes, and rule evaluations. You still scale the **targets**. A load balancer in front of one small instance does not make that instance bigger. Pre-warming is rarely needed for ALB today. A sudden flood is more often survived by the balancer than by your app.

---

#### 22. What is a fixed response or a redirect rule used for?

**Answer:** A redirect sends HTTP to HTTPS or sends an old host to a new one, without a server. A fixed response returns a static code and body (a maintenance page, a 404 for unknown paths). Use them so you do not run a container just to bounce a request. They are listener rules, evaluated by priority like any other rule.

---

#### 23. How do you see access logs?

**Answer:** Enable access logs to an S3 bucket. Each line has the client, target, latency, status, and request path. They are the first place to confirm whether a 502 was the ALB failing to connect or the app returning 500. CloudWatch metrics (`HTTPCode_Target_5XX_Count`, `TargetResponseTime`, `HealthyHostCount`) are what you alarm on. Logs are what you read afterward.

---

## Scenarios

#### 24. Users see intermittent 502s right after every deploy. Healthy host count dips and recovers. What do you fix?

**Answer:** New tasks are registered before they listen, or old tasks are killed before they drain. Set a health-check grace period, a health check that matches the real port and path, a deregistration delay, and an application that handles SIGTERM by finishing requests. A rolling deploy with minimum healthy percent of 100 and max of 200 keeps old tasks until new ones are healthy.

---

#### 25. Only one of three tasks receives traffic. The others are healthy. Why?

**Answer:** Sticky sessions are on, or the other tasks are in an AZ whose load balancer node is not enabled, or a listener rule points at a different target group than the one you are watching. Cross-zone may be off on an NLB so one AZ with one task gets a third of the connections and that single task is hot. Check stickiness first.

---

#### 26. You need the same API hostname to route to ECS in two regions. Is that an ALB feature?

**Answer:** An ALB is regional. Multi-region failover is **Route 53** (latency or failover records) in front of one ALB per region, or Global Accelerator in front of regional ALBs or NLBs. The health check on the DNS record should look at the regional load balancer. Do not try to register another region’s IPs in a single ALB and expect a supported design.

---

#### 27. A private microservice must be called by several other VPCs. What do you place in front of it?

**Answer:** An internal NLB and **PrivateLink** (VPC endpoint service), or an internal ALB reached over Transit Gateway or peering. PrivateLink is the tighter option: consumers get an interface endpoint and never route freely into your subnets. Security groups on the endpoint and on the load balancer still apply. An internet-facing ALB plus a security group allow-list is weaker and easier to misconfigure.

---

#### 28. The ALB returns 503 and there are no healthy targets. The tasks are running. Where do you look?

**Answer:** Target group health-check path, port, and protocol. Security group on the task must allow the ALB. The container must listen on the same port the target group uses. For Fargate, targets must be type `ip` and the task IP must be registered. A successful `kubectl` or ECS “RUNNING” state does not mean the health check URL returns 200.

---

#### 29. How do you add a canary of a new version behind one hostname?

**Answer:** Two target groups (old and new). A listener rule forwards by **weight**, for example 90 percent to old and 10 percent to new. Watch 5xx and latency on the new group, then move the weight. ECS with CodeDeploy blue/green does this for you. Weighted target groups without a second hostname are the ALB-native version of a canary.

---

#### 30. What would you alarm on for a public ALB in front of an API?

**Answer:** `HTTPCode_ELB_5XX_Count` (the balancer itself failed), `HTTPCode_Target_5XX_Count` (the app failed), target response time, and `HealthyHostCount` below the minimum you need. Optionally rejected connections and a WAF blocked-request spike. Page on ELB 5xx, target 5xx rate, and zero healthy hosts. A single slow target is a dashboard item until it moves the p99.

---
