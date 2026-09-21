# AWS Auto Scaling — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS Auto Scaling in practice for a backend service?

**Answer:** People say “Auto Scaling” for two related things. An **EC2 Auto Scaling group (ASG)** keeps a desired number of instances running and replaces unhealthy ones. **Application Auto Scaling** adjusts other targets: ECS service desired count, DynamoDB capacity, Aurora replicas, and similar. Both react to a schedule or to a CloudWatch metric. Neither fixes an application that cannot run more than one copy.

---

#### 2. What are minimum, maximum, and desired capacity on an ASG?

**Answer:**

* **Minimum:** the group will not scale in below this. Also the floor during an AZ failure if you have set it across subnets.
* **Maximum:** the group will not scale out above this, even if the metric says to.
* **Desired:** how many instances the group wants right now. Scaling policies change desired. You can set it manually too.

If desired is 4, min is 2, and max is 10, a target-tracking policy can move desired between 2 and 10.

---

#### 3. What does an ASG use to launch instances?

**Answer:** A **launch template** (AMI, instance type, security groups, IAM profile, user data, subnet or the group’s VPC zone list). The ASG should point at a template version. When you need a new build, you create a new template version and start an **instance refresh**. Editing the template does not change instances that are already running.

---

#### 4. How does an ASG decide an instance is unhealthy?

**Answer:** By **EC2 status checks** and, if you enable them, **Elastic Load Balancing health checks**. When ELB health checks are on, an instance that fails the target-group health check is replaced even if the OS is still up. That is what you want for a web service: a process that is wedged should not stay in the group. Grace periods stop the group from killing an instance that is still booting.

---

#### 5. What is the health check grace period?

**Answer:** The number of seconds after launch during which the ASG ignores failing health checks. Set it longer than boot plus application startup. Too short, and every deploy looks like a crash and the group replaces instances forever. Too long, and a truly bad AMI stays in service.

---

#### 6. What happens when an instance fails in an ASG?

**Answer:** The ASG marks it unhealthy, terminates it, and launches a replacement to bring desired capacity back, preferably in a subnet that still has capacity. Attached EBS data is kept or deleted based on `DeleteOnTermination`. Anything only on instance store is gone. The application must be able to start from the AMI and user data alone.

---

## Scaling policies

#### 7. What is target tracking, and why is it the usual choice?

**Answer:** You set a metric and a target value, for example average CPU at 50 percent or ALB request count per target at 1000. AWS adds or removes capacity to hold that line. It builds the CloudWatch alarms for you. Use it unless you have a reason to write step policies. Scale on a metric that matches load (request count, queue depth), not only CPU, if CPU stays low while the app is busy waiting on IO.

---

#### 8. What is the difference between step scaling and simple scaling?

**Answer:** **Simple scaling** waits for a cooldown after each change before it can change again. **Step scaling** can apply different adjustments for different alarm bands (for example +1 instance above 60 percent CPU, +3 above 80 percent) and uses warm-up instead of a single cooldown. Target tracking is still simpler for most HTTP services. Step scaling fits when you know the jumps you want.

---

#### 9. What is a cooldown versus instance warm-up?

**Answer:** **Cooldown** (simple scaling) pauses all scaling activity so a new instance’s metrics do not immediately trigger another change. **Warm-up** tells target tracking and step scaling how long a new instance should be ignored in the metric, while other scaling can still happen. Set warm-up to the time until the instance is serving real traffic. A short warm-up causes flapping. A long one makes scale-out feel late.

---

#### 10. What is scheduled scaling, and when do you add it?

**Answer:** Scheduled actions set min, max, or desired at a cron time. Use them when you know the pattern: office-hours traffic, a Monday batch, a sale that starts at 09:00. Predictive scaling (part of AWS’s scaling options) forecasts from history. Scheduled actions are easier to explain in an incident. Combine them with target tracking for the unexpected spikes inside the day.

---

#### 11. What is scale-in protection?

