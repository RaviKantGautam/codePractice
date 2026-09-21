# AWS CodeBuild — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is AWS CodeBuild?

**Answer:** CodeBuild is a managed build service. It runs a build script in a container and then stops. You use it to compile, run tests, build a Docker image, and push artifacts. You do not keep a Jenkins agent pool patched for that job. A build project defines the environment, the source, and the spec. Each build gets a fresh container.

---

#### 2. Where does CodeBuild sit in a delivery pipeline?

**Answer:** After source, before deploy. CodePipeline (or GitHub Actions) checks out the commit and starts CodeBuild. The build produces an artifact or an image. A later stage deploys it. CodeBuild does not decide whether production should change. It reports success or failure and writes outputs.

---

#### 3. What is a buildspec?

**Answer:** A YAML file, usually `buildspec.yml` in the repo, that lists phases: `install`, `pre_build`, `build`, `post_build`. Each phase has commands. It also declares artifacts to pass on and, optionally, a cache. The build project can point at this file or store the spec in the project. Keep it in the repo so changes are reviewed with the code.

---

#### 4. What is the difference between a build project and a build?

**Answer:** The **project** is the configuration: source type, image, compute size, IAM role, timeout, and VPC. A **build** is one run of that project for one source version. Builds are immutable history. You change the project or the buildspec and the next build uses the new settings. You do not SSH into a build and “fix it”. You fix the spec and run again.

---

#### 5. What compute images can a build use?

**Answer:** AWS provides managed images (Amazon Linux, Ubuntu, Windows) with the AWS CLI and common runtimes. You can also use a **custom image** from ECR if you need a specific toolchain. A custom image makes builds faster to start when the tools are heavy, and it is another artifact you must patch. Start with a managed image unless the install phase dominates the build time.

---

#### 6. How does a build get credentials?

**Answer:** The build runs as an **IAM service role** on the project. The AWS CLI inside the build uses that role. Do not put long-lived access keys in the buildspec or in environment variables in the repo. Scope the role to what the build does: `ecr:PutImage` on one repository, `s3:PutObject` on the artifact bucket, and nothing like `iam:*`. The role is production-adjacent if it can push to the production image repository.

---

## Buildspec in practice

#### 7. What are the phases used for?

**Answer:**

* **install:** runtime versions and tools.
* **pre_build:** login to ECR, print the commit id, set variables.
* **build:** the real work (tests, `docker build`, `mvn package`).
* **post_build:** push the image, write a file the deploy stage needs, fail the build if a scan failed.

If a command returns non-zero, the phase fails and the build fails. `set -e` behavior is the default you should expect. Do not swallow test failures.

---

#### 8. How do you pass the image tag to a later deploy?

**Answer:** Write an `imagedefinitions.json` (for ECS) or set an output variable. The file contains the container name and the image URI with the tag or digest. CodePipeline passes that artifact to the ECS deploy action. The tag should be the commit SHA, not `latest`. The build that produced the image is the only place that knows the tag it pushed.

---

#### 9. What are artifacts?

**Answer:** Files the build uploads, usually to the pipeline’s artifact bucket, for the next stage. Declare them under `artifacts: files:`. Anything not declared is gone when the container exits. If the deploy needs a zip, a template, or a definitions file, it must be an artifact. Build logs are separate and stay in CloudWatch.

---

#### 10. What is the local cache, and what is a bad cache key?

**Answer:** CodeBuild can cache directories (dependencies, Docker layers) between builds to save time. Cache by something stable. A cache of `node_modules` that never invalidates will hide lockfile updates and produce “works on my machine” failures in reverse. Invalidate when the lockfile changes, and do not cache secrets. A cache is an optimization. The build must still succeed from an empty cache.

---

#### 11. How do tests run, and how do reports work?

**Answer:** Run the test command in the build phase. Export JUnit XML if you want CodeBuild **reports** in the console. Failing tests must fail the command. A report that says “failed” while the build succeeds is a misconfigured command. Unit tests belong here. A long end-to-end test against real AWS may belong in a later, separate project so the fast feedback loop stays fast.

---

#### 12. How do you build and push a Docker image?

**Answer:** In pre_build, `aws ecr get-login-password` and docker login. In build, `docker build -t repo:sha .`. In post_build, docker push. The role needs ECR push permissions. Prefer a multi-stage Dockerfile so the build tools are not in the runtime image. Enable image scanning on the repository and fail the build on your severity threshold if that is the policy. Do not tag only `latest`.

---

## Networking, secrets, and size

#### 13. When does a build need a VPC?

**Answer:** When it must reach a private resource: a database for integration tests, a private artifact store, or an internal API. Attach the project to private subnets and a security group. The build then needs a NAT gateway or VPC endpoints to reach public APIs such as ECR and CloudWatch, or those calls time out. Do not put the build in a public subnet with a wide-open security group to “make it work”.

---

#### 14. How should the build read secrets?

**Answer:** From **Secrets Manager** or **Parameter Store** at build time, using the build role, or from environment variables marked as secrets on the project (CodeBuild can pull them from Parameter Store or Secrets Manager). They show up masked in logs if you use the secrets configuration. Never echo them in the buildspec. A secret in a Docker layer is still in the image. Pass secrets at runtime to the app, not baked into the image during `docker build`, unless you have a specific reason and a process to rebuild on rotation.

---

#### 15. What is a privileged build?

**Answer:** Docker builds that need the Docker daemon require privileged mode on the CodeBuild environment (or a tool that builds without a daemon, such as Kaniko or Buildah, depending on the setup). Privileged mode weakens isolation. Only grant it to projects that build images. A test-only project should not be privileged. The build role plus privileged mode is a powerful combination. Keep the role narrow.

