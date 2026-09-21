# AWS CodeDeploy — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS CodeDeploy?

**Answer:** CodeDeploy rolls a new revision out to compute you already have: EC2 instances, on-prem servers, Lambda functions, or an ECS service. It follows a deployment configuration (all at once, half at a time, canary, blue/green) and can stop and roll back if a hook or an alarm fails. It does not build the artifact. CodeBuild does that. It does not decide the pipeline order. CodePipeline does that.

---

#### 2. What is an application, a deployment group, and a revision?

**Answer:**

* **Application:** a name for the thing you deploy (the orders service).
* **Deployment group:** where it goes (this ASG, this ECS service, this Lambda function) and how (the configuration and alarms).
* **Revision:** the exact bits for one deploy (an S3 zip, an image definition, a Lambda version).

One application can have a dev deployment group and a prod deployment group with different configs.

---

#### 3. What platforms does CodeDeploy support?

**Answer:**

* **EC2/on-premises:** an agent on the instance runs scripts from an `appspec.yml`.
* **Lambda:** shifts traffic between function versions or aliases.
* **ECS:** blue/green via a load balancer, using task sets and a listener.

The appspec and the hooks differ by platform. An EC2 appspec does not deploy Fargate. ECS blue/green is a different path from “SSH and pull”.

---

#### 4. What is an appspec file?

**Answer:** `appspec.yml` tells CodeDeploy what to copy and which lifecycle hooks to run. On EC2 it lists files to place and scripts for hooks such as `BeforeInstall`, `AfterInstall`, `ApplicationStart`, and `ValidateService`. On ECS and Lambda the file points at the target revision and related settings. It lives with the revision. The agent or the service runs it. You do not run it by hand on each box.

---

#### 5. What is a deployment configuration?

**Answer:** The speed and shape of the rollout. Examples: `AllAtOnce`, `HalfAtATime`, `OneAtATime`, and canary percentages. ECS and Lambda have their own configurations (for example a canary that shifts 10 percent of traffic, waits, then shifts the rest). Production user-facing services should not use all-at-once unless downtime is acceptable. One-at-a-time is slow and safe for a small fleet.

---

#### 6. How is CodeDeploy different from an Auto Scaling instance refresh or an ECS rolling update?

**Answer:** An instance refresh replaces instances from a new launch template. An ECS rolling update starts new tasks in the same service. CodeDeploy adds a **deployment object** with hooks, traffic shifting, and rollback tied to alarms. ECS can do a simple rolling update without CodeDeploy. You bring CodeDeploy in when you want blue/green or a controlled canary with automatic rollback. You do not need it for every service. Say that in an interview. It shows judgment.

---

## EC2 deployments

#### 7. What does the agent do on an instance?

**Answer:** The CodeDeploy agent polls or receives the deployment, downloads the revision from S3, and runs the appspec hooks in order. The instance profile needs permission to read that bucket and to talk to CodeDeploy. If the agent is stopped, the instance never updates. User data or a golden AMI should install and start the agent. A deployment group finds instances by **tags** or by an Auto Scaling group.

---

#### 8. What are the important EC2 hook order points?

**Answer:** `ApplicationStop` (old version), `BeforeInstall`, `AfterInstall`, `ApplicationStart`, `ValidateService`. Stop the old process before you overwrite files. Start it after. `ValidateService` should fail the deploy if the health check is red. If you only copy files and never fail a hook, CodeDeploy will mark a broken release as successful.

---

#### 9. What is a lifecycle event failure?

**Answer:** A hook script exited non-zero or timed out. CodeDeploy marks the instance failed and, depending on the configuration, stops the deployment and rolls back. The script log on the instance and the deployment event in the console show which hook. A timeout that is shorter than a slow `systemctl start` looks like a failed deploy. Set the timeout to match the script, and make the script fail clearly when the process is not listening.

---

#### 10. How do in-place and blue/green differ on EC2?

**Answer:** **In-place** updates the instances you already have, in batches. **Blue/green** launches new instances (usually a second Auto Scaling group), installs the revision, and shifts the load balancer to them, then terminates the old group after a wait. Blue/green needs more capacity and gives you a faster way back: shift traffic to the old group. In-place uses less hardware and is harder to undo if the new code corrupts local state.

