# AWS Backend Engineer Interview — 50 Scenario-Based Q&A (3–4 Yrs Experience)

> Focus: Security, Fault-Tolerance, Availability, Scalability, Monitoring, Encryption, Migrations, Long-running & Scheduled Tasks, Cost Calculation, Deployments & Upgrades.
> Level: you are expected to have **actually built it** — VPC, ALB, ASG/ECS, RDS, S3, IAM, CloudWatch, CI/CD — not just define services.
> How to use: Read scenario → try answering aloud in 2–3 min (What broke? What did you check first? What did you change? What did it cost?) → compare with answer.

---

## A. Security & Networking (1–8)

### Q1. Your EC2 in a public subnet was SSH-brute-forced. `0.0.0.0/0:22` was open. How do you fix it now and prevent it?
**What they check:** SG hygiene, SSM, least privilege.
**Answer:**
1. **Now:** Restrict SG 22 to your office IP / VPN only, or remove 22 entirely. Rotate key pair if compromised. Check `CloudTrail + VPC Flow Logs` for unusual logins.
2. **Proper fix:** Move app to **private subnet**, no public IP. Access via **SSM Session Manager** (no port 22, IAM-controlled, logged to S3/CloudWatch). ALB stays public.
3. **Prevention:** No `0.0.0.0/0` except 80/443 on ALB. Use `aws:SourceIp` conditions, Security Hub rule “restricted-ssh”. Automate with Terraform `ingress` review in PR.
**Mistake:** Just changing port 22 to 2222. Obscurity ≠ security.

### Q2. Customer images in S3 leaked — bucket was `public-read`. App needs to serve private images to logged-in users only.
**What they check:** Presigned URLs, OAC, Block Public Access.
**Answer:**
- Turn on **S3 Block Public Access (all 4)**, bucket policy Deny `*` unless via CloudFront OAC / app role.
- App generates **S3 presigned URL (expiry 5–15 min)** after auth check in Django/DRF. No static public URL.
- If via CDN: **CloudFront + Origin Access Control (OAC)**, signed URLs/cookies for premium content.
- Encrypt with SSE-S3, enable access logging + CloudTrail data events.
**Tradeoff:** Presigned URL = simple, no CDN caching per-user. CloudFront signed URL = cacheable + cheaper egress.

### Q3. A developer needs production RDS access for 2 hours to debug. You don’t want to share master password.
**What they check:** Temporary access, auditing.
**Answer:**
- No sharing master creds. Use **IAM database authentication** (RDS MySQL/Postgres token, 15-min TTL) or **Secrets Manager rotation + GetSecretValue** with time-bound IAM policy.
- Put DB in private subnet; dev connects via **bastion/SSM port-forwarding** (`aws ssm start-session`), not `publicly-accessible=true`.
- Enable **RDS Enhanced Monitoring + CloudTrail** for who-queried-what. Revoke after.
- Long-term: read replica for debugging, Masked PII in non-prod.
**Say:** “Access is granted, scoped, logged, and auto-expires.”

### Q4. Your public API `/login` is hit by 100k req/min from botnets. WAF? Rate limiting? Costs?
**What they check:** WAF, Shield, API Gateway throttling, ALB.
**Answer:**
- Put **AWS WAF on ALB/API Gateway/CloudFront**: AWSManagedRules (SQLi, XSS, AnonymousIP, Rate-based rule e.g. 2000/5min/IP with block + CAPTCHA).
- **API Gateway usage plans + throttling** (burst/quota per API key) or ALB + WAF rate rule if no API GW.
- **Route53 + CloudFront** absorbs L3/L4; **Shield Standard** is free, Advanced only if you need DDoS cost protection.
- Add **CloudWatch metric `WAFBlockedRequests` + alarm**, log to S3 for Athena analysis.
**Cost note:** WAF ~$5/rule/month + $1/million requests — far cheaper than scaling Fargate to absorb bots.

### Q5. Design VPC for Django (Fargate/EC2) + RDS MySQL + Redis. Where does each live?
**What they check:** Public/private subnets, NAT, SG chaining.
**Answer:**
- **VPC /16, 2 AZs:** 2 public subnets (ALB + NAT GW), 2 private app subnets (Fargate), 2 private data subnets (RDS, ElastiCache).
- **SG chain:** `ALB SG (80/443 from 0.0.0.0) → App SG (8000 only from ALB SG) → DB SG (3306 only from App SG)`. No SG opens port to `0.0.0.0` except ALB.
- Outbound from private → **NAT Gateway** (or VPC endpoints for ECR/S3/Secrets to save NAT data cost).
- Enable **VPC Flow Logs to CloudWatch**, DNS resolution on.
**Mistake:** Putting RDS in public subnet “for easy debugging”.

