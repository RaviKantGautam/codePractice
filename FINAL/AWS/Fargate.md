# AWS Fargate — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS Fargate?

**Answer:** Fargate is a serverless compute engine for containers. You run ECS tasks or EKS pods by declaring vCPU and memory. AWS provisions and patches the underlying hosts. You do not SSH to a node, choose an AMI, or join instances to a cluster.

---

#### 2. When would you choose Fargate instead of ECS on EC2?

**Answer:** Choose Fargate when the service is a normal container, the team does not want to operate nodes, and the workload fits Fargate’s CPU, memory, and storage sizes. Choose EC2 (or EKS node groups) when you need GPUs, privileged containers, custom kernel modules, instance-store disks, or very steady high utilization where reserved EC2 capacity is cheaper.

---

#### 3. What do you actually configure for a Fargate task?

**Answer:** A task definition (or a Kubernetes pod spec on EKS) with:

* CPU and memory combination Fargate allows
* Container image, port, and command
* **awsvpc** networking (required): subnets and a security group
* Task execution role and task role
* Log driver, usually `awslogs`
* Optional EFS volume or extra ephemeral storage

There is no instance type and no placement group.

---

#### 4. Why is `awsvpc` required on Fargate, and what does that mean for the app?

**Answer:** Each task gets its own elastic network interface, private IP, and security group, the same model as an EC2 instance. The container listens on the container port directly. You do not use Docker bridge port mapping. Security groups are attached to the task ENI, so two tasks can have different firewall rules even in the same subnet.

---

#### 5. How is Fargate billed compared with EC2?

**Answer:** You pay for the **requested** vCPU and memory for the time the task runs, billed per second with a one-minute minimum, plus normal charges for data transfer, load balancers, and storage. You do not pay for an idle host between tasks. On EC2 you pay for the instance even when tasks only fill part of it. Fargate Spot lowers the price with interruption risk, similar to EC2 Spot.

---

#### 6. What is the task execution role versus the task role on Fargate?

**Answer:**

* **Execution role:** used by the ECS agent (AWS) to pull the image from ECR, write logs, and fetch secrets referenced in the task definition.
* **Task role:** assumed by your application code for AWS API calls (S3, DynamoDB, SQS, and so on).

If the image pull fails, fix the execution role. If the app gets `AccessDenied` from DynamoDB, fix the task role.

---

#### 7. Can you SSH into a Fargate task to debug it?

**Answer:** There is no host to SSH to. Use **ECS Exec** (SSM) to open a shell in the container, CloudWatch logs, and traces. The task definition must enable `enableExecuteCommand`, and the task role needs SSM permissions. On EKS, use `kubectl exec` against the pod.

---

## Sizing, storage, and networking

#### 8. How do CPU and memory sizing work on Fargate?

**Answer:** You pick a supported pair, not an arbitrary instance. For example, 0.25 vCPU only allows a small memory range, while 4 vCPU allows a much larger range. If the container exceeds its memory limit, the task is killed (OOM). CPU is a hard ceiling at the task size you requested. Size from real RSS and CPU profiles, then leave headroom for traffic spikes.

---

#### 9. Where does a Fargate container write files, and what are the limits?

**Answer:** The container filesystem is ephemeral. Default ephemeral storage is 20 GiB, and you can raise it up to 200 GiB in the task definition. It disappears when the task stops. For data that must survive, mount **EFS**, or write to S3. Fargate does not attach EBS as a node disk you manage yourself (ECS on Fargate can use configured ephemeral storage; durable shared files belong on EFS or S3).

---

#### 10. A Fargate task in a private subnet cannot pull its image from ECR. What is missing?

**Answer:** The task needs a path to ECR and to CloudWatch if you use the awslogs driver. Either:

* A NAT gateway so the task can reach public AWS endpoints, or
* VPC interface endpoints for ECR (`api` and `dkr`), S3 (the image layers), and CloudWatch Logs.

The execution role still needs `ecr:GetAuthorizationToken`, `BatchGetImage`, and `GetDownloadUrlForLayer`. A security group must allow outbound HTTPS.

---

#### 11. How does a Fargate service sit behind a load balancer?

**Answer:** Create an ECS service with a load balancer block pointing at a target group (usually an ALB, or an NLB). The target type is `ip`, because each task has its own ENI. ECS registers and deregisters task IPs as tasks start and stop. The container must serve the health-check path on the port you declared. The task security group must allow traffic from the load balancer security group.

---

#### 12. Why do new Fargate tasks fail the ALB health check for the first minute?

**Answer:** The process is still starting. Set a **health check grace period** on the ECS service so ECS does not kill the task before the app listens. Align the ALB health check interval, healthy threshold, and the app’s startup time. A grace period that is too short looks like a crash loop.

---

#### 13. What networking feature do you lose compared with EC2 containers?

**Answer:** You cannot use `host` or `bridge` network modes, `privileged` mode, or devices that need the host kernel (GPU, custom modules). `DAEMON` scheduling (one agent on every host) does not apply, because there are no hosts you own. Sidecars still work: they are extra containers in the same task, sharing the task ENI.

---

## Scaling and deployments

#### 14. How do you scale a Fargate service?

**Answer:** ECS service auto scaling (Application Auto Scaling) changes the **desired count** of tasks. Target tracking on CPU, memory, or ALB requests per target is the usual policy. There is no ASG of instances to scale first. Account and service quotas still cap how many vCPUs you can run at once.

---

#### 15. What is Fargate Spot, and which workloads fit it?

**Answer:** Fargate Spot runs tasks on spare capacity and can be interrupted with about two minutes’ notice. Use it for batch jobs, queue consumers that are idempotent, and stateless workers. Do not use it as the only capacity for a user-facing API unless you also keep an On-Demand base. ECS capacity providers can mix Fargate and Fargate Spot with a weight and a base.

