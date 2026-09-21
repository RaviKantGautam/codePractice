# Amazon ECS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon ECS, and what are its main objects?

**Answer:** ECS (Elastic Container Service) runs Docker containers on AWS. The objects you work with are:

* **Cluster:** a logical group of capacity (Fargate, EC2 instances, or both).
* **Task definition:** a blueprint (image, CPU, memory, ports, roles, logs).
* **Task:** one running copy of that blueprint.
* **Service:** keeps a desired count of tasks running and wires them to load balancers and deployments.

---

#### 2. How is ECS different from EKS?

**Answer:** ECS is AWS’s own orchestrator. You describe tasks and services with ECS APIs, not Kubernetes manifests. EKS runs upstream Kubernetes. ECS is simpler for a team that only deploys on AWS. EKS fits when you already use Kubernetes, need its ecosystem, or want the same manifests in more than one cloud.

---

#### 3. What is the difference between a task and a service?

**Answer:** A task is a single run. You use `RunTask` for jobs, migrations, and one-off scripts. A service supervises tasks: it restarts them, rolls out new task-definition revisions, and registers them with a load balancer. A web API is a service. A nightly report is usually a task.

---

#### 4. What belongs in a task definition?

**Answer:** Family name, launch type or capacity-provider strategy, CPU and memory, one or more container definitions (image, command, port mappings, environment, secrets), log configuration, execution role, task role, network mode, and optional volumes. You revise the definition to ship a new image; you do not edit a running container in place.

---

#### 5. What is a container definition versus a task definition?

**Answer:** A task definition can hold several containers that always start and stop together (an app plus a log router or a proxy sidecar). Each container definition is one of those containers. They share the task’s network namespace on `awsvpc`, so sidecars reach the app on `localhost`.

---

#### 6. When would you run ECS on EC2 instead of Fargate?

**Answer:** When you need GPUs, privileged mode, a custom AMI, daemon agents on every host, or dense bin-packing to cut cost. EC2 also fits large disks and instance-store workloads. Fargate is the default when none of those constraints apply.

---

## Networking and IAM

#### 7. What are ECS network modes, and which one do services behind an ALB usually use?

**Answer:**

* **awsvpc:** task gets its own ENI and IP. Required on Fargate. ALB target type is `ip`.
* **bridge:** Docker bridge on the EC2 host, with a dynamic host port. ALB target type is `instance`.
* **host:** container uses the host network directly. Port conflicts if two tasks need the same port.

New services should use **awsvpc** unless you are maintaining an older EC2 cluster.

---

#### 8. Why do ECS tasks need two IAM roles?

**Answer:**

* **Task execution role:** the ECS control plane pulls from ECR, sends logs, and reads secrets declared in the task definition.
* **Task role:** your process calls AWS APIs.

On the EC2 launch type, the **instance role** is a third identity: it lets the ECS agent register the host. Application permissions should still be the task role, not the instance role, so every container on the box does not share the same power.

---

#### 9. How does an ECS service connect to an Application Load Balancer?

**Answer:** The service is configured with a target group, container name, and container port. ECS registers task IPs (awsvpc) or instance:port (bridge) as tasks become healthy, and deregisters them on stop. You still own the listener rules (host, path) and the health check. The target group health check and the ECS service health check are related but not the same setting.

---

#### 10. What is ECS service discovery?

**Answer:** ECS can register tasks in **AWS Cloud Map** under a private DNS name. Other services resolve `api.internal` and get current task IPs. Use it for service-to-service calls that do not need an ALB. **Service Connect** is the newer ECS feature that adds a managed proxy and simpler client-side names inside the cluster.

---

#### 11. A task can be placed, but the app cannot reach RDS in the same VPC. What do you check?

**Answer:** The task security group must be allowed on the RDS security group. The task must be in a subnet that can route to the database subnets. For `awsvpc`, the IP that RDS sees is the task IP, not the EC2 host IP. DNS must resolve the RDS endpoint, which requires the VPC DNS settings or a resolver path.

---

## Deployments and scaling

#### 12. How does ECS roll out a new image?

**Answer:** You register a new task-definition revision (new image tag or digest) and update the service to that revision. ECS starts new tasks and stops old ones according to **minimumHealthyPercent** and **maximumPercent**. Example: min 100, max 200 launches the new tasks first, then drains the old ones. Min 50, max 100 replaces tasks in place and uses less spare capacity.

---

#### 13. What does the deployment circuit breaker do?

**Answer:** If new tasks repeatedly fail to become healthy, ECS stops the deployment and rolls the service back to the previous revision. Without it, a bad image can sit in a loop of start, fail health check, kill, start. Turn it on for production services, and alarm on `DeploymentFailed` events.

---

#### 14. How do you scale ECS tasks, and how is that different from scaling EC2 instances in the cluster?

**Answer:** **Service auto scaling** changes the desired task count (CPU, memory, or request count). On Fargate that is enough. On EC2, tasks only start if the cluster has CPU and memory left, so you also scale the **Auto Scaling group** of container instances, often with a capacity provider based on reservation. Forgetting the second loop is why tasks stay `PENDING` with “insufficient memory”.

---

#### 15. What is a capacity provider?

**Answer:** A link between a service and a pool of capacity: an EC2 Auto Scaling group, Fargate, or Fargate Spot. A strategy sets a **base** (minimum tasks on a provider) and **weights** (how extra tasks split). Example: base 2 on Fargate On-Demand, then weight Spot higher for burst. The service stops choosing a launch type directly.