### Q6. `SECRET_KEY` and `DATABASE_URL` were committed to GitHub. What now?
**What they check:** Incident response, Secrets Manager.
**Answer:**
1. **Rotate immediately:** RDS password (Secrets Manager rotation), Django SECRET_KEY (invalidate sessions), any exposed AWS keys (`iam:DeleteAccessKey`).
2. Purge from git history (`git filter-repo` / BFG) + force-push, but assume it’s already copied — rotation matters more.
3. Move to **Secrets Manager / Parameter Store (SecureString)**, inject via ECS `secrets:` or env `type: SECRETS_MANAGER`. Never `PLAINTEXT` in buildspec/task def.
4. Add **git-secrets / trufflehog in CI**, block merge on finding. Enable **GuardDuty + CloudTrail** for key misuse.
**Say:** “Leaked secret = compromised secret. Revoke first, clean git second.”

### Q7. A vendor needs to read objects from one S3 prefix for 30 days. No IAM user sharing?
**What they check:** Cross-account IAM roles, STS.
**Answer:**
- Vendor creates role in **their account**, you create role in **your account** with trust policy to their `arn:aws:iam::<vendor>:root` + `ExternalId` (prevents confused deputy).
- Policy allows only `s3:GetObject` on `arn:aws:s3:::bucket/vendor/*` + `s3:ListBucket` with `prefix` condition.
- Vendor does `sts:AssumeRole`, gets 1-hr creds. Add expiry date in review + CloudTrail alert on use.
- Never create long-lived IAM user + access key for vendor.
**Why ExternalId:** stops another customer of same vendor assuming your role.

### Q8. Your app was vulnerable to SSRF and attacker hit `http://169.254.169.254/...` and stole EC2 role creds.
**What they check:** IMDSv2, least privilege.
**Answer:**
- Enforce **IMDSv2 (hop limit 1, `HttpTokens=required`)** — PUT+GET token flow blocks simple SSRF GET. Set in launch template: `metadata-options http-tokens=required`.
- Scope EC2/task role to **minimum ARNs** (e.g. only one S3 prefix, not `s3:*`). Short session.
- Validate/allowlist outbound URLs in app, block `169.254.169.254/32` at egress proxy.
- Prefer **ECS task role / IRSA** over instance role — blast radius is one task, not whole host.
**Interview line:** “IMDSv2 mitigates, least-privilege contains.”

---

## B. Scalability, Availability & Fault Tolerance (9–18)

### Q9. Big Billion Day sale in 2 days. Django on 2× EC2 behind ALB is at 85% CPU. Plan to handle 10x for 6 hours.
**What they check:** ASG, ALB, readiness, DB bottleneck.
**Answer:**
- **ASG:** Target-tracking on `ALB RequestCountPerTarget` + CPU 60%. Min 4, Max 20. Warm pool / pre-scale. Health check = `/health/` (DB + Redis ping), grace 180s.
- **ALB:** Sticky off for stateless, deregistration delay 30s, slow-start 60s.
- **App:** Make stateless (sessions in Redis/DB, media to S3). `gunicorn --workers (2×CPU)+1`, connection pooling (PgBouncer/RDS Proxy).
- **DB:** Add **read replica** for reads, enable **RDS Proxy** to avoid connection storm. Cache hot product pages in ElastiCache (TTL 60s).
- Load test with k6, set CloudWatch alarm on `TargetResponseTime p99`.
**Tradeoff:** Over-provision for 6 hrs is cheaper than outage; scale-in with cooldown after.

### Q10. One AZ goes down. Your app is in `ap-south-1a` only. What breaks and what’s the Multi-AZ design?
**What they check:** Multi-AZ vs single-AZ.
**Answer:**
- Single-AZ: EC2, RDS, NAT all die → full outage. ALB shows 503.
- Fix: **ALB + targets in ≥2 AZs**, **RDS Multi-AZ (standby)**, **NAT per AZ** (or at least routes), **ElastiCache with replica in other AZ**.
- **RDS Multi-AZ ≠ scaling** — standby is for failover (~60–120s DNS flip). Scaling reads = read replica.
- Test with **fault-injection (stop instance / reboot with failover)** in staging.
**Cost:** Multi-AZ RDS ≈ 2x instance cost; justify with RTO/RPO.

### Q11. SQS queue depth grows from 0 to 200k, consumers lag, some messages poison the worker repeatedly.
**What they check:** DLQ, visibility timeout, scaling.
**Answer:**
- Set **visibility timeout ≥ 6× processing time** to avoid duplicate processing. Enable **long polling (20s)** to cut cost.
- Add **DLQ + redrive**: `maxReceiveCount=3–5` → DLQ. Alarm on `ApproximateNumberOfMessagesVisible` + `NumberOfMessagesSent to DLQ`.
- Scale consumers on queue depth (ASG on `ApproximateNumberOfMessagesVisible` or ECS Service Auto Scaling, or Lambda event-source batching).
- Make worker **idempotent** (DB unique key on `message_id`) because SQS is at-least-once. Log `messageId` end-to-end.

