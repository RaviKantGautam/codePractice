# Amazon EBS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon EBS?

**Answer:** EBS (Elastic Block Store) is network-attached block storage for EC2. A volume looks like a disk to one instance. You partition it, put a filesystem on it, and mount it. Volumes are stored redundantly in **one Availability Zone**. They are not shared by many instances the way EFS is, except for specially designed multi-attach volumes.

---

#### 2. How is EBS different from instance store and from EFS?

**Answer:**

* **EBS:** durable across stop/start, tied to one AZ, attached to one instance (typical).
* **Instance store:** local disk on the host, very fast, erased when the instance stops or the host fails.
* **EFS:** shared NFS across AZs and many clients.

Boot disks are usually EBS. Scratch and caches can be instance store. Shared files belong on EFS or S3.

---

#### 3. What volume types should you know?

**Answer:**

| Type | Use |
| --- | --- |
| **gp3** | Default general-purpose SSD. You set IOPS and throughput independently of size. |
| **gp2** | Older general-purpose SSD. IOPS scale with size and bursting. Prefer gp3 for new volumes. |
| **io2 / io2 Block Express** | Sustained high IOPS and stronger durability for databases that need a performance SLA. |
| **st1** | Throughput-optimized HDD for large sequential IO (logs, warehouses). |
| **sc1** | Cold HDD, cheapest, infrequent sequential access. |

Do not put a random-IO database on sc1 or st1.

---

#### 4. What does it mean that a volume is AZ-bound?

**Answer:** A volume in `ap-south-1a` can only attach to an instance in `ap-south-1a`. You cannot move it to another AZ as a live attachment. To run in another AZ you create a **snapshot** and then a new volume from that snapshot in the target AZ. An ASG that launches in several AZs needs its root volume created in whichever AZ the instance lands in. The launch template does that for the root disk.

---

#### 5. What is a snapshot?

**Answer:** A snapshot is an incremental, point-in-time copy of a volume, stored in S3 (you do not see the bucket). The first snapshot copies the used blocks. Later snapshots store changes. You create a volume or an AMI from a snapshot, including in another region if you copy the snapshot there. Snapshots are the backup and the copy mechanism for EBS.

---

#### 6. Are snapshots consistent if the disk is being written?

**Answer:** A snapshot is **crash-consistent**: it matches a sudden power loss. For a database that is a risky restore point. Flush and freeze the filesystem or use the database’s backup tool (or RDS) before you snapshot. AWS also offers application-consistent snapshots through VSS on Windows and through scripts coordinated with Systems Manager. Do not assume a live MySQL data directory snapshot is clean.

---

## Performance and attachment

#### 7. Why is gp3 usually a better default than gp2?

**Answer:** On gp2, IOPS are tied to volume size (3 IOPS per GiB, with bursting). People grew disks they did not need just to buy IOPS. On gp3, a volume has a baseline (3,000 IOPS and 125 MB/s) and you can raise IOPS and throughput without adding gigabytes. You pay for the extra performance directly. New volumes should be gp3 unless a benchmark says otherwise.

---

#### 8. What limits EBS performance besides the volume type?

**Answer:** The **instance type** has a maximum EBS bandwidth and IOPS. A large io2 volume on a small instance will not reach the volume’s numbers. Also, the first read of a block restored from a snapshot is slower until the block is pulled in, unless you enable **fast snapshot restore** or pre-warm. Initialize new volumes from snapshots before a performance test.

---

#### 9. What is EBS multi-attach, and when is it safe?

**Answer:** io1 and io2 volumes can attach to more than one instance in the same AZ, with a cap on attachments. The filesystem must be a clustered filesystem that understands shared disks (not ext4 or xfs mounted read-write on two nodes). Most applications should not use multi-attach. It is for specialized storage designs. Two EC2 instances mounting one ext4 volume read-write will corrupt it.

---

#### 10. What is DeleteOnTermination?

