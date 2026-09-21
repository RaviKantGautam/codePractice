# AWS CloudTrail — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS CloudTrail?

**Answer:** CloudTrail records **API activity** in your AWS account: who called which action, on which resource, from where, and whether it succeeded. It is the audit log for the control plane. It is not where you look up application latency or your service’s INFO logs. That is CloudWatch.

---

#### 2. What is an event?

**Answer:** A JSON record of one API call. It includes the event time, event name (`StopInstances`, `PutObject`), the principal (IAM user, role, or AWS service), the source IP, the request parameters, and an error code if it failed. You search these when something changed and nobody remembers deploying.

---

#### 3. What is the difference between management events and data events?

**Answer:**

* **Management events:** control-plane calls, such as creating a bucket, changing a security group, or stopping an instance. A trail can log these by default.
* **Data events:** high-volume data-plane calls, such as S3 `GetObject` and `PutObject`, or Lambda invocations. They are **off** until you enable them, and they cost more.

Turn on data events for sensitive buckets or functions, not for every log bucket in the account, or the bill and the noise win.

---

#### 4. What is an Insights event?

**Answer:** CloudTrail Insights flags unusual API activity compared with a baseline, such as a spike in `TerminateInstances`. It is a hint, not a complete detector. You still want explicit alarms for the actions you care about (root login, trail stopped, public bucket policy). Insights will not know your change window.

---

#### 5. Where do you read events?

**Answer:** **Event history** in the console keeps the last 90 days of management events and is searchable without a trail. A **trail** delivers events to S3 (and optionally CloudWatch Logs) and can include data events and events from all regions. Event history is enough for a quick “who changed this”. A trail is what you need for retention, alerting, and a security review.

---

#### 6. Why is a trail better than only using event history?

**Answer:** Event history is short, is not a full export, and does not cover data events. A trail writes to an S3 bucket you control, can be multi-region, can send to CloudWatch Logs for metric filters, and can be locked down so an attacker cannot quietly edit the past. Production accounts should have a trail. Looking only at event history is a starting point during an incident, not the design.

---

## Trails and integrity

#### 7. What should a production trail look like?

**Answer:** An organization trail or an account trail that applies to **all regions**, writes management events, sends to an S3 bucket in a locked-down logging account if you have one, and is encrypted with KMS. Log file validation turned on. CloudWatch Logs optional but useful for alarms. Data events enabled only where the data is sensitive. The bucket policy allows CloudTrail to write and denies everyone else from deleting objects.

---

#### 8. What is log file validation?

**Answer:** CloudTrail writes a digest so you can prove log files were not modified or deleted after delivery. Turn it on. It does not stop someone from changing infrastructure. It helps you trust the log later. If you skip it, a reviewer will ask how you know the audit log is intact.

---

#### 9. What is a trail’s relationship with S3 object lifecycle?

**Answer:** The trail delivers objects. Lifecycle rules on that bucket move them to cheaper storage or expire them after the retention period your policy requires. Do not expire them in seven days if the company says one year. The bucket should block public access. CloudTrail logs that contain request parameters can include resource names and sometimes sensitive snippets. Treat the bucket as sensitive.

---

#### 10. Who can hide their tracks, and how do you make that harder?

**Answer:** A principal with permission to stop the trail, change the bucket policy, or delete objects can interfere with logging. Restrict `cloudtrail:StopLogging`, `DeleteTrail`, and `s3:DeleteObject` on the log bucket to a small break-glass role. Alarm when `StopLogging` or `DeleteTrail` happens. Write logs to another account so a compromised application account cannot delete them. This is the main reason a central logging account exists.

---

#### 11. What does CloudTrail not record?

**Answer:** It does not record data that never went through an AWS API. It does not replace application logs, OS auth logs, or a database’s own audit log. Some data events are not covered unless you enable them. Calls that fail IAM still appear, which is useful. Activity inside a container that never calls AWS does not appear. Say this clearly so you do not claim “CloudTrail sees everything”.

---

#### 12. How is CloudTrail different from AWS Config?

**Answer:** CloudTrail is the **stream of API calls**. Config is the **state** of resources over time and whether that state matches a rule (is this bucket public?). You use CloudTrail to see who changed a security group at 14:02. You use Config to see that the security group is still open to the world and to flag it. They complement each other.

---

## Finding what happened

#### 13. An instance was terminated and nobody claims it. What do you search?

**Answer:** Event name `TerminateInstances`, around the time the instance disappeared, in the right region and account. The event shows the principal: a role session name often includes the user or the pipeline, the source IP, and the request parameters with the instance id. If the principal is an Auto Scaling role, it was the ASG, not a person. Then look at ASG activity for the health-check failure.

---

#### 14. What is a principal, a user identity, and a session name?

**Answer:** The **user identity** block says whether the caller was an IAM user, an assumed role, or an AWS service. For assumed roles you get the role ARN and a **session name**. Good pipelines set a session name you can recognize (`github-actions-deploy`). A useless session name (`botocore-session-123`) makes the trail harder to read. Require session names in automation.

---

#### 15. How do you tell a console click from an SDK call?

**Answer:** The event includes a `userAgent`. The console and the CLI leave recognizable agents. This is a hint, not a legal proof. The source IP for console calls is the human’s network. The source IP for a role on EC2 may be the instance or a VPC endpoint. Read the whole identity block before you accuse a person.

---

#### 16. A deploy role can change anything. How does CloudTrail still help?