### Q12. RDS primary CPU 95%, lots of `SELECT`s from reports + app. Writes are fine. How to scale reads without downtime?
**What they check:** Read replica, Proxy, caching.
**Answer:**
- Create **RDS read replica** (async, no downtime), point reporting + heavy list APIs to replica endpoint (separate Django DB router).
- Add **RDS Proxy** in front to pool connections — fixes `Too many connections` during scale-out.
- Cache with Redis: cache-aside for dashboards (TTL), invalidate on write.
- Long-term: partition large tables, add missing indexes (check `Performance Insights` top SQL).
**Not:** Upgrading instance first — expensive and doesn’t fix read/write contention.

### Q13. DynamoDB `ProvisionedThroughputExceeded` on one partition key (`tenant_id=big-customer`).
**What they check:** Hot partition, adaptive capacity.
**Answer:**
- Symptom = hot key. Fix key design: composite `tenant#date#random_suffix` or write-sharding (e.g. `order#1..10`).
- Switch to **On-demand** for spiky, or Auto Scaling with high target + burst. Enable **DAX** if read-heavy.
- Use **SQS buffering** for bursts, exponential backoff + jitter in SDK.
- Check CloudWatch `ConsumedWriteCapacityUnits` per key via Contributor Insights.
**Say:** “Dynamo scales by partition; good key = even spread.”

### Q14. ALB returns 502, targets show `unhealthy`. Walk through debug.
**What they check:** Structured troubleshooting.
**Answer:**
1. Check **target health reason** in console (failed health check vs timeout).
2. `curl` health path from inside VPC: app port? SG allows ALB SG? NACL? Route?
3. Logs: `ECS stopped reason`, `gunicorn timeout`, `DB connection refused`, `OOMKilled` (raise memory).
4. Common: health path returns 302 (login redirect) but matcher expects 200 → set matcher `200-399` or use `/health/`. Grace period too short during migrations.
5. Verify **target-type=ip** for Fargate, same VPC, correct port.
**Order:** ALB → SG/network → app log → DB/dependency.

### Q15. Need DR: RPO <1 hr, RTO <4 hr for Django + MySQL. Active-passive in another region.
**What they check:** Backup, replication, Route53 failover.
**Answer:**
- **DB:** RDS automated backups + **cross-region read replica** (async <1s lag typical) or cross-region snapshot copy hourly.
- **App:** ECR cross-region replication, ECS service `desired=0` (pilot light) in DR region, Terraform same stack.
- **Data:** S3 **CRR** for media, Secrets Manager replicate.
- **DNS:** **Route53 health check + failover routing** to DR ALB. Test quarterly with GameDay.
- Document RPO = replica lag + backup freq, RTO = scale-out + DNS TTL (set TTL 60s).
**Cost saver:** Pilot-light (DB replica + minimal infra) vs hot-standby (full running).

### Q16. Users upload 5GB videos. EBS vs EFS vs S3? Design upload flow.
**What they check:** Right storage for job.
**Answer:**
- **S3** for blobs (11×9s durability, unlimited, cheap). EBS = one AZ disk for instance. EFS = shared POSIX FS (good for shared CMS, expensive at scale).
- Flow: Browser → **S3 presigned PUT** (direct, no load on app) → **S3 Event → SQS → Fargate worker** transcodes → store output in S3 → CloudFront serves.
- Multipart upload for >100MB, lifecycle to Intelligent-Tiering/Glacier.
**Why:** App servers stay stateless; no disk fills.

### Q17. Cache stampede: Redis goes down, all requests hit DB and DB dies.
**What they check:** Resilience patterns.
**Answer:**
- Client: **jittered TTL + stale-while-revalidate** (serve stale 60s while refill), **request coalescing / singleflight** so 100 same-key misses = 1 DB query.
- **Circuit breaker** (fail fast to default) + **bulkhead** (limit DB pool for refill).
- Redis: Multi-AZ with auto-failover, `maxmemory-policy=allkeys-lru`, separate cache cluster from sessions.
- Warm cache on deploy (pre-load hot keys).

