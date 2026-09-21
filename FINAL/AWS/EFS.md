# Amazon EFS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon EFS?

**Answer:** EFS (Elastic File System) is a managed **NFS** filesystem. Many EC2 instances, ECS tasks, and Lambda functions can mount the same file system at once and see the same files. It grows and shrinks with the data. You do not pick a volume size the way you do with EBS.

---

#### 2. When would you choose EFS instead of EBS or S3?

**Answer:**

* **EFS:** shared POSIX files across many compute nodes (user uploads processed by several workers, a shared config directory, CMS files).
* **EBS:** a disk for one instance in one AZ (database data directory, boot volume).
* **S3:** object PUT/GET, not file locking or append the way a program expects a disk.

If only one instance needs the data, EBS is simpler and usually faster. If clients only upload and download whole objects, S3 is the better fit.

---

#### 3. What is a mount target?

**Answer:** A mount target is an ENI in a subnet that clients use as the NFS endpoint. Create one mount target in each AZ where compute runs. Instances mount the AZ-local target so traffic stays in the AZ. The security group on the mount target must allow NFS (port 2049) from the client security group.

---

#### 4. What are storage classes on EFS?

**Answer:**

* **Standard** and **Standard-IA:** regional, stored across AZs.
* **One Zone** and **One Zone-IA:** cheaper, single AZ. An AZ loss can mean data loss. Do not use One Zone for the only copy of something you must keep.

Lifecycle management can move files that have not been accessed to IA. IA has a retrieval fee and a minimum duration. Small, frequently read files should stay in Standard.

---

#### 5. What performance modes and throughput modes matter?

**Answer:** EFS offers **General Purpose** performance (the right choice for almost all app workloads, with lower latency) and a legacy Max I/O mode you should not pick for new systems.

Throughput is **bursting**, **elastic**, or **provisioned**. Elastic grows with the workload and is the usual choice. Provisioned is for a steady high throughput you do not want tied to how much data you store. Bursting credits can run out on a small file system that suddenly reads a lot.

---

#### 6. How does an EC2 instance mount EFS?

**Answer:** Install the Amazon EFS mount helper (or use NFS directly), then mount the file system id, preferably via the helper so it uses TLS and the correct mount target. On boot, user data or a systemd unit should mount it, not a human. For ECS, declare an EFS volume in the task definition and a mount point in the container. The task security group must reach the mount target on 2049.

---

## Access and locking

#### 7. Can two writers use the same file?

**Answer:** NFS file locking exists, but many applications lock incorrectly or assume a local disk. Two processes appending to one log file will interleave or corrupt it. Design for **one writer per file**, or use a real queue or database for coordination. EFS is a shared disk, not a transaction manager.

---

#### 8. What is an access point?

**Answer:** An access point is an application-specific entry into the file system, with its own root directory and a forced POSIX user and group. Use it so a container can only see `/app-data` and writes files as a known uid. ECS and Lambda can mount an access point instead of the root of the file system. It is the main way to avoid every task sharing uid 0 over the whole tree.

---

#### 9. How does IAM authorization work with EFS?

**Answer:** You can require IAM to mount, in addition to the security group. The client role needs `elasticfilesystem:ClientMount` and, for writes, `ClientWrite`. This matters for Lambda and ECS, where you do not want “anyone in the subnet” to mount the data. Security groups still control the network path. IAM controls the identity.

---

#### 10. How do you connect Lambda to EFS?

**Answer:** The function must be in the same VPC and AZ connectivity as the mount targets. Configure the file system and an access point on the function. The execution role needs the EFS client actions. The function only sees the access point root. Cold starts get slower because the mount has to be ready. Do not put latency-critical tiny functions on EFS if S3 would do.

---

#### 11. What POSIX behaviors surprise people coming from S3?

**Answer:** Permissions, owners, and modes matter. A file written as root in one container is not writable by another user. Partial writes and file locks behave like NFS, including close-to-open consistency: a reader that already has a file open may not see a writer’s data until the writer closes and the reader reopens. Do not build a message queue out of lock files.

---

#### 12. What is the practical performance shape of EFS?

**Answer:** Latency is higher than a local EBS volume, especially for metadata-heavy work (thousands of tiny files, `ls` on huge directories, compilers, and some CMSs). Throughput is high for large sequential reads and writes. If the workload is “many small files and stat calls”, measure it. That pattern is the usual reason teams move back to EBS or redesign around S3.

---

## Operations and failure

#### 13. How do you back up EFS?

**Answer:** **AWS Backup** can take incremental backups on a schedule and restore the file system or a subset of files. EFS is redundant across AZs in the regional storage classes, but that does not protect you from a bad `rm -rf` or a buggy writer. Backups are how you return to yesterday. Replication to another region is for disaster recovery.

---

#### 14. What is EFS replication?

**Answer:** Replication keeps a copy of the file system in another region or account-style destination, asynchronously. The destination is read-only until you fail over. Use it when an AZ-redundant file system in one region is not enough. It is not a point-in-time snapshot you can browse as “last Tuesday” the way AWS Backup is. RPO is not zero.

---

#### 15. A mount hangs and the application is stuck. What do you check?

**Answer:** Security group on the mount target (TCP 2049 from the client), NACL ephemeral ports, whether the mount target exists in the instance’s AZ, and DNS resolution of the file system name (VPC DNS must be enabled). A mount option of `hard` will block IO until the network returns, which looks like a hung process. Check that the AZ is healthy and that you did not delete the mount target.