**Answer:** A flag on the volume attachment. If true, terminating the instance deletes the volume. Root volumes often default to true. Data volumes you care about should be false until you have snapshots, or you will delete the only copy when the ASG replaces the instance. Stop does not delete the volume either way.

---

#### 11. What happens to an EBS volume when you stop an instance?

**Answer:** The volume remains and stays attached in the metadata sense. You are billed for the storage. You are not billed for instance hours. Data on the volume is kept. You can start the instance again, possibly on a different host, and the volume is reattached. You cannot detach a root volume from a running instance. You can detach a non-root volume and attach it to another instance in the same AZ.

---

#### 12. How do you resize a volume?

**Answer:** Increase the EBS volume size (you generally cannot shrink). Then extend the partition and the filesystem inside the OS (`growpart` and `resize2fs` or `xfs_growfs`). CloudWatch will not do that for you. Take a snapshot first. gp3 IOPS and throughput can also be changed without growing the disk.

---

## Encryption, backup, and cost

#### 13. How does EBS encryption work?

**Answer:** You encrypt a volume with a KMS key at creation time. Snapshots of an encrypted volume are encrypted. Volumes created from those snapshots are encrypted. There is no supported way to turn encryption off later. To encrypt an existing unencrypted volume: snapshot it, copy the snapshot with encryption enabled, and create a new volume. The instance type must support encrypted volumes (all current ones do).

---

#### 14. Who can read an encrypted snapshot?

**Answer:** Anyone who can use the KMS key and has IAM permission on the snapshot. Sharing a snapshot with another account also requires sharing the KMS key. A snapshot copied to a backup account with a key that account controls is safer than sharing the production key. The root volume of an AMI is just a snapshot. Encrypt it if the disk holds secrets or customer data.

---

#### 15. How should a self-managed database on EC2 be backed up?

**Answer:** Prefer the database’s own dump or physical backup tool, sent to S3, plus a documented restore drill. EBS snapshots are a second layer if you freeze IO first. RDS or Aurora removes this work. If you stay on EC2, automate snapshots with **Amazon Data Lifecycle Manager** or AWS Backup, copy them to another region, and test a restore onto a new instance. A snapshot you have never restored is a hope, not a backup.

---

#### 16. What is Amazon Data Lifecycle Manager?

**Answer:** A policy that creates and deletes EBS snapshots or AMIs on a schedule, with retention counts. Use it so disks are not backed up by a forgotten cron on one instance. Target volumes by tags. Combine it with a cross-region copy if the recovery plan needs another region.

---

#### 17. Why is an unattached volume still on the bill?

**Answer:** You pay for provisioned storage whether or not an instance is attached, and you pay for snapshots separately. Terminated instances with `DeleteOnTermination` false leave orphan volumes. Tag volumes with the service name and alarm or budget on unattached volumes. Snapshots that are incremental still cost money for the data they uniquely hold.

---

#### 18. What is fast snapshot restore?

**Answer:** It pre-warms a snapshot in an AZ so volumes created from it deliver full performance immediately, instead of lazily loading blocks on first read. It costs extra. Use it for large database volumes where the first hour of a restore must be fast. It is unnecessary for small boot disks.

---

## Scenarios

#### 19. You restored a snapshot into another AZ and the instance will not boot. What is wrong?

**Answer:** The new volume must be in the **same AZ as the instance**. A snapshot is regional (usable to create a volume in any AZ of that region), but the volume you created may be in a different AZ from the instance you picked. Create the volume in the instance’s AZ, attach it as the root device name the AMI expects, and confirm the AMI architecture matches the instance type.

---

#### 20. CloudWatch shows the volume at 100 percent burst balance and the database is slow. What do you change?

**Answer:** On gp2, burst balance at zero means you are stuck at baseline IOPS. Move the volume to **gp3** or **io2** and set IOPS to the level the database actually needs, and confirm the instance type can drive that many IOPS. Adding disk size on gp2 also raises baseline IOPS, but that is the expensive way to buy performance.