### Q18. You use Spot for workers to save 70%. How to not lose jobs on interruption?
**What they check:** Spot handling.
**Answer:**
- Use **ASG mixed instances + capacity-optimized allocation**, `capacity-rebalance=true`. On `EC2 Spot Interruption notice (2-min)` → drain.
- Jobs via **SQS**: visibility timeout hides job; if worker killed, message reappears. Checkpoint long jobs to S3/DB.
- Stateless workers, no local data. On-demand base (30%) + Spot (70%).
- For ECS: `ECS managed draining` + `spot` capacity provider.
**Numbers:** Spot saves ~60–70% but only for fault-tolerant, retryable work.

---

## C. Monitoring, Logging & Troubleshooting (19–24)

### Q19. p99 latency jumped 300ms → 2s after a release, but CPU is fine. Where do you look?
**What they check:** Tracing vs metrics.
**Answer:**
- **X-Ray / OTEL trace:** split time into ALB → app → DB → Redis → external API. Usually DB N+1 or downstream timeout.
- **RDS Performance Insights:** top SQL by latency, locks, `SELECT ... FOR UPDATE` waiting.
- **ALB `TargetResponseTime` vs `RequestCount`:** if ALB slow but app fast → TLS/athena? Check `p50 vs p99` (p99 = few slow queries).
- Correlate deploy time in CloudWatch, check new migration missing index.
**Say:** “CPU fine → not compute, it’s waiting — traces show what it waits on.”

### Q20. Disk filled at 3 AM and app crashed. Design logging so it never happens again.
**What they check:** Centralized logging.
**Answer:**
- Never log to local disk unbounded. Ship via **CloudWatch agent / Firehose → S3 + Athena**, rotation + `logrotate` max 100MB.
- Django: JSON logs to stdout → ECS `awslogs` driver → CloudWatch (7-day retention, export to S3).
- Alarm on `disk_used_percent >75%` + `log group ingestion spike`. Set **S3 lifecycle** on logs.
- Fix root: `DEBUG log file` in repo (`logs/debug.log`) grows forever — switch to console handler in prod.

### Q21. Lambda times out intermittently when calling RDS in VPC. Sometimes 30s cold + ENI delay.
**What they check:** Lambda VPC networking.
**Answer:**
- Lambda in VPC needs **ENI in private subnets + NAT** (or VPC endpoints). Cold start creates ENI → adds latency. Use **provisioned concurrency** for critical path.
- Reuse DB connection outside handler, use **RDS Proxy** (pooling, IAM auth).
- Increase memory (more CPU = faster), set timeout < API GW 29s, add **DLQ + retries with backoff**.
- Metrics: `ConcurrentExecutions`, `Duration p99`, `ENI cold start`. Consider moving to Fargate if always-VPC + long-lived.

### Q22. When do you use CloudWatch vs CloudTrail vs X-Ray vs VPC Flow Logs?
**Answer:**
- **CloudWatch Metrics/Logs/Alarms:** “What is happening now?” CPU, 5xx, latency. Dashboards + paging.
- **CloudTrail:** “Who did what API call?” IAM, console, `DeleteBucket`, root login. Audit.
- **X-Ray:** “Where is it slow across services?” Distributed trace.
- **VPC Flow Logs / ALB access logs / S3 access logs:** Network forensics, 5-tuple, blocked traffic.
**Interview tip:** Give one real example of each you’ve used.

### Q23. Team gets 200 alerts/day and ignores them. Redesign alerting.
**What they check:** SLO-based alerting.
**Answer:**
- Only page on **user-impacting SLO burn**: `5xx >0.5% for 5m`, `p99 >1s for 10m`, `RDS failover`, `queue DLQ >0`. Everything else = ticket/email.
- Multi-window: fast-burn (5m) pages, slow-burn (1h) tickets. Add runbook link in alarm.
- Suppress during deploy (CodeDeploy hook), auto-resolve, dedupe with SNS → PagerDuty/OpsGenie.
- Weekly review: if alarm never paged actionable → demote to dashboard.
**Line:** “If everything pages, nothing pages.”

### Q24. After deploy, 5xx jumps to 20%. Roll back or roll forward?
**Answer:**
- If **error budget burning + no quick fix (<10 min)** → **rollback now** (ECS circuit-breaker auto-rollback, CodeDeploy auto-rollback on CloudWatch alarm).
- Check: new migration incompatible? New env var missing? Health check passing but app broken (need smoke test `/health/detailed`)?
- Need **deployment safety**: `minimumHealthy 100%`, `max 200%`, stop on alarm, automated smoke (login + list API) in CodeBuild post-deploy.
- Post-mortem: why didn’t staging/canary catch? Add canary 10% next time.

---

## D. Encryption, Secrets & Compliance (25–29)

