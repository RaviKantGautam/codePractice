# AWS Step Functions — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS Step Functions?

**Answer:** Step Functions runs a **state machine**: a JSON or YAML definition (Amazon States Language) of steps, transitions, retries, and error handling. Each execution has an id and a history. Steps can call Lambda, ECS, SQS, DynamoDB, and many other services, or wait for a callback. You use it when a business process has several stages and you do not want that control flow buried in one function.

---

#### 2. When would you use a state machine instead of one Lambda calling another?

**Answer:** Use Step Functions when there are branches, parallel work, waits, or retries you want to see in a console and in an execution history. Use a single function when the work is one short step. Chaining Lambdas by hand loses the history, duplicates retry code, and makes partial failure hard to explain. A queue between services is better when the steps are independent and owned by different teams (choreography). Step Functions is orchestration: one definition owns the sequence.

---

#### 3. What is the difference between Standard and Express workflows?

**Answer:**

| | Standard | Express |
| --- | --- | --- |
| Duration | Up to one year | Up to five minutes |
| Rate | Lower, for business processes | Very high, for event processing |
| History | Full visual execution history | Logs, not a year-long history |
| Pricing | Per state transition | Per execution, duration, and memory |
| Fit | Orders, approvals, human waits | Streaming, IoT, high-volume short flows |

Express also comes in synchronous (caller waits) and asynchronous forms. Do not pick Express for a workflow that waits for a human.

---

#### 4. What are the common state types?

**Answer:**

* **Task:** do work (invoke Lambda, call a service, start a job).
* **Choice:** branch on the input JSON.
* **Parallel:** run branches at the same time and continue when they finish.
* **Map:** run the same steps for each item in an array.
* **Wait:** sleep for seconds or until a timestamp.
* **Pass:** reshape JSON without calling anything.
* **Succeed / Fail:** end the execution.

A definition is these states plus `Next`, `End`, `Retry`, and `Catch`.

---

#### 5. How does data move between states?

**Answer:** The execution has a JSON input. Each state can filter it with `InputPath`, send part of it to the task with `Parameters`, and write the result back with `ResultPath` so you do not wipe the original input. `OutputPath` chooses what the next state sees. The usual bug is a Task that replaces the whole JSON with a Lambda response and the next state cannot find `$.orderId`. Use `ResultPath` to nest the response under a key.

---

#### 6. What is an execution, and can you start two for the same order?

**Answer:** An execution is one run, with an execution name and an ARN. Standard workflows can use a name you supply. Starting a second execution with the **same name** while one is running fails, which is a useful idempotency guard (one execution per order id). If the first has already finished, the name can often be reused depending on the API. Express executions are not idempotent by name in the same way. Still store “this order already started” in your database for the user-facing API.

---

## Errors, retries, and service integrations

#### 7. How do Retry and Catch work?

**Answer:** On a Task you list **Retry** rules: error name, interval, backoff, and max attempts. **Catch** sends matching errors to a fallback state (compensate, notify, or Fail). Retries happen before Catch. Use Retry for timeouts and throttling. Use Catch when retries are exhausted or the error is permanent (bad input). A state machine without Catch fails the whole execution on the first unhandled error, which may be what you want if you also alarm on failed executions.

---

#### 8. What errors should you retry?

**Answer:** `States.Timeout`, `States.TaskFailed` for transient downstream errors, and service throttling (`Lambda.TooManyRequestsException`, `States.Timeout`). Do not retry a validation error the same way forever. Set `MaxAttempts` and a backoff. Add jitter through the backoff rate so a downed dependency is not hammered at the same second by every execution.

---

#### 9. What is a service integration, and when do you skip Lambda?

**Answer:** Step Functions can call AWS APIs directly (DynamoDB `putItem`, SQS `sendMessage`, ECS `runTask`) using the state machine’s IAM role. That avoids a Lambda whose only job is to call one API. Use Lambda when you have real logic. The integration pattern can be **request response** (fire and return), **run a job** (wait until an ECS task or a batch job finishes), or **wait for a callback** with a task token.