---

#### 16. Why did writes suddenly get slow after months of fine performance?

**Answer:** Bursting throughput credits are exhausted on a small file system, or you moved a large working set into IA and now pay latency on every read. CloudWatch metrics for `BurstCreditBalance`, percent IO limit, and storage class explain which one. Switch to elastic or provisioned throughput, or move the hot files back to Standard.

---

#### 17. How do you restrict one ECS service to one directory?

**Answer:** Create an **access point** with a root path such as `/payments` and a POSIX uid/gid the container runs as. Mount that access point in the task definition. A second service gets a different access point. This is not a full security boundary against root in the container, so do not run the container as root if the data is sensitive.

---

#### 18. Can you use EFS for a relational database?

**Answer:** You should not. Databases expect a dedicated low-latency disk and specific fsync behavior. Use RDS, Aurora, or EBS on a single instance. EFS is for shared files. Running MySQL data directories on NFS is a common way to corrupt a database.

---

#### 19. How does encryption work?

**Answer:** Encryption **at rest** uses a KMS key you choose when you create the file system. You cannot turn it on later. Encryption **in transit** is TLS through the EFS mount helper (`tls` mount option). Enable both for anything that holds customer data. IAM authorization is often combined with TLS.

---

#### 20. What breaks if you only create a mount target in one AZ?

**Answer:** Instances and tasks in other AZs either cannot mount or they cross AZs for every IO, adding latency and data-transfer cost. If that AZ fails, every client loses the filesystem even though regional EFS data is still stored across AZs. Create a mount target in each AZ you run compute in.

---

## Scenarios

#### 21. Several Fargate tasks must read a shared config file that changes a few times a day. Is EFS the right tool?

**Answer:** It works, but it is heavy for a few kilobytes. Parameter Store, Secrets Manager, S3, or AppConfig are simpler and have a clearer refresh story. Use EFS when the shared data is real files the program opens by path (templates, user uploads, a tree of assets), not when you only needed a config API.

---

#### 22. Two workers must process files dropped in a directory, and each file must be processed once. How do you avoid double processing?

**Answer:** Do not rely on “whoever sees the file first”. Have the producer write to an `incoming` directory and then rename into a `ready` directory (rename is atomic on the same file system). A worker renames the file into `processing` before it starts, so the other worker will not see it. On success, move it to `done`. A queue (SQS) plus S3 is still cleaner if you can change the design.

---

#### 23. You moved a service from one EC2 instance with EBS to three instances and pointed them all at EFS. Pages got slower. Why?

**Answer:** Local EBS latency is lower than NFS, and the app may be doing many small reads and stat calls that were cheap on a local disk. Check whether the working set is in IA, whether throughput credits are gone, and whether all three instances mount the local AZ’s target. Caching hot files in memory or keeping a local disk for temp files, with EFS only for the shared durable files, is the usual fix.

---

#### 24. A container writes a file as root and a second container cannot read it. What happened?

**Answer:** The file mode or owner blocks the second process’s uid. Access points can force a uid so both containers write as the same user. Align the container `user` in the task definition with that uid, and set a umask or an explicit mode in the writer. This is ordinary Unix, made visible because the filesystem is now shared.

---

#### 25. How do you restore one deleted directory without rolling the whole system back?

**Answer:** Restore from **AWS Backup** into a new file system or use item-level recovery where the backup plan supports it, then copy the directory back. Replication will not help if the delete already replicated. Versioning like S3 does not exist on EFS. The operational control is backup frequency versus how much data you can afford to lose.

---

#### 26. Lambda functions in two AZs time out on first use of EFS. What is misconfigured?

**Answer:** Mount targets missing in one AZ, the Lambda security group not allowed on port 2049, or the function’s subnets are private and DNS cannot resolve the EFS name. Also confirm the access point exists and the role has `ClientMount`. A too-short function timeout hides the mount latency on a cold start. Raise the timeout and fix the network path.

---

#### 27. How would you migrate a large tree off a self-managed NFS server onto EFS?

**Answer:** Use **AWS DataSync** or `rsync` over a mounted source and destination. DataSync is the managed option and can verify files. Plan a cutover window: final sync, stop writers, sync again, remount clients on EFS. Check ownership, symlink behavior, and that file names are compatible. Do not point production at EFS until a test client has listed and read the tree.

---

#### 28. What CloudWatch signals tell you EFS is the bottleneck?

**Answer:** `PercentIOLimit`, `PermittedThroughput` versus actual throughput, `BurstCreditBalance` near zero, and high client-side NFS latency in the app. Storage bytes growing without a matching access pattern tells you lifecycle to IA may help cost but will hurt reads. Alarm on IO limit percent and on burst credits if you still use bursting mode.

---

#### 29. A One Zone file system was chosen to save money. What risk do you accept?

**Answer:** The data lives in one AZ. An AZ outage or loss can make the data unavailable or destroy it. There is no second AZ copy. That is acceptable for rebuildable caches and CI artifacts, not for customer uploads you cannot recreate. Regional Standard costs more and survives an AZ failure.

---

#### 30. How do you decide the throughput mode for a new shared upload directory?

**Answer:** Start with **elastic** throughput so a spike of uploads does not depend on burst credits, and use the regional Standard storage class if the files are read after upload. Measure for a week. Move to provisioned only if the bill or the latency of elastic is worse than a known steady rate. Put a lifecycle policy on files that age out of the working set so they move to IA.

---