### Q25. How do you encrypt everything for Django + RDS + S3 + EBS?
**Answer:**
- **In transit:** TLS 1.2+ everywhere. ALB HTTPS (ACM), RDS `require_secure_transport=ON`, Redis `TLS + AUTH`, S3 via HTTPS only (bucket policy deny `aws:SecureTransport=false`).
- **At rest:** S3 SSE-S3 (dev) / SSE-KMS CMK (prod), RDS `storage_encrypted=true`, EBS encrypted by default, Secrets Manager with KMS, CloudWatch log group with KMS.
- **App:** `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS.
**Check:** `aws config rule encrypted-volumes + s3-bucket-ssl-requests-only`.

### Q26. AWS-managed key vs Customer-managed CMK in KMS? When to pay for CMK?
**Answer:**
- **AWS-managed (`aws/rds`, `aws/s3`):** free, auto-rotation yearly, no cross-account control.
- **CMK:** you control rotation, grants, CloudTrail per-key audit, cross-account sharing. Costs $1/key/month + API calls.
- Use CMK for PII/PCI, cross-account pipeline artifact bucket, prod DB. Use AWS-managed for dev logs/cache.
- Enable **automatic rotation**, scope `kms:*` via `ViaService` condition (e.g. only RDS can use key).

### Q27. Terminate TLS at ALB or end-to-end to container?
**Answer:**
- **Default (practice/startup): TLS at ALB, HTTP inside VPC.** Simple, ACM auto-renews, less CPU on app. VPC is trusted boundary + SGs.
- **End-to-end (finance/health):** ALB HTTPS → target HTTPS with self-signed/ACM Private CA on container, or NLB with TLS passthrough. Needed if compliance says “encrypt even inside VPC”.
- Always set `X-Forwarded-Proto` handling in Django (`SECURE_PROXY_SSL_HEADER`) so `is_secure()` works behind ALB.
**Tradeoff:** E2E = more ops (cert rotation on tasks) for smaller threat window.

### Q28. PII (phone, Aadhaar) is in logs and S3 exports. How to find and fix?
**Answer:**
- Discover: **Macie** scans S3 for PII, **CloudWatch Logs Insights** query for patterns, DLP in CI.
- Fix: structured logging with **redaction filter** (mask `phone → ****1234`), never log request body wholesale. S3 objects with PII → **SSE-KMS + separate bucket + strict policy + Object Lock** if needed.
- Access: CloudTrail data events on that bucket, Athena query only via approved role.
- Process: data retention policy (delete after N days via lifecycle), consent + purpose.

### Q29. Ransomware deleted S3 + RDS. How do you recover?
**Answer:**
- **S3:** Versioning + **MFA Delete + Object Lock (Compliance)** on critical bucket, cross-region replication, Block `s3:Delete*` for app role (only backup role can delete).
- **RDS:** Automated backups 7–30d + manual snapshots + cross-region copy. Test restore quarterly (restore to new instance, time it).
- **IAM:** No `s3:*` + `rds:*` on same role. Separate backup account with Vault Lock.
- Runbook: isolate (revoke keys), restore to new resources, verify hash/row counts, flip DNS.
**Say RPO/RTO numbers:** “With versioning + daily snapshot, RPO <24h, RTO ~1h.”

---

## E. Migrations (30–35)

### Q30. Migrate on-prem MySQL 500GB to RDS with <5 min downtime.
**Answer:**
- Use **AWS DMS full load + CDC**: DMS replication instance → target RDS. Keep source binlog on (`binlog_format=ROW`, retention 24h).
- Pre-check with **DMS Schema Conversion + premigration assessment**, create indexes beforehand, larger RDS during load then downsize.
- Cutover: stop writes (maintenance page), wait lag=0 (`CDCLatencySource`), promote RDS, flip `DATABASE_URL` via Secrets Manager, switch DNS. Keep fallback.
- Validate row counts + checksums, run smoke tests. Keep DMS running 2 days for rollback.
**Alternative:** `mysqldump` only for <10GB or downtime-tolerant.

### Q31. Move Django from single EC2 (with local media + cron) to ECS Fargate. Steps?
**Answer:**
1. **Stateless first:** media → S3, sessions → DB/Redis, cron → EventBridge, logs → CloudWatch.
2. Containerize (gunicorn, non-root, healthcheck). Push to ECR.
3. Terraform: VPC + ALB + ECS + RDS + Secrets (same as this repo’s `Terraform-prac`).
4. **Dual-run:** new stack points to copy of DB, smoke test, then blue/green DNS weight 10% → 100%.
5. Decommission EC2 after 1 retention window. Update deploy pipeline to ECR+ECS.
**Pitfall:** local disk `media/` lost on new task — must move before migration.

### Q32. Move 5TB from old S3 bucket/account to new with validation, no re-upload by users.
**Answer:**
- **S3 Batch Replication / `aws s3 sync` from EC2 in same region** (not laptop) with `--size-only` + versioning on. For cross-account, destination bucket policy allows source role.
- Preserve metadata/ACLs, enable **S3 Inventory + checksum** to verify object counts.
- Large: **S3 Batch Operations** + manifest, CloudWatch `BytesPendingReplication`.
- Cutover: dual-write period, then flip CloudFront origin. Keep old bucket read-only 30d with lifecycle to Glacier.

### Q33. Upgrade RDS MySQL 5.7 → 8.0. App uses Django 5.0. Risk plan?
**Answer:**
- Check **RDS pre-upgrade checker** (reserved words, utf8mb3 → utf8mb4, removed functions). Test in clone (restore snapshot to new instance, upgrade, run test suite + slow-query compare).
- Strategy: **Blue/Green RDS** (creates green 8.0, syncs, single switchover ~1 min) or read-replica upgrade + promote.
- App: `mysqlclient` compatible, test `ONLY_FULL_GROUP_BY` (8.0 default strict) — common Django `GROUP BY` breakage.
- Rollback: keep blue 48h, snapshot before. Upgrade staging → canary → prod off-peak.

### Q34. Data-center exit: flip `app.example.com` from on-prem to ALB with zero surprise.
**Answer:**
- Lower **Route53 TTL to 60s** 48h before. Create **weighted routing**: 90% on-prem, 10% ALB. Monitor 5xx/latency.
- Pre-warm ALB (request ramp), ensure ACM cert covers domain, test TLS + sticky + WAF rules in staging.
- Use **health checks** + failover: if ALB unhealthy, DNS fails back.
- After 24h clean, weight 100% ALB, raise TTL back to 3600. Keep on-prem warm 1 week.

### Q35. Move sessions/cart from Postgres to DynamoDB with zero downtime.
**Answer:**
- **Dual-write + backfill:** write to both, read from Postgres; backfill history with DMS/Glue; shadow-read Dynamo and compare.
- Flip reads to Dynamo with feature flag per tenant. Keep Postgres as fallback 2 weeks.
- Design PK: `pk=USER#123, sk=CART#...`, TTL for expiry, On-demand initially then provisioned.
- Verify with replayed traffic + `ContributorInsights` for throttles.