---

#### 10. What is the callback pattern (`.waitForTaskToken`)?

**Answer:** The task pauses and gives your worker a **task token**. The state machine does not continue until someone calls `SendTaskSuccess` or `SendTaskFailure` with that token, or the timeout fires. Use it for human approvals, manual review, or a worker that cannot be polled easily. The token must be stored safely. If you lose it, the execution waits until it times out. Heartbeats (`SendTaskHeartbeat`) show the worker is alive.

---

#### 11. How do you pass a task token to a human approval?

**Answer:** The Task sends the token to SQS, SES, or a database row in the approval tool. The approve action in your API calls `SendTaskSuccess` with the token and the decision JSON. Set a timeout on the task so a forgotten approval fails or escalates. Do not keep the token only in an email if you cannot recover it. Store it on the approval record.

---

#### 12. What is a Map state, and what is Distributed Map?

**Answer:** **Map** runs the same iterator states for each element of an array in the input. Inline Map is limited by payload size and is fine for tens of items. **Distributed Map** reads a large list from S3 or a JSON array and fans out up to thousands of child executions. Use Distributed Map for “process every object under this prefix”. Use a plain loop in Lambda only for a handful of items where a state machine adds no value.

---

## Design choices

#### 13. How do you choose between Step Functions and SQS choreography?

**Answer:**

* **Step Functions:** one team owns the end-to-end process, you need the history, timeouts, and compensation in one place.
* **SQS or EventBridge choreography:** each service reacts to events and does not know the whole flow. Better when teams deploy independently.

A hybrid is normal: the state machine does the order flow, and one task publishes an event for analytics. Do not rebuild a 20-service company inside one state machine JSON file.

---

#### 14. What is compensation, and where does it live?

**Answer:** Compensation undoes a step that succeeded when a later step fails (refund a charge, release inventory). In a state machine it is a Catch path that runs compensating tasks. It must be idempotent, because retries can run it twice. This is the orchestration version of a saga. The state machine makes the path visible. It does not make the undo logic correct by itself.

---

#### 15. How large can the payload be?

**Answer:** Standard workflow state payloads are limited (256 KB of input and output per state is the figure to remember). Do not pass files through the state JSON. Pass an S3 key or a database id. Distributed Map exists because a giant array does not fit in one execution input. If you hit `States.DataLimitExceeded`, move the data out of the execution.

---

#### 16. How do you stop a stuck execution?

**Answer:** `StopExecution` with a cause. The state machine role or the operator role needs that permission. Stopping does not automatically roll back work already done. Design Catch and compensation, or have an operator playbook. Executions also end when a state’s timeout or the whole execution timeout elapses. Set timeouts so a lost callback cannot run for a year unnoticed.

---

#### 17. How does IAM work?

**Answer:** The state machine has an **execution role** that needs permission for every service integration it calls (`lambda:InvokeFunction` on specific functions, `sqs:SendMessage` on one queue, and so on). Callers need `states:StartExecution` on that state machine. Least privilege means one role per workflow, not `states:*` and `lambda:*` on `*`.

---

#### 18. How do you deploy a state machine?

**Answer:** As code: SAM, CDK, CloudFormation, or Terraform. The definition is a file in git, not a JSON blob edited in the console. CI publishes a new revision. Running executions keep the revision they started with, so a deploy does not mutate in-flight orders. That is what you want. Test the definition with the Step Functions local testing or with a dev account execution before you promote it.

---

#### 19. What is a state machine alias or version?

**Answer:** You can publish numbered versions and point an alias at a version, including gradual traffic shifting between versions. Use this for a risky change to a busy Express or Standard workflow. In-flight executions stay on the version they started. New `StartExecution` calls use the alias. Do not test a breaking definition change only in the console editor against production.

---

#### 20. How do you observe failures?

**Answer:** CloudWatch metrics for executions failed, throttled, and timed out, plus logs. Standard executions have a visual history you can open from the execution ARN you logged at start. Emit the execution ARN in the API response and in your logs. Alarm on failed executions and on age if you use a queue in front of `StartExecution`. Express workflows need log level set to capture failures, because they do not keep the same history.