---

#### 16. What is the difference between a rolling update and a blue/green deploy on ECS?

**Answer:** A rolling update replaces tasks inside one service. Blue/green, through **CodeDeploy**, runs a second set of tasks and shifts ALB listener traffic (canary or all-at-once), then terminates the old set. Blue/green gives a faster traffic cutback. It needs extra capacity and a CodeDeploy application configured for ECS.

---

#### 17. How should a consumer handle ECS task shutdown?

**Answer:** ECS sends **SIGTERM**, waits `stopTimeout` (default 30 seconds), then SIGKILL. The process should catch SIGTERM, stop taking new work, finish or release in-flight messages, and exit. For ALB services, deregistration delay must fit inside that window so the load balancer stops sending requests before the process dies.

---

## Operations and failure

#### 18. What does it mean when a task is `PENDING`, `RUNNING`, or `STOPPED`?

**Answer:**

* **PENDING:** accepted, but the image is pulling or capacity/ENI is not ready.
* **RUNNING:** the essential containers are up. The app can still be failing its load-balancer health check.
* **STOPPED:** the task ended. Read `stoppedReason` and the container exit code. Essential container exit stops the whole task.

---

#### 19. Why does ECS restart your task when the main container exits, but not always when a sidecar exits?

**Answer:** Containers are marked **essential** or not. If an essential container exits, the task stops and a service will start a replacement. A non-essential sidecar can exit without stopping the task. Your application container should be essential.

---

#### 20. How do you run a database migration exactly once before new code serves traffic?

**Answer:** Do not hide it in every container entrypoint, or every task will migrate concurrently. Run a one-off task (`RunTask`) in the pipeline, wait for exit code 0, then update the service. The migration needs the same network path and task role as the app, and it should be backward compatible with the still-running old tasks until the rollout finishes.

---

#### 21. Where do you look when a service is stuck and will not stabilize?

**Answer:** The service **events** tab (placement failures, health checks), the stopped task reason, CloudWatch logs from the container, and the target group’s healthy host count. Then check image architecture (arm64 vs amd64), secrets the execution role cannot read, and a health check path that the app does not serve.

---

#### 22. How do you keep an image tag from moving underneath a running deployment?

**Answer:** Do not deploy mutable tags such as `latest` in production. Publish an immutable tag or deploy by **image digest**. ECR tag immutability and a lifecycle policy that expires untagged images support that habit. The task definition should pin what you tested.

---

#### 23. What is ECS Exec, and what extra access does it create?

**Answer:** ECS Exec lets you open a shell in a running container through SSM, including on Fargate. It is useful for debugging and dangerous if left open for everyone. Enable it per service, restrict the IAM permission to a break-glass role, and send session logs to CloudWatch or S3.

---

## Scenarios

#### 24. Two copies of a worker process a message at the same time after a deploy. The code is a single consumer loop. What happened?

**Answer:** The old task was still running while the new task started (maximum percent above 100), and the old process did not stop polling on SIGTERM. Both called `ReceiveMessage`. Fix shutdown handling, and make processing idempotent. If the queue is FIFO, also check that you did not increase concurrency inside one message group.

---

#### 25. You moved a service from bridge mode to awsvpc and the ALB targets went unhealthy. What is the usual mismatch?

**Answer:** The target group is still type `instance`, or the health check still uses the old dynamic host port. Awsvpc needs target type `ip` and the container port. The security group on the task ENI must allow the ALB, not only the EC2 host security group.

---

#### 26. A cluster of EC2 container instances shows free CPU in CloudWatch, but tasks will not place. Why?

**Answer:** ECS placement uses **reserved** CPU and memory on the container instance, not live utilization. A task that asks for 1 GB still occupies 1 GB even if the process is idle. Fragmentation also matters: 2 GB free split across hosts cannot place a task that needs 2 GB on one host. Look at remaining reservation, not guest CPU percent.

---

#### 27. How would you run a log router next to every app container without putting it in every image?

**Answer:** Add a sidecar container (Fluent Bit or the AWS Distro for OpenTelemetry) to the task definition, sharing `localhost` on awsvpc. The app writes to a local port or a shared volume, and the sidecar ships logs. On EC2, a daemon service is the other option: one agent per host. Fargate has no daemon service, so the sidecar is the pattern.

---

#### 28. Production must stay up if one Availability Zone is lost. What do you set?

**Answer:** Subnets in at least two AZs, desired count of at least two tasks, and a spread placement so tasks are not all in one zone. The load balancer spans those subnets. On EC2, the Auto Scaling group also spans the AZs. A minimum healthy percent that allows the service to run with one task missing avoids a stuck deploy during the failure.

---

#### 29. A secret rotated in Secrets Manager, but running tasks still use the old value. Why?

**Answer:** Secrets in the task definition are resolved when the task **starts**. Running processes keep the environment they were given. Force a new deployment after rotation, or have the app reload the secret itself. Confirm the execution role can read the new version and that the definition does not pin an old version stage.

---

#### 30. What is a practical CI/CD path for an ECS service?

**Answer:** CI builds the image, scans it, and pushes it to ECR with the git SHA as the tag. The deploy step registers a new task-definition revision with that tag and calls `UpdateService`. CodePipeline can chain CodeBuild and an ECS deploy action, or the same calls can live in GitHub Actions. The pipeline should wait until the service is stable and fail the job if the circuit breaker rolls back.

---
