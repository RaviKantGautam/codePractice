# Amazon EC2 — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon EC2, and when would a backend service run on it instead of Lambda?

**Answer:** EC2 provides virtual machines (instances) in a VPC. You choose the OS image, instance size, storage, and network, and you are responsible for the OS, runtime, and process supervision.

Choose EC2 when the workload needs a long-running process, a custom runtime, GPU or high network throughput, persistent local state, or protocols and ports that do not fit a function. Lambda is a better fit for short, event-driven work where you do not want to manage a server.

---

#### 2. What is an AMI, and what is the difference between an AMI and a snapshot?

**Answer:** An AMI (Amazon Machine Image) is a template used to launch an instance: root volume, launch permissions, and block-device mapping. A snapshot is a point-in-time copy of a single EBS volume stored in S3.

An AMI often *references* snapshots of its volumes, but the AMI is what you launch. You snapshot a volume to back it up or to build a new AMI.

---

#### 3. What happens to data if you stop an instance versus terminate it?

**Answer:**

* **Stop:** The instance shuts down. The root EBS volume (and other EBS volumes) remain, and you can start the instance again. You are not billed for instance hours while it is stopped, but you still pay for EBS. Data on instance-store volumes is lost. A public IP usually changes unless you attached an Elastic IP. The private IP in the subnet is typically kept while stopped.
* **Terminate:** The instance is deleted. EBS volumes are deleted or kept according to the volume’s `DeleteOnTermination` flag. Instance-store data is gone.

---

#### 4. What is user data, and when does it run?

**Answer:** User data is a script or cloud-init config passed at launch. By default it runs **once**, on the first boot, as root. It is used to install packages, pull config, or start an agent.

It is not a reliable place for secrets (it is visible to anyone who can read instance metadata or the launch config). Prefer SSM Parameter Store, Secrets Manager, and an instance role.

---

#### 5. How does an application on EC2 get permission to call AWS APIs without storing access keys?

**Answer:** Attach an **IAM role** to the instance through an **instance profile**. The instance metadata service hands out temporary credentials that the AWS SDK refreshes automatically.

Never bake long-lived access keys into the AMI or user data. Scope the role to the APIs the process actually needs.

---

#### 6. What is the difference between a security group and a network ACL?

**Answer:**

| | Security group | Network ACL |
| --- | --- | --- |
| Scope | Instance (ENI) | Subnet |
| State | Stateful: return traffic is allowed automatically | Stateless: you must allow both directions |
| Rules | Allow only | Allow and deny |
| Evaluation | All matching allows apply | Rules evaluated in number order |

For most application traffic, security groups are the control you change day to day. NACLs are a coarse subnet firewall.

---

#### 7. What is an Elastic IP, and when is it a bad default?

**Answer:** An Elastic IP is a static public IPv4 address you can attach to an instance or a network interface. It survives stop/start.

It is a poor default for internet-facing apps. Prefer a load balancer with a stable DNS name so instances can be replaced. Elastic IPs also cost money when they are allocated and not attached to a running instance, and public IPv4 addresses are billed.

---

#### 8. What are instance store volumes, and when are they useful?

**Answer:** Instance store is temporary disk physically attached to the host. It is fast and included with some instance types, but it is wiped on stop, terminate, or host failure.

Use it for caches, scratch space, or buffers that can be rebuilt. Put anything you must keep on EBS, EFS, or S3.

---

## Networking and placement

#### 9. Why does an EC2 instance in a private subnet have no internet access even if it has a route to `0.0.0.0/0`?

**Answer:** A private subnet’s route to the internet must go through a **NAT gateway** (or NAT instance) in a public subnet. A route that points at an **internet gateway** only works for instances that themselves have a public IP. Private instances also need security groups and NACLs that allow the outbound traffic and, for NACLs, the return traffic.

---

#### 10. What is an ENI, and why might an instance have more than one?

**Answer:** An Elastic Network Interface is a virtual NIC with a primary private IP, optional secondary IPs, a MAC address, security groups, and an optional public IP.

Extra ENIs are used for management vs data networks, appliances that need multiple interfaces, or moving a fixed IP from a failed instance to a standby in the same subnet and AZ.

---

#### 11. What is the instance metadata service, and why is IMDSv2 preferred?

