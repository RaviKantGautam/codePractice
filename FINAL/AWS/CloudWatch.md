# Amazon CloudWatch — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon CloudWatch?

**Answer:** CloudWatch is the monitoring service for AWS and for your application. It stores **metrics**, **logs**, and **alarms**, and it can drive dashboards and actions. It answers “is the service healthy right now?” It is not an audit trail of who called an API. That is CloudTrail.

---

#### 2. What is a metric, a namespace, and a dimension?

**Answer:** A **metric** is a time series of numbers, such as `CPUUtilization` or `5xx`. A **namespace** groups metrics (`AWS/EC2`, `AWS/Lambda`, or a custom `Orders/API`). **Dimensions** are labels that split the series (`InstanceId`, `FunctionName`). An alarm on CPU without the right dimension is an average of everything, which hides the one instance that is on fire.

---

#### 3. What is the difference between standard and high-resolution metrics?

**Answer:** Standard resolution is one minute. High resolution can be one second, which you need for a short alarm on a custom metric. Most AWS service metrics are one minute. Do not alarm on a five-second blip of CPU. Alarm on sustained error rate or latency. High resolution costs more and is for the few metrics where a minute is too slow.

---

#### 4. What does an alarm actually watch?

**Answer:** A statistic (average, sum, p99, maximum) over a period, for a number of evaluation periods. Example: sum of 5xx greater than 20 for 3 periods of 1 minute. The alarm goes `ALARM`, `OK`, or `INSUFFICIENT_DATA`. Actions can notify SNS, scale an Auto Scaling group, or create an incident. A threshold with no action is a dashboard decoration.

---

#### 5. Why do new resources show `INSUFFICIENT_DATA`?

**Answer:** Not enough points have arrived, or the metric is not being published because the resource is idle (some metrics only appear when there is traffic). Treat missing data explicitly: either missing is OK (a queue with no messages) or missing is a breach (a heartbeat that should always exist). The wrong choice pages you every night or hides an outage.

---

#### 6. What is a dashboard for, if alarms exist?

**Answer:** Alarms page a human about a decision you already made. A dashboard is how you see the shape of an incident: latency, error rate, saturation, and deploys next to each other. Build one per service with the few graphs that explain user pain. A dashboard of forty CPU charts will not be opened.

---

## Logs

#### 7. How do application logs get to CloudWatch?

**Answer:** A **log group** holds **log streams** (one per instance, task, or Lambda environment). EC2 uses the CloudWatch agent. ECS and Lambda can ship stdout with the `awslogs` driver or the Lambda runtime. You give the agent or the task execution role permission to `CreateLogStream` and `PutLogEvents`. Logs are not searchable in a useful way until they are actually shipped. A file on disk on one instance is not a log strategy.

---

#### 8. What is a metric filter?

**Answer:** A pattern on a log group that turns matching lines into a metric. Example: count lines containing `"level":"ERROR"` and alarm when the count spikes. Use it when the platform metric is not enough (business errors, failed payments). Keep the pattern strict so a debug line does not increment the error metric. Prefer structured JSON logs so the filter is reliable.

---

#### 9. What are Logs Insights?

**Answer:** A query language over log groups. You filter, parse fields, and aggregate (`filter status >= 500 | stats count() by path`). It is how you debug after an alarm. It is not a long-term data warehouse. Queries scan the retention window you set and you pay for data scanned. Narrow the time range first.

---

#### 10. How long are logs kept, and what should you set?

**Answer:** The default is often **never expire**, which becomes a surprise bill. Set retention on every log group: shorter for debug-heavy apps, longer for security-relevant logs if policy requires it. Ship audit logs to S3 (and maybe Glacier) if you must keep them for years. CloudWatch is the hot store. S3 is the cheap archive.

---

#### 11. What is the difference between an application log and a VPC flow log or ALB access log?

**Answer:** Application logs are what your process prints. ALB access logs and VPC flow logs are AWS-generated records of requests or packets, usually delivered to **S3** (flow logs can also go to CloudWatch). Use ALB logs to see a 502 the app never logged because it never received the request. Use app logs to see the exception. You often need both.

---

#### 12. Why might two log lines from one request be hard to find?

**Answer:** They are in different streams or services and nothing ties them together. Put a **request id** (and a trace id if you have X-Ray or OpenTelemetry) on every line. API Gateway and ALB give you an id. Log it in the application. Without it, Insights queries are guesses across a time window.

---

## Metrics that matter

#### 13. What is the difference between `Sum` and `Average` on a count metric?

**Answer:** Error **counts** should use **Sum**. An average of a count across periods is hard to explain and easy to under-alarm. Latency should use a percentile (`p99`) if you publish one, not only the average. An average latency of 80 ms can hide a p99 of 4 seconds. CPU is usually Average or Maximum depending on whether one hot instance matters.

---

#### 14. How do you publish a custom metric?

**Answer:** `PutMetricData` with a namespace, name, value, and dimensions, or an **embedded metric format** line in your logs that CloudWatch extracts. EMF avoids a separate API call on the hot path and keeps the metric tied to the log line. Do not create a dimension with unbounded values (user id, request id). That blows up the number of time series and the bill. Dimensions should be low cardinality: service, route, status class.

---

#### 15. What is embedded metric format?

**Answer:** A JSON log line that includes a special block naming the metrics and dimensions, plus the values. CloudWatch Logs turns it into metrics. You still see the raw line in Insights. Use it from Lambda and containers instead of calling `PutMetricData` for every request. The IAM role needs log permissions. It does not need `cloudwatch:PutMetricData` for the EMF path.

---