---

## F. Long-Running & Scheduled Tasks (36–40)

### Q36. Video transcode takes 40 min. Lambda times out at 15 min. Design on AWS.
**Answer:**
- Don’t use Lambda for work >15 min. Use **Fargate task / Batch job**: S3 PUT → EventBridge → **SQS → ECS worker** (or **AWS Batch** with job queue + retries).
- Progress in DynamoDB (`job_id → status/%`), browser polls or WebSocket via API GW.
- Idempotent job (S3 object key as idempotency key), DLQ after 3 tries. Scale workers on queue depth.
- **Batch** if you need GPU/spot + array jobs; **Fargate** if steady Django/Celery workers.
**Cost:** Fargate per-second; Batch on Spot saves more for batch.

### Q37. Nightly 2 AM report (Django management command, 20 min) + every-5-min heartbeat. Cron on EC2 is flaky.
**Answer:**
- **EventBridge Scheduler → ECS RunTask** (one-off Fargate task overrides command to `python manage.py daily_report`). No server to keep up. Retry once, DLQ to SNS.
- For <15 min + light: **EventBridge → Lambda**.
- Prevent overlap: **Step Functions with `...: semantic` or DB advisory lock** (`SELECT pg_try_advisory_lock`) so second run exits if first still running.
- Monitor with `ECS task failed` alarm + report-row-count check (if 0 rows → alert, not silent success).

### Q38. Celery + Redis on one EC2 keeps OOMing. How to run task queue reliably?
**Answer:**
- Replace Redis broker with **SQS (or ElastiCache Serverless with HA)**. Workers on **ECS Service auto-scaling on queue depth** or ASG.
- Separate queues: `default`, `heavy`, `email` — so one slow task doesn’t block login emails. Separate worker pools + concurrency limits.
- Visibility timeout > task timeout, DLQ, idempotent tasks, Flower behind auth (not public).
- Persist results in DB, not broker. Use **EventBridge + Step Functions** if you need visual retries/state instead of Celery chains.

### Q39. Scheduler fires twice (duplicate reports, double charge). How to guarantee once?
**Answer:**
- Schedulers are at-least-once. Make job **idempotent**: DB unique constraint on `(date, job_name)`, S3 object `if-none-match`, Stripe idempotency key.
- **Distributed lock:** DynamoDB conditional write (`attribute_not_exists(lock_id)`) with TTL, or **EventBridge Scheduler with `...` + Step Functions Express (exactly-once workflow)**.
- Single scheduler (not cron on 2 boxes), set `MaximumEventAge + retry=0` for non-critical, DLQ for missed.
**Say:** “You can’t guarantee firing once; you guarantee effect once.”