**Answer:** You can see **which** action ran, **when**, and from **which** pipeline identity, even if the role is broad. That shortens the incident. It is not a substitute for a narrower role. If every change is `AdministratorAccess` from a laptop, the trail is a sad story. If only the pipeline role can deploy, the trail confirms the pipeline did it.

---

#### 17. How do you alert on a specific API call?

**Answer:** Send the trail to CloudWatch Logs and add a **metric filter** for the event name, or route CloudTrail events through **EventBridge** and match `StopLogging`, `ConsoleLogin` without MFA, or `PutBucketPolicy`. EventBridge is the cleaner option for new alerts. The metric filter works if logs are already going to CloudWatch. Test by performing the action in a dev account.

---

#### 18. What is an organization trail?

**Answer:** In AWS Organizations, a trail defined in the management or a delegated admin account can log every member account. Member accounts cannot turn it off if you set it that way. This is what you want once you have more than a couple of accounts. Each account’s event history still exists, but the copy that security trusts lives in the organization trail’s bucket.

---

## Security scenarios

#### 19. Root user activity showed up. Why is that an alarm even if the call succeeded?

**Answer:** The root user should not be used for daily work. Any root API call or console login is a signal to verify, except a known break-glass procedure you already documented. Alarm on root usage. MFA on root is the preventive control. CloudTrail is how you know the control was bypassed or used.

---

#### 20. Someone claims a bucket was always private. How do you check?

**Answer:** Search CloudTrail for `PutBucketPolicy`, `PutBucketAcl`, and `DeletePublicAccessBlock` on that bucket name. The event parameters show the policy that was applied and who wrote it. Config can show the current evaluation. CloudTrail shows the change. If data events are off, you will not see who **downloaded** the objects, only who changed the policy.

---

#### 21. You enabled S3 data events and the bill jumped. Was that a mistake?

**Answer:** Data events on a busy bucket record every GET and PUT. That can be millions of events. Enable them on buckets that hold sensitive data or where you must investigate object access. Leave them off for high-volume log and asset buckets unless a requirement says otherwise. You can scope data events to specific bucket ARNs. Do not enable “all S3 in the account” by default.

---

#### 22. A Lambda function’s data events are enabled. What will you see that management events did not show?

**Answer:** Invoke events: who or what invoked the function, and when. Management events already show configuration changes (`UpdateFunctionCode`, permission changes). If the question is “who changed the code”, management events are enough. If the question is “who invoked it”, you need data events or the function’s own logs. CloudWatch logs are usually the better tool for invoke debugging. Data events are for audit.

---

#### 23. How do you investigate an access key that might have leaked?

**Answer:** Search CloudTrail for that access key id across regions (the trail must be multi-region, because attackers pick another region). Look at event names, source IPs, and error codes. Disable the key, rotate it, and check for `CreateUser`, `AttachUserPolicy`, and unusual `RunInstances`. Event history in one region is not enough if the attacker used another region and you had no trail there.

---

#### 24. CloudTrail shows `AccessDenied` for the app role. The app logs only say “failed”. Which do you trust for IAM debugging?

**Answer:** CloudTrail (and the encoded authorization message) names the action and the resource. Fix the policy to allow that action on that resource. Application logs rarely include the missing IAM action. This is one of the best day-to-day uses of CloudTrail for a backend engineer, not only for security incidents.

---

## Practice

#### 25. A teammate changed a security group yesterday. Walk through the lookup.

**Answer:** Event history or the trail, event name `AuthorizeSecurityGroupIngress` or `RevokeSecurityGroupIngress`, resource the security group id, time window yesterday. Read the principal and the CIDR they added. If the principal is a pipeline role, check the commit. If it is a user at an unexpected IP, treat it as an incident. Then confirm the current rule still matches what you intended, because a later call may have changed it again.

---

#### 26. Why would an event appear in one region’s history and not another?

**Answer:** Most service APIs are regional. The event is stored in the region where the call was made. A multi-region trail copies them to one S3 prefix structure so you can search centrally. IAM is global, but many IAM events are recorded in us-east-1. If you only look at ap-south-1 event history, you can miss them. This is a common interview follow-up. Mention it.

---

#### 27. How do you keep CloudTrail events long enough for a compliance request without querying S3 by hand every time?

**Answer:** Deliver to S3 with lifecycle to the required retention, and optionally to CloudWatch Logs for recent searches. For heavier queries, catalog the S3 data with Glue or query it with Athena. You do not keep years of events only in CloudWatch Logs. Cost and retention belong on S3. Athena is the usual “security asked for a quarter of API calls” tool.

---

#### 28. What is CloudTrail Lake?

**Answer:** A managed store for CloudTrail events with SQL queries, so you do not have to build Athena yourself. It is optional. A trail to S3 remains the durable export. Lake is convenient if the team will actually query it. Mention it as an option, not as a replacement for understanding trails.

---

#### 29. An attacker who compromised a role deleted objects in a bucket. Will CloudTrail show the deletes?

**Answer:** Only if **S3 data events** were enabled for that bucket before the delete. Management events will show if they changed the bucket policy or disabled logging, not each `DeleteObject`. This is the argument for data events on sensitive buckets and for a trail the attacker cannot stop. Application-level deletes through the AWS API are still API calls. Deletes inside a database are not in CloudTrail.

---

#### 30. What would you put in place in a new account before the first production workload?

**Answer:** A multi-region trail with log file validation, delivery to a locked S3 bucket, an alarm on `StopLogging` and on root login, and data events for any bucket that will hold customer data. Tell the team that event history is for quick lookups and the trail is the record. Pair it with CloudWatch alarms for the workload itself. CloudTrail does not page you when the API returns 500 to users.

---