---

## Scenarios

#### 21. The API must return in under a second, but the workflow takes two minutes. How do you connect them?

**Answer:** The API calls `StartExecution` and returns **202** with the execution ARN or a job id. It does not call `StartSyncExecution` (that waits). The client polls your status endpoint, which calls `DescribeExecution`, or a later state notifies the user. Express synchronous workflows are only for work that finishes within the HTTP timeout.

---

#### 22. A Lambda task succeeded, the next state failed, and the Lambda ran again on retry of the whole execution. The email was sent twice. What do you change?

**Answer:** Do not retry the entire business action blindly. Make the email step idempotent (store “email sent for order id”), and use Retry on the failing state only, not “start a second execution” without a guard. Catch the failure and compensate instead of re-entering the send step. Execution names based on order id stop a duplicate start while the first run is open.

---

#### 23. Inventory is reserved, then payment fails. How should the state machine behave?

**Answer:** Payment is a Task with Retry on timeout only. On payment failure, Catch runs a **release inventory** task, marks the order failed, and ends. The release task is idempotent. The user-facing status comes from the order row, which the state machine updates, not from a guess about which state is running. This is a short saga.

---

#### 24. You have 100,000 S3 objects to resize. Lambda times out if you loop in one function. What state do you use?

**Answer:** A **Distributed Map** over the S3 prefix, with an iterator that invokes one Lambda (or an ECS task) per object and a concurrency limit so you do not overload the image service. Failures can be written to a results bucket. One execution per object from your own fan-out loop is harder to operate. One Lambda that lists and processes everything will hit the 15-minute limit.

---

#### 25. A Wait state of 24 hours is used to remind a user. The deploy replaces the state machine that night. Does the wait continue?

**Answer:** Yes. The running execution stays on the definition version it started with and wakes up after the wait. The new definition applies to new executions. Do not delete the old Lambda the waiting execution will call next until those executions finish. Version the functions or keep the old targets until the long waits drain.

---

#### 26. How do you test a Choice state without deploying the whole stack?

**Answer:** Feed the Choice a JSON input in a unit test of the definition (Step Functions local, or the console’s test with a mocked state) and assert the next state. Choice rules use comparison operators on paths (`NumericGreaterThan`, `StringEquals`). A missing field does not match and falls through to `Default`. Always set a Default, or an unexpected payload fails the execution.

---

#### 27. The state machine role can invoke any Lambda in the account. Why is that a problem?

**Answer:** Anyone who can edit the definition (or a bug in a template) can make the workflow call a function in another system and pass it the execution input, which may contain personal data. Scope `lambda:InvokeFunction` to the function ARNs this workflow uses. Same for SQS and DynamoDB. Review the role when you add a state.

---

#### 28. Express workflow executions are missing from the console history the next day. Is data lost?

**Answer:** Express does not keep Standard’s execution history. Turn on CloudWatch logs for the workflow if you need to debug after the fact. The business result should be in your database either way. Do not use Express as an audit trail. Use Standard when auditors or support staff open the visual history for a single order months later.

---

#### 29. How would you add a manual review only for orders over a threshold?

**Answer:** A Choice state on `$.amount`. Under the threshold, go to the fulfill task. Over it, go to a callback task that writes an approval row and waits for the task token. On approve, continue. On reject or timeout, compensate and fail. The API that approves must check the caller is allowed to approve. The state machine does not know your org chart unless you enforce it in that API.

---

#### 30. What is a sensible first workflow for a backend team new to Step Functions?

**Answer:** A Standard workflow for one business process you already struggle to retry: for example “create order, charge, notify”. Three Task states, Retry on the charge, Catch to a failure state that marks the order failed, execution name equal to the order id, payload limited to ids, and an alarm on failed executions. Add Parallel, Map, and callbacks when that is in production and understood. Do not start with a 40-state machine.

---
