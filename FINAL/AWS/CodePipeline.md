# AWS CodePipeline — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS CodePipeline?

**Answer:** CodePipeline is a continuous delivery orchestrator. A **pipeline** has **stages**, and each stage has **actions**: take source, build, test, approve, deploy. It runs those actions when the source changes or when you start it. It does not compile code itself. CodeBuild does. It does not shift traffic itself. CodeDeploy, CloudFormation, or an ECS action does.

---

#### 2. What is a stage versus an action?

**Answer:** A **stage** is a phase (Source, Build, DeployStaging, Approve, DeployProd). Actions inside a stage can run in sequence or in parallel. The next stage starts only when the current stage succeeds, unless you configured otherwise. A failure stops the pipeline at that point. Stages are how you express “do not touch prod until staging and the approval are done”.

---

#### 3. What are typical action providers?

**Answer:**

* **Source:** CodeConnections (GitHub, GitLab, Bitbucket), CodeCommit, or S3.
* **Build:** CodeBuild.
* **Deploy:** CodeDeploy, ECS, S3, CloudFormation, or Elastic Beanstalk.
* **Invoke:** Lambda for a custom step.
* **Approval:** a manual gate.

The pipeline stores **artifacts** between actions in an S3 bucket. That bucket is how the image definition or the zip gets from build to deploy.

---

#### 4. How is CodePipeline different from GitHub Actions or GitLab CI?

**Answer:** Same job: run steps on each change. CodePipeline is native to AWS IAM, artifacts in S3, and deploy actions for ECS, CloudFormation, and CodeDeploy. GitHub Actions is native to GitHub and can also deploy to AWS by assuming a role. Pick one primary system so you do not have two places that both deploy prod. The interview point is the flow (source, build, deploy, approval), not loyalty to a product.

---

#### 5. What starts a pipeline execution?

**Answer:** A change in the source (a push to the branch you configured), a CloudWatch Events / EventBridge rule, a manual `StartPipelineExecution`, or a periodic trigger. Each execution has an id and a source revision. You can see which commit it ran. Do not share one pipeline across unrelated apps. One service, one pipeline, one history.

---

#### 6. What is an artifact?

**Answer:** The output of an action, stored in the pipeline’s artifact bucket, and named so a later action can take it as input. The build action outputs `BuildOutput` containing `imagedefinitions.json` or a zip. The deploy action consumes `BuildOutput`. If the name does not match, the deploy runs with the wrong bits or fails immediately. Artifacts are the contract between stages.

---

## Designing the flow

#### 7. What does a minimal backend pipeline look like?

**Answer:** Source on the main branch. Build in CodeBuild: test, build an image, push it with the commit SHA, write the definition file. Deploy to staging (ECS or CloudFormation). Optional manual approval. Deploy to production using the **same** artifact. Alarms exist so a bad prod deploy is visible. The pipeline role can deploy. Developers do not have a parallel path that copies files to prod from a laptop.

---

#### 8. Why should production deploy the same artifact that staging ran?

**Answer:** Rebuilding can pull newer dependencies and produce different bytes. Staging then proved nothing. Pass the artifact through. The production action should not run `docker build` again. If you must rebuild, pin every input so the digest matches, and compare digests before you trust it.

---

#### 9. What is a manual approval action for?

**Answer:** A human gate before production, or before a destructive step. The approver needs `codepipeline:PutApprovalResult`. Use it when the blast radius is high and the team is small enough to respond. Do not put an approval in the middle of a flow nobody watches, or releases sit for days. An approval is not a test. Staging should already have passed automated checks.

---

#### 10. How do you deploy to dev on every push and to prod only from a release?

**Answer:** Separate pipelines, or one pipeline whose prod stage is fed only from a release branch or a tag. A single pipeline on `main` that always deploys prod is fine if `main` is protected and staging must succeed first. Do not deploy prod from every pull request branch. A PR pipeline runs tests and stops.