**Answer:** A flag on an instance that tells the ASG not to terminate it when scaling in. Use it for a long job that must finish, or a one-off debug instance you placed in the group. If you forget to clear it, the group cannot scale in and you keep paying. Do not enable it on every instance by default.

---

#### 12. How does an ASG spread instances across Availability Zones?

**Answer:** You attach one subnet per AZ. The group tries to keep the counts balanced. If an AZ fails, later scale-out uses the remaining subnets. Rebalancing can terminate an instance in a crowded AZ and launch one in a sparse AZ. For stateful instances that cannot be killed, that default is dangerous. Stateless instances behind a load balancer are the model that matches ASG.

---

## Load balancers, hooks, and Spot

#### 13. How should an ASG work with an ALB?

**Answer:** Register the ASG with the target group. New instances are registered when they launch. ELB health checks should be enabled on the ASG. Set **deregistration delay** on the target group so an instance is drained before terminate. The application must pass the health check only when it can serve traffic, not merely when the OS has booted.

---

#### 14. What is a lifecycle hook?

**Answer:** A pause during launch or terminate where the instance sits in `Pending:Wait` or `Terminating:Wait` until a heartbeat completes the action or the timeout expires. Use a terminating hook to finish a queue message, copy logs, or deregister from a cluster. Use a launching hook when setup must finish before the instance is `InService`. If the hook never completes, the instance sits until the timeout, and scale-out looks stuck.

---

#### 15. What are termination policies?

**Answer:** The order the ASG uses to pick which instance to kill on scale-in. The default prefers instances across AZs for balance, then the oldest launch template, then the instance closest to the next billing hour. You can prefer the oldest instance so new code stays. You cannot get a perfectly gentle policy. Design the app so any instance can die.

---

#### 16. What is an instance refresh?

**Answer:** A rolling replacement that launches instances from the current launch template and terminates old ones, with a minimum healthy percentage. This is how you roll an AMI or user-data change through the group. Checkpoints can pause the refresh for verification. If new instances fail health checks, the refresh should be rolled back rather than left half-finished.

---

#### 17. How do mixed instances and Spot work in an ASG?

**Answer:** A mixed-instances policy lists instance types and a split between On-Demand and Spot. The group launches a **base** of On-Demand and puts the rest on Spot, or uses a percentage. Diversify instance types so a Spot shortage in one type does not stall scale-out. Spot can be interrupted with about two minutes’ notice. Do not use Spot alone for the only copy of a stateful service.

---

#### 18. What is the difference between ASG scaling and ECS service auto scaling?

**Answer:** An ECS **service** scales the number of **tasks**. On Fargate that is the only loop. On ECS with EC2, tasks need free CPU and memory on container instances, so a **capacity provider** also scales the ASG of instances. Scaling the ASG without scaling the service just adds empty hosts. Scaling the service without capacity leaves tasks in `PENDING`.

---

## Failure and scenarios

#### 19. The ASG is at maximum capacity and latency is still high. What is going on?

**Answer:** The policy did its job and stopped at **max**. Raise max if the account quota and the budget allow it, and check that the extra instances would help. If the database is the bottleneck, more instances make it worse. Confirm new instances are healthy and receiving traffic. A target-tracking metric that is flat (for example CPU while threads are blocked on a lock) will also refuse to scale.

---

#### 20. Instances launch and are immediately terminated in a loop. What do you check?

**Answer:** Health check grace period too short, health check path wrong, security group blocking the load balancer, user data failing so the process never listens, or an AMI that crashes on boot. Look at ASG activity history and the system log. A bad launch template rolled out to 100 percent will keep cycling until you stop the refresh and fix the template.

---

#### 21. You set desired capacity to 6, but only 4 instances are running. Why might that be?

**Answer:** The AZ or instance type is out of capacity, an account vCPU quota is hit, a launch failure (bad AMI, encrypted EBS key the role cannot use, subnet out of IPs) is retrying, or a lifecycle hook is holding instances in `Pending:Wait`. The activity tab shows the error. Desired is a request, not a guarantee.

