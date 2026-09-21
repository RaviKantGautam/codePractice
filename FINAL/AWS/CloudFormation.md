# AWS CloudFormation — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS CloudFormation?

**Answer:** CloudFormation creates and updates AWS resources from a template (YAML or JSON). A **stack** is one running copy of that template. You change the template, update the stack, and CloudFormation figures out what to add, modify, or delete. It is infrastructure as code. The alternative of clicking in the console does not review, does not roll back, and does not reproduce the environment.

---

#### 2. What is a template, a stack, and a change set?

**Answer:**

* **Template:** the desired resources and their properties.
* **Stack:** the resources CloudFormation created in an account and region from that template.
* **Change set:** a preview of what an update **would** do, before you execute it. Use it on production so a surprise replacement is visible.

A stack is not “a folder of files”. One stack update is one transaction CloudFormation tracks.

---

#### 3. What does a resource look like in a template?

**Answer:** A logical id, a `Type` such as `AWS::SQS::Queue`, and `Properties`. Other resources refer to it with `!Ref` or `!GetAtt`. The logical id is how CloudFormation tracks the resource across updates. If you rename the logical id, CloudFormation thinks the old resource was deleted and a new one should be created. That mistake replaces databases.

---

#### 4. What is the difference between parameters, mappings, and outputs?

**Answer:**

* **Parameters:** inputs at deploy time (environment name, instance size), so the same template serves dev and prod.
* **Mappings:** static lookup tables inside the template (AMI ids per region, if you still do that yourself).
* **Outputs:** values other stacks or humans need afterward (a URL, a queue ARN).

Do not put secrets in parameters in the console history if you can read them from Secrets Manager inside the template instead. Parameters are not a secret store.

---

#### 5. What are intrinsic functions you will actually see?

**Answer:** `!Ref` (the default value of a resource, often an id or name), `!GetAtt` (a specific attribute, such as an ARN), `!Sub` (string interpolation), `!Join`, and conditions (`!If`, `!Equals`). `Fn::GetAZs` and `!Select` show up in network templates. You do not need every function. You need to read a template without guessing.

---

#### 6. How does CloudFormation decide to update in place or replace a resource?

**Answer:** Each property is documented as “update requires no interruption”, “some interruption”, or “replacement”. Changing an S3 bucket name or an RDS subnet group often **replaces** the resource. Replacement can mean delete and create. For a database, that is data loss unless deletion protection and a snapshot policy stop it. Read the change set for the word **Replace** before you execute.

---

## Updates, failure, and deletion

#### 7. What happens if an update fails halfway?

**Answer:** By default CloudFormation rolls the stack back to the last successful state. Resources it already changed are reverted where that is possible. Rollback can also fail, and then the stack is `UPDATE_ROLLBACK_FAILED`, which needs a human. Watch the events tab. The error is usually one resource’s API message (a quota, a name collision, a missing permission), not “CloudFormation is down”.

---

#### 8. What is a stack policy?

**Answer:** A policy that prevents updates to specific resources, such as “do not replace this database”. It is a guardrail on top of IAM. Use it for stateful resources. It is not a backup. Deletion protection on the resource itself (RDS, DynamoDB) should also be on.

---

#### 9. What is deletion policy?

**Answer:** On a resource, `DeletionPolicy: Retain` keeps the resource when the stack is deleted or the resource is removed from the template. `Snapshot` (where supported) takes a snapshot first. `Delete` is the default and will remove the bucket, table, or instance. Set `Retain` or `Snapshot` on anything you cannot recreate. Empty the bucket or CloudFormation may fail to delete a non-empty S3 bucket, which is a separate and useful failure.

---

#### 10. What is `UpdateReplacePolicy`?

**Answer:** The same idea as deletion policy, but for when an **update** would replace the resource. Set it to `Retain` or `Snapshot` on databases so a bad property change does not delete the old database after creating a new one. People set `DeletionPolicy` and forget this path. Change sets still need a human who notices “replace”.

---

#### 11. Why would removing a resource from the template delete it in AWS?

**Answer:** The template is the desired state. If the resource is gone from the template, CloudFormation deletes it on the next update, unless a deletion policy says retain. Commenting out a table to “temporarily disable” it drops the table. Remove resources only when you mean to destroy them.

---

#### 12. What is drift?

**Answer:** Drift is a difference between the stack’s expected properties and the real resource, usually because someone changed the resource in the console or with the CLI. CloudFormation can detect drift. It does not always fix it until the next update, and an update might overwrite the console change. The rule is: if CloudFormation owns the resource, change the template. Console hotfixes become the next outage when a deploy reverts them.

---

## Structure and safety

#### 13. How do you split stacks?

**Answer:** One stack for the network (VPC, subnets) that changes rarely, one for data (RDS, buckets) with tight protections, and one or more for the application (Lambda, ECS, queues). Share values through outputs and **exports**, or through SSM parameters. A single giant stack works until one bad update threatens everything and the deploy takes forever. Split along change rate and blast radius.

---

#### 14. What is a nested stack versus a cross-stack reference?

**Answer:** A **nested stack** is a stack the parent creates from a template URL in S3. It deploys as a unit with the parent. A **cross-stack reference** is an exported output that another stack imports. Exports cannot be changed or deleted while another stack imports them, which surprises people during refactors. SSM parameters are often less brittle than exports for loose coupling.

---

#### 15. What is a stack set?

**Answer:** A way to deploy the same template across many accounts and regions from a central account, using AWS Organizations. Use it for guardrails, a baseline trail, or a standard bucket. Do not use a stack set for an application that each team deploys on its own cadence. Stack sets are an organization tool.

---

#### 16. How do IAM permissions work for a deploy?