**Answer:** The metadata service at `169.254.169.254` exposes the instance id, IAM credentials, user data, and network config to software on the instance.

IMDSv1 answers a simple GET. IMDSv2 requires a session token from a PUT request first, which blocks most SSRF attacks that can only issue GET requests. Require IMDSv2 (`HttpTokens=required`) and hop limit `1` unless a container on the host needs a higher hop limit.

---

#### 12. What are placement groups, and which type would you pick for a low-latency cluster?

**Answer:**

* **Cluster:** instances packed close together in one AZ for the lowest latency and highest throughput. One rack or host failure can hit many nodes.
* **Spread:** each instance on distinct hardware, small groups, for a few critical nodes.
* **Partition:** instances split into partitions that do not share underlying hardware, used by large distributed systems (Hadoop, Kafka, Cassandra).

A low-latency cache or HPC mesh uses a **cluster** placement group, accepting the correlated-failure risk.

---

#### 13. How do you reach an instance that has no public IP for debugging?

**Answer:** Do not open SSH to the world. Common options:

* **SSM Session Manager**, using the SSM agent and an instance role with `AmazonSSMManagedInstanceCore`. No inbound port and no bastion.
* A bastion or SSM port forwarding if you truly need SSH.
* **EC2 Instance Connect** for short-lived SSH keys, still better combined with a locked-down security group.

---

## Operations

#### 14. What do the two EC2 status checks mean?

**Answer:**

* **System status check:** AWS-side problems (host hardware, network, power). Stop/start moves you to a new host and often clears it. Reboot does not.
* **Instance status check:** the OS is not responding (kernel panic, exhausted CPU, misconfigured network). Reboot or fix the guest. Stop/start also works but is heavier.

An Auto Scaling group should replace instances that fail health checks instead of leaving a human to reboot them.

---

#### 15. What is the difference between reboot, stop/start, and terminate from an operations point of view?

**Answer:**

* **Reboot:** same host, same disks, same public and private IPs. Like an OS reboot.
* **Stop/start:** new host, EBS volumes reattached, instance-store wiped, public IP usually changes. Use this when the underlying host is impaired.
* **Terminate:** instance is gone. Treat the AMI and user data as the way you rebuild it.

---

#### 16. How do you patch a fleet of EC2 instances without logging into each one?

**Answer:** Use **SSM Patch Manager** (or a pipeline that bakes a new AMI). The usual pattern is golden AMI: build and scan an image in CI, then roll the Auto Scaling group onto a new launch template version. In-place patching is fine for long-lived instances, but replacing instances is easier to roll back.

---

#### 17. What should you put in a launch template?

**Answer:** AMI id, instance type, key pair (if any), security groups, subnet or network interface, IAM instance profile, user data, EBS mapping, IMDSv2 requirement, monitoring, and tags. An Auto Scaling group should reference a launch template version, not a one-off “launch instance” click, so every replacement is identical.

---

#### 18. How do purchasing options change the price and the interruption risk?

**Answer:**

* **On-Demand:** no commitment, highest flexibility, can be interrupted only by you or a rare capacity issue.
* **Savings Plans / Reserved Instances:** commit to spend or to a specific usage for 1 or 3 years in exchange for a lower rate. The instance itself is not special.
* **Spot:** spare capacity at a large discount. AWS can reclaim it with a short interruption notice (typically two minutes). Good for workers that can checkpoint or be replaced.
* **Dedicated Hosts / Dedicated Instances:** hardware isolation for licensing or compliance. Much more expensive.

A stateless web tier is often Savings Plans plus an Auto Scaling group. Batch workers can be Spot.

---

#### 19. A deployment replaced the AMI, but running instances still serve the old build. Why?

**Answer:** Changing the launch template or AMI does not mutate instances that are already running. You have to start an **instance refresh** (or a rolling update) so the Auto Scaling group terminates old instances and launches new ones from the updated template. Confirm the ASG is using the new template **version**, not `$Default` or an old pinned version.

---

#### 20. How do you keep a root volume from being deleted on terminate, and when would you?

**Answer:** Set `DeleteOnTermination` to false on that volume. You would do this when the disk holds data you cannot rebuild and you are about to terminate or replace the instance. For stateless app servers, leave it true so terminated instances do not leak volumes and cost.