---

#### 11. What happens to an instance that is unhealthy before the deploy starts?

**Answer:** CodeDeploy can skip unhealthy instances or fail, depending on settings. If you skip them, you can “succeed” while leaving old code on the broken instance, and when it recovers it serves the old version. Know which setting you use. An ASG health check should replace bad instances so the fleet is homogeneous after the deploy, not a mix of revisions.

---

#### 12. How do rollbacks work on EC2?

**Answer:** You can enable automatic rollback on failed deployment or when a CloudWatch alarm fires. Rollback redeploys the last good revision. It is not a database restore. If the new version ran a destructive migration, rolling the code back is not enough. Time the alarm so a short blip does not roll back a good deploy, and so a real failure does not bake for an hour.

---

## Lambda and ECS

#### 13. How does a Lambda deployment shift traffic?

**Answer:** CodeDeploy uses an alias that points at versions. It publishes the new version and shifts the alias weight: canary (a small percent, then the rest) or linear (a percent every few minutes) or all at once. Hooks (`BeforeAllowTraffic`, `AfterAllowTraffic`) can run tests. If a hook fails or an alarm fires, the alias returns to the old version. Production should invoke the **alias**, not `$LATEST` and not a raw version number.

---

#### 14. What is a BeforeAllowTraffic hook for?

**Answer:** A Lambda function CodeDeploy invokes after the new version exists and before users are sent to it. Use it for a smoke test against the new version’s ARN. If the test fails, users never see the new version. Keep the hook fast and deterministic. A flaky smoke test will block every release. The hook’s role can invoke the new version. It should not be the same broad role as the application if you can avoid it.

---

#### 15. How does ECS blue/green with CodeDeploy work?

**Answer:** CodeDeploy creates a replacement task set with the new image, registers it with a **test** or production listener on the load balancer, shifts traffic (canary or all at once), and terminates the original task set after a bake time. You need an ALB or NLB, two target groups, and a service configured for blue/green (or the newer blue/green APIs CodeDeploy drives). A rolling ECS update does not use a second target group. Blue/green does.

---

#### 16. Why would an ECS deploy succeed in CodeDeploy and still serve old traffic?

**Answer:** The listener rule is still sending production traffic to the original target group, or the bake time has not shifted weight, or you watched the test listener and not the production listener. Confirm the listener rule’s target group weights. Also confirm the new tasks passed the target group health check. CodeDeploy will not shift traffic to unhealthy targets if the deployment is configured correctly. If it is not, you can shift to a target group with no healthy tasks and cause an outage.

---

#### 17. What IAM permissions does CodeDeploy need?

**Answer:** A **service role** that CodeDeploy assumes, with permission to update the ECS service, modify the load balancer and target groups, pass roles, or call Lambda and read the revision in S3. The pipeline role is separate: it can call `codedeploy:CreateDeployment`. Do not use the application’s runtime role as the CodeDeploy service role. The deploy role can change infrastructure. The app role should only read and write data.

---

#### 18. What is a bake time?

**Answer:** The wait after traffic shifts before CodeDeploy terminates the old ECS tasks or finishes the Lambda shift. During the bake, alarms can still trigger a rollback. Set it long enough to see error rates, and short enough that a bad deploy does not sit there all afternoon while you pay for two fleets. If nobody watches alarms, a long bake time does nothing. Wire the alarm to the deployment group.

---

## Operations

#### 19. What should trigger an automatic rollback?

**Answer:** A failed lifecycle hook, a failed deployment, or a CloudWatch alarm on 5xx, latency, or Lambda errors during the bake. The alarm must exist before the deploy and must actually go into alarm when the new code is bad. An alarm that never fires will not save you. Test the rollback in a non-production group so you know the alias or the listener moves back.

---

#### 20. How do you stop a deployment that is going wrong but has not failed a hook?

**Answer:** Stop the deployment in the console or API. For ECS blue/green, stopping should send traffic back if rollback is enabled. Know the behavior for your configuration before the incident. A manual listener change is the backup if CodeDeploy is stuck. Then fix the revision. Do not keep retrying the same broken artifact.