### Q40. 10k concurrent WebSockets for live tracking. ALB + Django Channels won’t hold.
**Answer:**
- Don’t hold sockets in Django. Use **API Gateway WebSockets → Lambda/DynamoDB connections table** or **IoT Core MQTT** for massive fan-out.
- Flow: client → API GW `$connect` stores `connectionId` in Dynamo → publish via SNS → Lambda fans out via `postToConnection`. Disconnect cleans up.
- If on ALB: use **sticky + NLB + separate socket service (Node/FastAPI)**, not Django workers (blocks gunicorn).
- Monitor `ConcurrentConnections`, throttle per-IP with WAF.

---

## G. Cost Calculation & Cost-Effective Solutions (41–45)

### Q41. Bill doubled after moving to VPC. You see NAT Gateway + data transfer spike. Diagnose and cut?
**Answer:**
- Check **Cost Explorer by service + AZ**: `NatGateway-Hours + DataProcessed ($0.045/GB)`, `EC2 DataTransfer`, `CloudWatch Logs ingestion`.
- Causes: ECR/S3/Secrets traffic going via NAT instead of **VPC endpoints (Gateway for S3/Dynamo = free, Interface for ECR/Secrets/Logs ~$7/mo + $0.01/GB — still cheaper than NAT)**. Cross-AZ traffic (ALB → task in other AZ = $0.01/GB).
- Fixes: add Gateway endpoints now, Interface endpoints for high-volume APIs, keep AZ-affinity, S3 lifecycle, delete idle NAT in dev (use single NAT), compress logs, set CloudWatch retention 7d not Never.
**Example math:** 1TB via NAT = $45; via S3 Gateway endpoint = $0.

### Q42. 10TB in S3 Standard, mostly accessed once then rarely. Cheapest safe layout?
**Answer:**
- **S3 Intelligent-Tiering** (auto moves, no retrieval fee) or explicit: Standard (30d) → **Standard-IA** → **Glacier Instant** → **Deep Archive** after 180d via lifecycle.
- Enable **compression (parquet/gzip)**, delete incomplete multipart uploads after 7d, versioning with noncurrent expiry (30d).
- **Math:** 10TB Standard ≈ $230/mo; Intelligent-Tiering infrequent ≈ $125 + monitoring $0.0025/1000; Deep Archive ≈ $10/mo but 12h restore. Show tradeoff on retrieval.
- Add **S3 Storage Lens + Request metrics** to prove access pattern before moving.

### Q43. Dev env (4× EC2 + RDS) idles nights/weekends. Cut 60% without hurting devs?
**Answer:**
- **Instance Scheduler (EventBridge + Lambda)**: stop 8pm–8am + weekends → saves ~65% compute. RDS stop/start same schedule (max 7d stopped — re-trigger).
- Switch to **Graviton (t4g/m7g: 20% cheaper + faster)**, **Savings Plan 1-yr** for baseline, Spot for CI runners.
- Downsize via **Compute Optimizer** (often 2x over-provisioned), EBS `gp3` not `gp2`, delete unattached EBS/snapshots >30d.
- **Math example:** 4× `t3.medium` 24×7 ≈ $120/mo → scheduled 12×5 ≈ $40 + Graviton −20% ≈ $32.

### Q44. API does 5M req/mo, avg 200ms. ALB+Fargate vs API GW+Lambda — which is cheaper?
**Answer:**
- **Lambda math:** 5M × $0.20/M + 5M×0.2s×1GB/1024 × $0.00001667 ≈ $1 + $16 ≈ **$17/mo** + API GW $3.5/M ×5 = $17.5 → ~$35/mo.
- **Fargate math:** 0.25 vCPU +0.5GB always-on ≈ $15/mo + ALB $16 + LCU (~5M req ≈ $5) ≈ **$36/mo**.
- Verdict: at 5M/mo they tie; <2M Lambda wins; >20M sustained Fargate wins (no per-req tax). Add **provisioned concurrency / Fargate SP** to refine.
- Non-cost: Lambda = no patching, 15-min limit; Fargate = persistent connections, WebSockets.

### Q45. RDS `db.m5.large` Multi-AZ $350/mo is heavy for staging. Cheaper but safe?
**Answer:**
- Staging: **Single-AZ `db.t4g.micro/small` + stop schedule + snapshot before stop**. Use **Aurora Serverless v2 (0.5–2 ACU)** if spiky — scales to near-zero.
- Prod: **Reserved Instance 1-yr (~40% off)** or Graviton `db.m7g` (better $/perf). Enable **Performance Insights + autoscaling storage**.
- Don’t: use prod class in staging “to be safe” — use prod-like *version*, not size. Load test on prod-class only during test week.
**Numbers:** `db.t4g.micro` single-AZ ≈ $13/mo vs `m5.large` Multi-AZ ≈ $350 — 25x for staging is waste.