---

## Security and failure

#### 21. Your app on EC2 can read S3 in one environment and gets `AccessDenied` in another. What do you check first?

**Answer:**

1. The instance profile attached to **this** instance, not the role you think you attached in the console earlier.
2. The role’s identity policy and any permission boundary.
3. The S3 bucket policy, which can deny even when the role allows.
4. VPC endpoint policy, if the subnet uses an S3 gateway endpoint.
5. Whether the code is accidentally using env-var keys from the wrong account.

CloudTrail on the S3 data event or the encoded authorization failure message usually names the missing action.

---

#### 22. Why is opening port 22 to `0.0.0.0/0` a problem even with a key pair?

**Answer:** The instance is exposed to internet scanning. A stolen key, a vulnerable SSH version, or a weak user account is enough to get a shell. Security groups should allow SSH only from a known CIDR or, better, you should drop inbound SSH and use SSM.

---

#### 23. How would you design a single EC2 instance so that a process crash does not require a human?

**Answer:** Run the process under systemd (or similar) with `Restart=always`. Add a CloudWatch alarm on the process or on failed health checks, and an Auto Scaling group of size 1 with an ELB health check so a wedged OS is replaced. A single instance is still one failure domain; a real service uses at least two instances in two AZs behind a load balancer.

---

#### 24. What is termination protection, and what does it not stop?

**Answer:** Termination protection blocks an accidental `TerminateInstances` API call. It does **not** stop an Auto Scaling group from replacing the instance, a shutdown from inside the OS (unless shutdown behavior is set to stop), or deletion of the whole stack. Spot interruption also ignores it.

---

#### 25. How do EBS snapshots and AMIs fit into backup for an EC2-hosted database?

**Answer:** Snapshots are crash-consistent at the volume level. For a database, flush and freeze writes (or use the database’s own snapshot/backup tool, or RDS) before snapshotting, otherwise you can restore a torn page. Copy snapshots to another region if the recovery plan requires it. An AMI captures the boot disk so you can relaunch the host; it is not a substitute for logical database backups.

---

## Scenarios

#### 26. A private EC2 service must call a public SaaS API and also read from S3 and DynamoDB. How do you design the network path?

**Answer:** Put the instances in private subnets. Send S3 and DynamoDB traffic through **VPC gateway or interface endpoints** so it stays on the AWS network. Send the SaaS traffic through a **NAT gateway** in a public subnet. Security groups allow egress only where needed. The instance role covers AWS APIs; the SaaS credential lives in Secrets Manager.

---

#### 27. You need to run a weekly job that takes 6 hours and 200 GB of scratch disk. Lambda and Fargate both feel awkward. What do you use?

**Answer:** A scheduled job (EventBridge rule) that starts an EC2 instance, or a container on ECS with enough ephemeral disk, sized for the 6-hour run. EC2 fits when you want a specific instance store or a large EBS scratch volume and a simple “start, run, stop” lifecycle. Use Spot if the job can restart, and terminate the instance at the end so you do not pay for idle time.

---

#### 28. Users report timeouts after you moved the app into a new subnet. The process is running and the security group looks the same. What else changed?

**Answer:** Security groups are attached to the ENI, but the **subnet route table**, NACLs, and whether the subnet is public or private all changed with the move. A load balancer target group may also still point at the old instance or old port. Check the route to the load balancer or NAT, NACL ephemeral ports, and that the new ENI is in the target group and healthy.

---

#### 29. How do you roll out a risky app change on EC2 with a quick rollback?

**Answer:** Bake two AMIs (or two artifact versions pulled at boot). Put them in two launch template versions. Use an Auto Scaling instance refresh or a second target group and shift traffic at the load balancer. Rollback is “point the ASG or listener back at the previous template or target group” and refresh again. Feature flags reduce how often you need a full instance replace.

---

#### 30. What would you monitor on an EC2-backed HTTP service before you get paged at night?

**Answer:** ALB 5xx and target response time, healthy host count, EC2 CPU and status-check failures, disk usage and inode usage, memory if you installed the CloudWatch agent, and the application’s own error log metric filter. Alarm on **symptoms users feel** (error rate, latency, no healthy targets) more than on CPU alone.

---