---

#### 11. What are parallel actions good for?

**Answer:** Independent work in one stage: deploy two services that must move together, or run two test suites. They should not depend on each other’s artifacts from the same stage. If B needs A’s output, they are sequential. Parallel deploys to the same resource will race. Do not parallelize two actions that update one ECS service.

---

#### 12. How do environment variables and stage overrides work?

**Answer:** CodeBuild actions can set environment variables per action, so the same buildspec deploys different parameter values only if you are careful. Prefer separate deploy actions with explicit stack parameters (`Environment=prod`) over a buildspec that guesses the branch. Secrets should come from Secrets Manager, referenced so they are not stored in the pipeline definition in plain text.

---

## IAM, failure, and safety

#### 13. What IAM roles are involved?

**Answer:**

* The **pipeline service role** starts actions and reads and writes the artifact bucket.
* Each **action** may have its own role (CodeBuild’s role, CloudFormation’s role) that the pipeline is allowed to pass.
* A human approver uses their own IAM identity.

The pipeline role should not be `AdministratorAccess`. Scope it to the services this pipeline deploys. A pipeline that can pass a broad CloudFormation role is as powerful as that role.

---

#### 14. What happens when a stage fails?

**Answer:** The execution stops in the failed state. Later stages do not run. You fix the cause and retry the stage or the execution, depending on whether the source revision should stay the same. A new commit starts a new execution. Know whether your pipeline cancels the in-flight execution when a newer commit arrives. For production, cancelling a half-finished deploy automatically can be worse than letting it fail clearly. Choose the behavior on purpose.

---

#### 15. How do you roll back a production deploy that the pipeline marked successful?

**Answer:** The pipeline will not automatically redeploy the previous artifact just because users are unhappy, unless you wired alarms and CodeDeploy rollback. Re-run the previous successful execution’s deploy, or run a pipeline that takes the previous image digest. Keep enough artifact history to do that. “Rollback” is a new deploy of old bits, or a traffic shift back. Practice it.

---

#### 16. What is a CloudFormation action in a pipeline?

**Answer:** Create or update a stack from a template artifact, optionally with a change set that you approve. The action can wait for the stack to finish. If the stack rolls back, the action fails. This is how infrastructure and serverless apps move through the same pipeline as the image. Review the change set action before the execute action in production so a replacement is visible.

---

#### 17. What is an ECS deploy action versus CodeDeploy in the pipeline?

**Answer:** The standard ECS action updates the service to a new task definition from `imagedefinitions.json` and waits for stability. That is a rolling update. If you need blue/green, the action is CodeDeploy and the pipeline passes the revision CodeDeploy expects. Using the wrong action type is a common mismatch: the file the build wrote does not match what the deploy action reads, and the stage fails or deploys the wrong container name.

---

#### 18. How do notifications work?

**Answer:** EventBridge rules on pipeline execution state changes, or the notification settings that publish to SNS or a chat tool. Notify on failed stages. A green pipeline does not need a message every time if the team is busy. A failed production stage does. Include the pipeline name, stage, and execution id so the on-call can open the right run.

---

## Operations

#### 19. Why does the pipeline say it succeeded but the service is still on the old image?

**Answer:** The deploy action updated a different cluster, service, or task definition family. Or the imagedefinitions container name did not match the service, and the action no-op’d in a surprising way. Or a second pipeline deployed over the first. Check the task definition revision in ECS and the execution’s artifact. The pipeline status is “the action API returned success”, not “I curled the endpoint and saw the new build”.

---

#### 20. How do you prevent two people from deploying different commits at once?

**Answer:** One pipeline for that service, with executions configured so a new prod deploy does not overlap a running one (queue them, or lock the prod stage). IAM so humans cannot `UpdateService` around the pipeline. If two pipelines target the same ECS service, they will fight. There should be one writer.

---

#### 21. What belongs in source control versus in the pipeline console?