**Answer:** The deployer needs `cloudformation:*` on the stack **and** permission to create the resources in the template, unless you use a **service role** the stack assumes. A service role is better for CI: the pipeline can only pass that role, and the role can create only what the app needs. `CAPABILITY_IAM` or `CAPABILITY_NAMED_IAM` must be acknowledged when the template creates IAM resources, so a template cannot quietly create an admin role without the deployer noticing.

---

#### 17. What is `CAPABILITY_IAM` asking you to confirm?

**Answer:** That the template contains IAM resources and you accept that those policies will be created. Named IAM requires `CAPABILITY_NAMED_IAM` when the template sets a role or user name. Review those resources in the diff. A template from the internet that creates `AdministratorAccess` is how accounts get owned. The checkbox is not a formality.

---

#### 18. How do you handle secrets in a template?

**Answer:** Do not commit passwords. Create a Secrets Manager secret outside the template or generate it with a resource that does not echo the value into outputs. Pass the secret **ARN** into ECS or Lambda. Avoid `NoEcho` parameters as the only protection. They are still in stack details in some views and in CI logs if you are careless. NoEcho is better than printing the password. It is not encryption.

---

## Day-to-day engineering

#### 19. What is the AWS SAM relationship to CloudFormation?

**Answer:** SAM is a transform on top of CloudFormation for serverless apps. A shorter `AWS::Serverless::Function` expands into a Lambda function, a role, and event sources. `sam deploy` is CloudFormation underneath. The stack, change sets, and rollback behavior are the same. If you can read a CloudFormation event log, you can debug a SAM deploy.

---

#### 20. What is CDK, in this context?

**Answer:** The Cloud Development Kit writes code (TypeScript, Python, and others) that **synthesizes** a CloudFormation template. You still get a stack and a change set. When a deploy fails, the error is a CloudFormation resource error. Learn enough template and enough events-tab reading that a CDK abstraction does not block you. The synthesized template in `cdk.out` is what actually deployed.

---

#### 21. How do you see what a deploy will change?

**Answer:** Create a **change set** and read every replacement. In CDK or SAM this is `diff` or a change-set step in CI. Reject a change set that replaces a database, a queue with messages, or a bucket, unless that was the plan and data is protected. Applying immediately from a laptop without a diff is how drift and deletions happen.

---

#### 22. A stack is stuck in `UPDATE_ROLLBACK_FAILED`. What is the situation?

**Answer:** An update failed, and the attempt to roll back also failed, often because a resource was changed outside CloudFormation or a permission is missing. The stack will not accept a normal update until you continue the rollback, sometimes skipping the resource that cannot roll back, and then repair it. Read the events from the bottom. Do not delete the stack as a first move if it holds data.

---

#### 23. Why did CloudFormation say the S3 bucket already exists?

**Answer:** Bucket names are global, and the template uses a name that another account or an old retained bucket already took. Or the stack is being recreated and `DeletionPolicy: Retain` left the bucket behind. Generate a unique name (`!Sub ${AWS::AccountId}-${AWS::Region}-logs`) or import the existing bucket into the stack. Do not keep retrying the same name.

---

#### 24. What is resource import?

**Answer:** A way to bring an existing resource under a stack without recreating it. You write the resource in the template and import it with the real id. Use it when a console-built database must become code. Practice in a dev account. A bad import can still cause a later update to replace the resource.

---

## Scenarios

#### 25. Dev and prod must differ only by size and domain name. How do you avoid two templates?

**Answer:** One template, parameters for environment, domain, and instance size, and conditions if a resource exists only in prod (a replica, a WAF). Deploy two stacks, `orders-dev` and `orders-prod`, with different parameter values. Never maintain copy-pasted templates that drift. Secrets and account ids come from the account you deploy into, not from a hardcoded prod id in the file.

---

#### 26. A developer hotfixed the Lambda environment variable in the console. The next deploy reverted it. Why?

**Answer:** The template is the source of truth. The hotfix was drift. Put the variable in the template or in SSM and redeploy. If console access is required for emergencies, the follow-up task is to make the template match before the next pipeline run. Tell the team this will keep happening until the template is updated.

---

#### 27. How would you protect an RDS instance declared in CloudFormation?

**Answer:** `DeletionPolicy` and `UpdateReplacePolicy` of `Snapshot` or `Retain`, RDS deletion protection enabled, a stack policy that denies replacement, and a change-set review in CI. The database password comes from Secrets Manager. The template does not set `DeletionPolicy: Delete` on a stateful resource because that is the default and it is wrong here.

---

#### 28. Two stacks both try to create a queue named `orders`. What happens?

**Answer:** The second fails because the name exists. Prefer names that include the stack or the environment, or omit the name and let CloudFormation generate one, then pass the ARN via an output. Generated names are safer. Fixed names are for resources other systems must find, and they must be unique on purpose.

---

#### 29. CI is allowed to deploy, but a developer should not be able to delete the prod stack. How do you split that?

**Answer:** The pipeline assumes a deploy role that can update the stack and pass the CloudFormation service role. Humans do not have `cloudformation:DeleteStack` on prod. The service role cannot be assumed from a laptop. Protect the pipeline role the same way you protect production credentials. A developer can still deploy through the pull request.

---

#### 30. What do you check when a teammate says “CloudFormation deleted our table”?

**Answer:** The stack events for the table’s logical id, whether the logical id was renamed, whether the resource left the template, and whether a replacement update ran. Then check deletion policy and whether a snapshot exists. CloudTrail shows who called `UpdateStack` or `DeleteStack`. The fix going forward is a change set, a stable logical id, and a retain or snapshot policy. The immediate fix is the snapshot or point-in-time restore, if one exists.

---