---

#### 16. How do you pick a compute size?

**Answer:** Start small. If the build spends its time compiling or running tests on CPU, a larger compute type shortens the wall clock and can cost less overall. If the build is waiting on downloads, a larger CPU will not help. Look at the phase times in the log. Timeouts should cover a slow dependency install without being so long that a hung build blocks the queue for an hour unnoticed.

---

#### 17. What are build logs, and who can read them?

**Answer:** Logs go to CloudWatch Logs under the project’s log group. They can contain command output, test names, and accidental secrets. Restrict who can read the log group. Set retention so old logs expire. When a build fails, the log is the first place you look, not the pipeline UI’s one-line status.

---

#### 18. How do you run the same project for a pull request and for main?

**Answer:** Use a source that supports webhooks (CodeConnections / GitHub) and a build that runs on pull requests without publishing to the production ECR repository. Separate projects, or a buildspec branch on the branch name, so PR builds cannot assume the production deploy role’s permissions. The safest split is a PR project whose role can only pull dependencies and run tests, and a main project whose role can push images.

---

## Failure and design

#### 19. The build works on your laptop and fails in CodeBuild. What is different?

**Answer:** A different OS or tool version, missing environment variables, no Docker daemon, a private dependency the laptop reaches through VPN, or a file that was never committed. Reproduce with the same managed image. Print versions in pre_build. Do not depend on a global tool you installed on the laptop and forgot to put in `install`. The build container starts empty except for the image.

---

#### 20. The build role can deploy to production, and the buildspec runs a script from the repo. What is the risk?

**Answer:** Anyone who can change the buildspec on a branch the project builds can run commands with that role. If pull requests trigger a privileged role, a malicious PR can push to production. Run untrusted code with a role that cannot deploy. Require a protected branch for the project that has the push-to-prod role. Review buildspec changes like application code.

---

#### 21. How do you speed up a build that downloads the internet every time?

**Answer:** Cache the package manager directory, use a lockfile so downloads are stable, and use a custom image that already contains the heavy toolchain. For Docker, enable layer caching carefully. Also fail fast: run unit tests before the image push so a test failure does not spend minutes on a push you will throw away. Parallelize independent test packages only if the suite is large enough to matter.

---

#### 22. What is a secondary source?

**Answer:** A build can pull more than one repository (the app and a shared deploy scripts repo). Declare them in the project and reference them in the buildspec. Use this sparingly. A submodule or a versioned artifact is often clearer. Secondary sources that float on `main` of another repo make the build unreproducible.

---

#### 23. How do you pin tool versions?

**Answer:** In the buildspec `runtime-versions`, and in the Dockerfile base image digest. Floating “latest” on a CLI or a base image means today’s build is not last month’s build. Pin and bump on purpose. A sudden failure after no code change is often an unpinned tool or base image moving.

---

#### 24. What should a build not do?

**Answer:** It should not apply database migrations to production, change DNS, or approve its own deploy. It should not leave behind long-lived infrastructure. It should not use the application’s production database as test fixture data. Build and unit test here. Deploy and migrate in a later stage with a different role and a human or a protected environment if the risk calls for it.

---

## Scenarios

#### 25. Image push fails with 403. Tests passed. What do you check?

**Answer:** The **build role’s** ECR permissions, the repository policy, and whether the login used the right region and account. Tests do not need ECR push, so they can pass while push is denied. Also check that the repository exists and tag immutability is not rejecting a tag you already pushed. The log line from the docker push is the actual error. Read it before you widen IAM to `ecr:*`.

---

#### 26. You need an integration test that hits a private RDS clone. How do you isolate it?

**Answer:** A separate CodeBuild project in the VPC, security group allowed on the clone only, role allowed to read one secret. It runs after unit tests, not on every keystroke. The clone is rebuilt by the pipeline or is a snapshot restore, not production. If the test writes data, it must not point at the real endpoint. A wrong secret in the build project is how tests corrupt prod. Name the secret and the endpoint so that mistake is obvious.

---

#### 27. Two branches build at once and both push the tag `latest`. What breaks?

**Answer:** You cannot tell which commit `latest` is, and the second push wins. Tag with the commit SHA. If two builds must not push the same immutable tag, the git SHA already makes that unique. Disable concurrent pushes to a moving tag. Production deploys should use the SHA artifact from the pipeline execution, not whatever `latest` is at deploy time.

---

#### 28. How would you structure a buildspec for a Python service?

**Answer:** Install the Python version. Pre_build creates a virtualenv and installs from a lockfile. Build runs `pytest` and then builds the image with the same lockfile. Post_build pushes the image only if tests passed (it will not run if build failed, so keep tests in `build` before the push, or put the push in post_build after a successful build phase). Artifacts include `imagedefinitions.json`. Cache the pip directory. The role can push to the dev ECR repository. Nothing in the spec echoes the database URL.

---

#### 29. CodeBuild is slow to start and the compile is only 20 seconds. What dominates?

**Answer:** Provisioning the container and installing dependencies. A custom image with dependencies, a cache, and a smaller install phase help more than a bigger CPU. Also check whether you are using a VPC without endpoints, so every start waits on a cold NAT path to download packages. Look at phase timestamps in the log before you buy a larger compute type.

---

#### 30. What is a reasonable CodeBuild setup for a small backend team?

**Answer:** One project for pull requests that runs tests and cannot push to production. One project on the protected branch that builds, scans, and pushes an image tagged with the git SHA, and emits the definition file for CodePipeline. The role is service-specific. Logs expire. The buildspec is in the repo. A failed test fails the build. Deploys happen in the next pipeline stage, not in a shell script at the bottom of the buildspec that SSHes to a server.

---