---

## H. Deployments & Upgrades (46–50)

### Q46. Deploy Django to ECS with zero downtime. Rolling vs blue/green? What about `migrate`?
**Answer:**
- **Rolling (default):** `min 100%, max 200%`, health grace 180s, circuit-breaker rollback on. Simple, needs 2x capacity briefly.
- **Blue/green (CodeDeploy):** two target groups, test listener, shift 10% → 100%, auto-rollback on alarm. Better for risky DB change, needs extra config.
- **Migrations:** backward-compatible only (expand → migrate → contract). Run `migrate` as **separate one-off task before deploy**, not in container CMD at scale (two tasks racing). For practice single-task, CMD migrate is OK.
- Pre-check: `collectstatic` in image build, smoke `/health/` + `/admin/login/`, CloudWatch alarm auto-rollback.

### Q47. Deploy failed halfway: new code needs column `credits`, old code still running. How to avoid?
**Answer:**
- **Expand-migrate-contract:** Deploy 1: add nullable column (old + new code work). Deploy 2: backfill + start writing. Deploy 3: make NOT NULL / drop old column.
- Never `DROP COLUMN` + code using it in same release. Make migration **backward-compatible + reversible**.
- Pipeline: migration task runs first, app deploy only if exit 0. On fail, CodePipeline stops before Deploy stage. Keep DB snapshot pre-deploy.
**Interview line:** “DB changes ship in 2 releases, app in 1.”

### Q48. Product wants canary: 10% users see new checkout for 1 hour, instant rollback.
**Answer:**
- **ALB weighted target groups:** `v1 weight 90, v2 weight 10`, shift via CLI/Terraform. Or **Route53 weighted** across services. Or **feature flag (LaunchDarkly/Unleash)** for finer % + instant off without deploy.
- Monitor conversion + 5xx per target group (`TargetResponseTime`, business metric `checkout_success`). Auto-rollback: alarm → weight back to 0.
- Sticky sessions off, ensure both versions share DB schema + Redis format.
- Prefer flag for UI copy, weighted deploy for infra risk.

### Q49. ECS deploy stuck: new task starts then stops, service keeps old version. Debug?
**Answer:**
1. `aws ecs describe-tasks --stopped --include reason`: `CannotPullContainerError` (ECR perms/image tag), `OOMKilled` (raise memory), `health check failed` (wrong path/port), `ResourceInitializationError: secrets` (execution role can’t read Secrets).
2. Check **stopped reason + CloudWatch logs** (often empty = never started = pull/secret/env error).
3. Verify SG (ALB → task), target group port, `essential=true`, env var typo.
4. Fix: push correct tag, `aws ecs update-service --force-new-deployment`. Enable **circuit breaker + CloudWatch alarm** so it auto-rolls back instead of hanging.
**Note in this repo:** service ignores `task_definition` drift — pipeline owns image, so re-release after fixing Terraform.

### Q50. Upgrade EKS 1.28 → 1.30 with zero downtime. Node strategy?
**Answer:**
- **Managed node groups rolling / Karpenter:** create new node group on new AMI, cordon → drain (respect PDBs: `minAvailable 1`), PodDisruptionBudgets + `terminationGracePeriod`.
- Upgrade order: **control plane → addons (VPC-CNI, CoreDNS, kube-proxy) → nodes**. Check deprecated APIs (`kubectl convert`, `pluto`).
- Use **surge nodes** (extra capacity) so drain doesn’t evict all replicas. Canary one AZ first.
- For ECS equivalent: new task definition revision + rolling with `min 100%`.
**Mistake:** upgrading control plane + nodes together, no PDBs → outage.

---

## Cheat-sheet: lines to drop in interview

- “Private subnets + ALB public, DB has no public IP.”
- “Stateless app, state in RDS/S3/Redis — that’s what lets us scale.”
- “At-least-once everywhere (SQS, schedulers) → idempotency key + unique constraint.”
- “Page only on SLO burn, everything else is a ticket.”
- “DB changes in two releases, app in one.”
- “Show me the bill: NAT + transfer is usually the surprise, not compute.”

## Hands-on next steps (maps to `Terraform-prac/` in this repo)

1. Add ACM + HTTPS listener, redirect 80→443.
2. Add VPC endpoints for ECR/S3/Secrets, compare NAT bill before/after.
3. Split `migrate` into CodeBuild/ECS RunTask, raise `desired_count` to 2.
4. Add `/health/` + canary weights + rollback alarm.
5. Store state in S3 + practise `terraform destroy` cost drill.