---

#### 16. How does a rolling deploy work on Fargate?

**Answer:** The service has a minimum healthy percent and a maximum percent (for example 100 and 200). ECS starts new tasks from the new task definition, waits until they are healthy, then stops old tasks. A **deployment circuit breaker** rolls back automatically if new tasks never become healthy. Because you do not drain a node, the unit of replacement is the task.

---

#### 17. What is a platform version, and do you pin it?

**Answer:** A platform version is the Fargate runtime (host OS features, ephemeral storage behavior, and so on). `LATEST` follows AWS updates. Pin a version when you need a reproducible runtime for a regulated deploy, and plan to move forward, because old platform versions are retired. For most services, `LATEST` is fine.

---

#### 18. How do secrets get into a Fargate container without baking them into the image?

**Answer:** Reference Secrets Manager or SSM Parameter Store in the container `secrets` block of the task definition. The execution role must be allowed to read those secrets. ECS injects them as environment variables at start. The image stays free of credentials, and rotating the secret does not require a new image, only a new task.

---

## Failure and cost

#### 19. A task stops with exit code 137. What does that usually mean?

**Answer:** The process was killed with SIGKILL, most often an **out-of-memory** kill because the container crossed its memory limit. Check the task’s stopped reason in ECS and the memory metric. Raise the memory (and the matching CPU tier if required) or fix a leak. 137 can also be an external kill during deprovision, so read the stop reason before you only blame the app.

---

#### 20. Tasks stay in `PENDING` for several minutes. What do you look at?

**Answer:** Fargate is trying to place an ENI and pull the image. Common causes: no free IPs in the subnet, a security group or endpoint blocking ECR, a missing execution role, an image tag that does not exist, or a CPU quota. The service event list in ECS usually states the reason. Subnet IP exhaustion is very common because every task consumes an IP.

---

#### 21. How do you keep a queue worker from running twice during a deploy?

**Answer:** Make the consumer idempotent. On shutdown, the task receives SIGTERM; stop polling, finish or return the message, and exit before the stop timeout. Set the SQS visibility timeout longer than processing, and use a deployment that does not start unbounded extra consumers. Fargate will still kill the task if it ignores SIGTERM.

---

#### 22. Why can Fargate feel more expensive than a small EC2 cluster?

**Answer:** You pay for the size you request on every task, all the time it runs, and you cannot bin-pack many small tasks onto one instance you already paid for. A steady 24/7 service with high utilization is often cheaper on EC2 with a Savings Plan. Fargate wins when utilization is spiky, when the team is small, or when host patching is the larger cost.

---

#### 23. How do logs and metrics leave a Fargate task?

**Answer:** The `awslogs` log driver ships stdout and stderr to a CloudWatch log group. You do not install a host agent. Custom metrics can be published with the task role via `PutMetricData`, or you can run an OpenTelemetry sidecar in the same task. There is no node-level CloudWatch agent unless you add that sidecar yourself.

---

## Scenarios

#### 24. You must move an ECS-on-EC2 service to Fargate. What in the task definition will break?

**Answer:** Check network mode (`bridge` or `host` must become `awsvpc`), port mappings (no host port), privileged mode, extra `linuxParameters` devices, Docker volumes on the host, and `DAEMON` services. Links that assumed a shared bridge network must use localhost for sidecars or service discovery for other services. IAM must be split into execution role and task role if it was only an instance role before.

---

#### 25. An internal API on Fargate must be called only by other services in the VPC. How do you expose it?

**Answer:** Use an **internal** ALB in private subnets, target type `ip`, and a security group that allows the app port only from the caller security group. Do not give the tasks a public IP. Service Connect or Cloud Map is an alternative when you do not need HTTP load-balancing features.

---

#### 26. A batch job needs 100 GB of input, processes it, and writes a result to S3. How do you run it on Fargate?

**Answer:** Raise ephemeral storage enough for the input and working set (up to 200 GiB), or stream from S3 instead of downloading everything. Run it as a one-off task (`RunTask`) or a short-lived service fed by a queue. The task role can read and write S3. If the job regularly needs more than 200 GiB of local disk or a GPU, use EC2.

---

#### 27. During a deploy, users see connection resets for a few seconds. What is missing?

**Answer:** The load balancer is still sending traffic while the task is stopping, or the app is exiting before it finishes in-flight requests. Enable **deregistration delay** (draining) on the target group, handle SIGTERM by stopping the listener only after work completes, and keep the ECS stop timeout long enough for that drain. Health checks should fail the task out of rotation before it is killed.

---

#### 28. How do you give one Fargate service read access to a bucket and another service no access, in the same cluster?

**Answer:** Separate **task roles**. The cluster does not share one instance role the way EC2 launch types often do. Attach a role that allows `s3:GetObject` on that bucket to the first service’s tasks only. The second service’s role simply omits it.

---

#### 29. Fargate Spot interruptions are killing a user-facing API in the middle of the day. What change do you make?

**Answer:** Move the API to Fargate On-Demand, or set a capacity-provider strategy with a non-zero On-Demand **base** and only extra scale on Spot. The API tasks should drain on interruption, but user traffic should not depend on Spot alone.

---

#### 30. What would you check the morning after a Fargate service suddenly stopped scaling out?

**Answer:** ECS service events for quota errors (`vCPU limit`), subnet IP exhaustion, failed image pulls, a scaling policy whose metric stopped publishing, and a deploy stuck because new tasks are unhealthy so desired count cannot move. CloudWatch `RunningTaskCount` versus `DesiredTaskCount` shows whether the scheduler is behind.

---