---

#### 22. How do you scale on SQS queue depth?

**Answer:** Target tracking supports the `ApproximateNumberOfMessagesVisible` metric, often expressed as a backlog per instance (messages divided by running instances) using metric math. Each instance runs a worker. Scale out when the backlog per instance rises. Scale-in must be slow enough that you do not kill workers mid-batch. The worker has to tolerate interruption. A tiny queue that fluctuates around zero will flap if the target is too sensitive.

---

#### 23. What is the risk of scaling on CPU alone for a web API?

**Answer:** The API can be slow because of database waits, lock contention, or a full connection pool while CPU stays at 20 percent. The ASG will not grow. Prefer ALB **RequestCountPerTarget** or a custom latency metric, and still alarm on latency and 5xx. CPU-based scaling fits CPU-bound workers better than IO-bound HTTP handlers.

---

#### 24. How do you do a blue/green deploy with an ASG?

**Answer:** Launch a second ASG from the new template, attach it to a second target group, and shift the ALB listener weight from the old group to the new one. Roll back by shifting weight back. Instance refresh is a simpler rolling replace inside one group when you do not need an instant cutback. Blue/green costs more while both groups are up.

---

#### 25. An instance is unhealthy only in one AZ. Should you turn the AZ off?

**Answer:** First check whether the subnet route, NACL, or a zonal dependency (a single-AZ database, a missing NAT) is the cause. If the AZ itself is impaired, the ASG will launch replacements in other subnets as instances fail, as long as max capacity and IP space allow it. Manually disabling an AZ is an incident action, not the steady-state design. Steady state is at least two subnets and stateless instances.

---

#### 26. How do lifecycle hooks and a terminating scale-in interact with a long request?

**Answer:** On scale-in the instance is deregistered from the load balancer, waits the deregistration delay, then terminates. If a lifecycle hook is configured, your script can wait for in-flight work and then call `CompleteLifecycleAction`. If the request is longer than the deregistration delay and the hook timeout, the client is cut off. Align those timers with the longest request you are willing to accept, or make the work resumable.

---

#### 27. What IAM permissions does the ASG itself need versus the instance?

**Answer:** The instance profile is for the **application** (S3, DynamoDB, SSM). The ASG launches instances using your user or a service-linked role (`AWSServiceRoleForAutoScaling`), which needs to pass that instance profile and to register targets if you use a load balancer. A common failure is `PassRole`: the deployer can create a group but cannot attach the instance profile. That is an IAM configuration error, not an AMI error.

---

#### 28. How would you protect a database from a scale-out storm?

**Answer:** Cap ASG **maximum** size, scale gradually (warm-up, step adjustments that are not huge), and use reserved concurrency if the tier is Lambda. The database should have connection pooling (RDS Proxy, or a pool sized as connections per instance times max instances). An unbounded max plus a CPU target of 30 percent can open hundreds of connections and take the database down, which then makes the app slower, which scales out more.

---

#### 29. What is predictive scaling, and when is it optional?

**Answer:** Predictive scaling uses past days of load to pre-launch capacity before a repeating peak, so you are not late. It is optional. Turn it on when traffic is regular and scale-out is too slow for the spike (large AMIs, slow boot). It is not a substitute for a max cap and a target-tracking policy for surprises. If the traffic pattern changes (a new product launch), the forecast is wrong until history catches up. Keep scheduled actions for events you know that the model has never seen.

---

#### 30. What would you put on a dashboard for an ASG-backed service?

**Answer:** Desired, in-service, and pending counts, healthy hosts in the target group, ALB 5xx and latency, scaling activities (launch and terminate failures), and the metric the policy tracks. Alarm when in-service stays below desired, when healthy hosts drop, and when launch failures repeat. CPU on one instance is less useful than “are we at max and still slow?”.

---