---

#### 21. An ASG keeps launching instances, and the root volume has data you expected to survive. Why doesn’t it?

**Answer:** Each launch creates a **new** root volume from the AMI. Writes to the root disk of a previous instance die with that instance if `DeleteOnTermination` is true. An ASG is for stateless instances. Put durable data in RDS, S3, or a separate data volume with a backup plan, not on the root disk of an auto-scaled instance.

---

#### 22. How do you move a data volume to a replacement instance with the least downtime?

**Answer:** If the new instance is in the **same AZ**: stop the application, unmount, detach, attach to the new instance, mount, start. If it is in another AZ: snapshot, create a volume in the new AZ, attach, then catch up with the database’s own replication if you cannot afford the snapshot gap. You cannot detach a volume and attach it across AZs directly.

---

#### 23. A nightly snapshot job slows the application. How do you reduce the impact?

**Answer:** Snapshots are incremental and should be brief at the API level, but a database that must freeze IO will stall writers. Take the snapshot from a replica, not the primary. Or use the storage engine’s hot backup. Stagger snapshots so you do not snapshot every volume at the same minute. Confirm you are not taking a full new volume copy by accident.

---

#### 24. How would you encrypt the root volume of an existing unencrypted instance?

**Answer:** Snapshot the root volume, copy that snapshot specifying a KMS key, register an AMI from the encrypted snapshot, and launch a replacement instance. Stop traffic, copy any last changes, and cut over. You cannot flip a flag on the live unencrypted volume. Test the boot before you terminate the old instance.

---

#### 25. What is the failure mode of a single EBS volume in one AZ?

**Answer:** EBS replicates inside the AZ, so a single disk failure is unlikely to destroy the volume. An **AZ outage** still takes the volume and the instance offline together. Design the service as multiple instances in multiple AZs with data in RDS/Aurora, or accept the downtime and restore from a snapshot in another AZ. A single EC2 plus one EBS volume is one failure domain.

---

#### 26. gp3 throughput is set high, but `iotop` never gets close. Where is the ceiling?

**Answer:** The instance’s EBS bandwidth cap, a small IO size (IOPS-bound rather than throughput-bound), or the application issuing IO one request at a time. Check the instance type’s EBS maximum and CloudWatch `VolumeThroughputPercentage`. Raising volume throughput further does nothing if the instance or the app cannot issue enough IO.

---

#### 27. How do you give a forensic copy of a volume to another team without letting them change production?

**Answer:** Snapshot the volume and share the snapshot with the other account, or copy it into a forensics account. They create their own volume. Do not attach the production volume to their instance. If the volume is encrypted, share the KMS key usage as well, or copy the snapshot under a key they control.

---

#### 28. What CloudWatch metrics matter for an EBS data volume?

**Answer:** `VolumeQueueLength`, read and write latency, consumed IOPS versus provisioned IOPS, throughput percent, and on gp2 the burst balance. Alarm on latency and queue length, not only on IOPS. A volume can be “not full” of IOPS and still be slow if the application’s IO size and the instance cap disagree. Disk space is an OS metric: install the CloudWatch agent for filesystem percent used.

---

#### 29. You need 20,000 IOPS for a self-managed database. What do you pick?

**Answer:** An **io2** or **io2 Block Express** volume sized for that IOPS number, on an instance type whose EBS limit is at least that high, in the same AZ as the instance. gp3 can also reach high IOPS, but io2 is the type with the durability story databases ask for. If this is a standard relational database, RDS or Aurora with provisioned IOPS is less work and usually the right recommendation before you run MySQL yourself.

---

#### 30. A snapshot restore boots, but the database takes an hour to become fast. What is going on?

**Answer:** Blocks are loaded from the snapshot on first read (lazy load). The first pass over the data is slow. Enable **fast snapshot restore** before you create the volume if you need immediate performance, or run a warm-up read of the files before you put the instance back in the load balancer. This is expected behavior, not a broken volume.

---