**Answer:** The pipeline definition should be code (CloudFormation, CDK, or Terraform), reviewed like the app. A pipeline that exists only as console clicks cannot be restored or reviewed. Connection secrets and approval emails are configuration. The stage structure belongs in git.

---

#### 22. How do you add a security scan without making the pipeline impossible to understand?

**Answer:** A CodeBuild action or a phase in the existing build that fails the build on critical findings, placed before deploy. Publish the report as an artifact or a log. Do not add five manual gates. One automated scan with a clear threshold beats a stage nobody knows how to satisfy. Dependency scanning and image scanning cover different things. Start with one.

---

#### 23. What is a pipeline variable or a namespace output?

**Answer:** Actions can publish output variables (an image digest, a stack name) that later actions read. Use them so you do not parse logs. They are not a secret store. If a later stage needs the digest, pass it as a variable instead of assuming a tag. Document the variable name. A typo shows up as an empty deploy.

---

#### 24. How do you test a pipeline change?

**Answer:** In a dev account or a dev pipeline that deploys to a non-production service. A change to the prod pipeline definition can stop releases. Use a change set or a terraform plan. Break the pipeline on purpose in dev (fail the test command) and confirm the prod stage does not run. Never “test” a new prod stage by pointing it at the real service the first time without a dry run.

---

## Scenarios

#### 25. Staging deployed, the approval sat for three days, and production then failed. What is stale?

**Answer:** The artifact might still be valid, but the environment moved: a secret rotated, a template parameter changed, or the staging stack was updated again by a later execution. Check whether a newer execution superseded this one. Approvals that linger need a timeout or a rule that you redeploy staging first. Prod failing after a long wait is often drift, not a bad test three days ago.

---

#### 26. A commit to `main` did not start the pipeline. What do you check?

**Answer:** The source action’s branch, the connection status to GitHub, the webhook or CodeConnections permissions, and whether a trigger filter excludes the path you changed. EventBridge rules if you start the pipeline that way. The repo’s branch protection is unrelated to detection. The connector must be healthy. A disconnected connection looks like a quiet repo.

---

#### 27. Developers want to hotfix prod from their laptops. How do you answer without blocking an incident?

**Answer:** The incident path is still the pipeline: a commit on a hotfix branch that runs the same build and deploy, maybe with the approval skipped by a break-glass role that is logged and alarmed. A laptop `aws ecs update-service` will be overwritten or will drift. If you truly must do it once, the follow-up is to make the pipeline match what you shipped before the next run reverts it. CloudTrail will show the laptop call. Use that as the audit, not as the design.

---

#### 28. How would you add a database migration to the pipeline safely?

**Answer:** A stage before the application deploy, with a role that can run migrations and nothing else, using a script that is backward compatible. The app deploy follows. The migration does not run inside every container startup. If the migration fails, the new app does not deploy. Destructive migrations are a later pipeline run after the new code is stable. The pipeline makes the order obvious. It does not make a bad `DROP COLUMN` safe.

---

#### 29. The artifact bucket is growing without limit. What do you change?

**Answer:** A lifecycle rule on the artifact bucket to expire old objects after a period you can still roll back (for example 30 days), and do not disable artifact encryption or public access while you do it. Builds that upload debug tarballs you do not need should stop. The bucket is not a data lake. It is a handoff between stages.

---

#### 30. What would you draw on a whiteboard for a production-ready pipeline?

**Answer:** Git push to a protected branch. Source action. CodeBuild runs tests and pushes an immutable image, output artifact is the image URI. Deploy to staging and wait until healthy. Automated smoke check. Manual approval if the service is customer-facing and the team wants it. Deploy the same artifact to production with CodeDeploy canary or an ECS rolling update, and a CloudWatch alarm that can roll back. IAM is scoped. The pipeline definition is in git. One sentence on failure: the stage stops, we fix forward or redeploy the previous artifact, and we do not rebuild from floating tags.

---