---

#### 21. What is a deployment’s relationship to a database migration?

**Answer:** CodeDeploy does not version the schema. Run migrations as a separate, controlled step that is compatible with the **old** code still running during a rolling or blue/green shift. Expand, then deploy code, then contract later. If the new code requires a column the old code does not tolerate, blue/green will break the old tasks as soon as the migration runs. Order the changes.

---

#### 22. How do you deploy the same revision to prod that you deployed to staging?

**Answer:** Promote the artifact (S3 revision id or image digest), do not rebuild. The deployment group changes. The revision does not. Rebuilding on the prod branch can produce different bytes if dependencies float. The pipeline should pass the same artifact object from the staging deploy action to the prod deploy action, with a manual approval in between if you want one.

---

#### 23. What does “minimum healthy hosts” mean?

**Answer:** The deployment configuration will not continue if too many instances are unhealthy or failed. It protects you from a bad revision taking the whole fleet down in one batch. If the minimum cannot be met because the fleet was already sick, the deploy fails closed. Fix the fleet or adjust the configuration on purpose, not by switching to all-at-once in the incident without understanding it.

---

#### 24. How do you see why a deploy failed?

**Answer:** The deployment’s lifecycle events, the instance or task id that failed, the hook script output, and the load balancer health checks. CloudTrail shows who started the deployment. CodeDeploy’s own logs matter more than the pipeline’s “action failed” line. The pipeline only knows that CreateDeployment eventually reported failure.

---

## Scenarios

#### 25. Half the EC2 instances run the new build and half run the old one after a “successful” deploy. What happened?

**Answer:** The deployment skipped instances without the agent or without the right tag, or a later Auto Scaling launch used an old AMI and user data that did not install the new revision. New instances should get the current revision automatically if the deployment group is tied to the ASG correctly. If they launch from an AMI that bakes code, the AMI and CodeDeploy are two sources of truth. Pick one.

---

#### 26. Lambda canary sends 10 percent of traffic to the new version and the error alarm fires. What do users see after rollback?

**Answer:** The alias should point back at the previous version, so new invocations use the old code. In-flight invocations on the new version still fail. The 90 percent on the old version were fine the whole time. That is the point of the canary. If the function was invoked by a version ARN directly, those callers bypass the alias and ignore the rollback. Fix the callers.

---

#### 27. ECS blue/green cannot place the green tasks. What is the usual cause?

**Answer:** The cluster has no capacity (EC2) or no IPs or vCPU quota (Fargate), or the new task definition fails health checks. CodeDeploy waits and then fails. The original task set should keep serving. Read the ECS service events, not only CodeDeploy. A bad image that crashes is a health-check failure. A subnet out of IPs is a placement failure. They look similar from the pipeline and different in the ECS events.

---

#### 28. You want a 10 percent canary for an ECS service that today uses a rolling update. What has to exist first?

**Answer:** Two target groups, a listener that can shift weight, a CodeDeploy application and deployment group for ECS, and a service that uses the blue/green deployment controller. The pipeline’s deploy action must be CodeDeploy, not the ECS rolling action. Practice once in dev. Switching controllers is a design change, not a checkbox on the old service.

---

#### 29. A hook script assumes bash and the instances are Amazon Linux 2023. It worked on the old AMI. Why might it fail now?

**Answer:** The script used a path, a package, or a `python` binary that the new AMI does not have. Hooks run on the instance OS, not in your laptop. Test the revision against the current AMI. Print the error to stdout so the agent captures it. A hook that works only on the AMI you remember is a failed deploy waiting for the next image update.

---

#### 30. When would you skip CodeDeploy entirely?

**Answer:** When a simple ECS rolling update or a Lambda alias update in CloudFormation is enough, and you do not need traffic shifting or hook-based rollback. When the compute is a single container you replace by updating the service in the same pipeline action. Choose CodeDeploy when the extra control (canary, blue/green, automatic rollback on an alarm) is worth the setup. A small internal worker queue does not need a canary. A public API often does.

---