#### 16. Which service metrics would you alarm on for an HTTP API on ECS behind an ALB?

**Answer:** ALB target 5xx and ELB 5xx, target response time, healthy host count, and the app’s own error metric if 5xx is not the whole story. ECS `RunningTaskCount` versus desired. CPU is secondary. Page on error rate and on zero healthy hosts. Ticket on sustained latency. Do not page on a single CPU spike.

---

#### 17. How do you avoid alarm noise?

**Answer:** Alarm on symptoms users feel, require several periods, and use a rate or a percentage when traffic varies. Separate warning from page. An alarm that fires every deploy will be ignored the one time it is real. If deploys always blip 5xx, fix the deploy (drain, grace period) instead of raising the threshold until the alarm is useless.

---

#### 18. What is a composite alarm?

**Answer:** An alarm on other alarms, with AND or OR. Example: page only when error rate is high **and** request count is above a floor, so a quiet night with one error does not wake anyone. Use it to express “this is an incident”, not to hide every signal. The child alarms still exist for the dashboard.

---

## Traces and cost

#### 19. What is X-Ray, and how does it relate to CloudWatch?

**Answer:** X-Ray (and Application Signals / OpenTelemetry on AWS) traces a request across services: API Gateway, Lambda, a downstream call. CloudWatch metrics tell you the API is slow. A trace tells you which hop is slow. Enable tracing on the edge and instrument the AWS SDK so the segment includes DynamoDB or S3 time. Traces are sampled. You will not get one for every request unless you pay for that.

---

#### 20. What is Contributor Insights or Logs anomaly detection useful for?

**Answer:** Finding which dimension or which log pattern dominates (the one customer, the one IP, the new error string) without writing a query during the incident. Anomaly detection on a metric can alarm when today’s shape does not match the past. It false-positives on deploys and on Monday traffic. Use it as a hint, and keep explicit alarms for the SLOs you actually promise.

---

#### 21. Why did the CloudWatch bill grow after a new feature?

**Answer:** A custom metric with a high-cardinality dimension, debug logs at INFO on every request with no retention limit, or a dashboard that refreshes expensive Logs Insights queries. Check the number of metrics and ingestion bytes. Fix the dimension, drop the log level, set retention, and sample debug logs. Metrics and logs are cheap until a loop publishes one of each per user.

---

#### 22. How do alarms reach a human?

**Answer:** An alarm action publishes to **SNS**. SNS fans out to email, a chat webhook, or a paging tool. The topic policy must allow CloudWatch to publish. Test the path. An alarm that only emails a shared inbox nobody reads is not an on-call system. Lambda can also subscribe if you need to format the message.

---

#### 23. What is the difference between CloudWatch alarms and EventBridge rules on the same event?

**Answer:** An alarm watches a **metric** over time and flips state. EventBridge matches **events** (a deploy, an EC2 state change, an alarm state change). You can send alarm state changes to EventBridge for routing. Do not rebuild “CPU high for 5 minutes” as an EventBridge rule. That logic is an alarm.

---

## Scenarios

#### 24. Users see errors, but CPU and memory look fine. Where do you look?

**Answer:** ALB 5xx and latency, application error logs for the same minute, dependency metrics (RDS connections, DynamoDB throttles), and a trace if you have one. The app can be broken while the process is idle, waiting on a database or failing fast. Saturation metrics are not a substitute for the error rate.

---

#### 25. The alarm fired overnight and recovered before anyone opened the laptop. How do you still learn from it?

**Answer:** The alarm history and the graphs for that window stay in CloudWatch. Look at logs for the request ids in that period. If it recovers in one minute every night, it is probably a cron or a scale event, and the alarm period is too sensitive. Adjust the alarm or fix the job. Do not delete the alarm because it was brief.

---

#### 26. Lambda errors are high in the Lambda metric, and API Gateway 5xx is low. How can both be true?

**Answer:** The function is failing on **asynchronous** invocations (S3, SNS, EventBridge) that do not go through the API. Or the API is returning a handled 4xx while a background path throws. Split alarms by trigger, and log the event source. One error metric for the whole function mixes user traffic with batch work.

---

#### 27. You need to know if a queue consumer is stuck. Which metric?

**Answer:** SQS `ApproximateAgeOfOldestMessage`, alarmed above the time you are willing to be behind. Depth alone is ambiguous. Also alarm on the DLQ’s visible messages. The consumer’s CPU is optional. Age is the user-facing symptom for a backlog.

---

#### 28. A developer wants to log the full request body on every call. What do you push back on?

**Answer:** Bodies contain passwords, tokens, and personal data, and they dominate ingestion cost. Log the request id, route, status, and duration always. Log a body only in a debug mode, with fields redacted, for a short time. Metric filters and traces solve most “what failed” questions without a copy of every payload.

---

#### 29. How would you add monitoring to a new service in the first week?

**Answer:** Ship structured logs to a log group with retention. Alarm on ALB or API Gateway 5xx and latency, and on healthy targets or Lambda errors. Add one business metric (orders created, payments failed) via EMF. Put those on one dashboard. Add a trace header. Expand after the first real incident shows a hole. Do not wait for a perfect SLO document to have the 5xx alarm.

---

#### 30. How do you tell CloudWatch and CloudTrail apart in an interview answer?

**Answer:** CloudWatch is performance and health: metrics, logs, alarms, traces. CloudTrail is an audit log of **API calls**: who stopped the instance, who changed the security group, from which IP, and whether it succeeded. During an incident you use both. CloudWatch shows the symptom. CloudTrail shows whether a human or a pipeline changed infrastructure at that minute.

---
