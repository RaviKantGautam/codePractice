# Amazon ECR — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon ECR?

**Answer:** ECR (Elastic Container Registry) is a managed Docker (OCI) image registry. You push images from CI and pull them from ECS, EKS, Lambda, or any client that speaks the Docker registry API. Images are stored in repositories inside a private registry in your account, or in the public registry (`public.ecr.aws`).

---

#### 2. What is a registry, a repository, and an image tag?

**Answer:**

* **Registry:** the account-level endpoint, such as `123456789012.dkr.ecr.ap-south-1.amazonaws.com`.
* **Repository:** a named collection of images, such as `payments-api`.
* **Tag:** a pointer to an image manifest, such as `git-sha-a1b2c3`. The real identity of the image is its **digest** (`sha256:...`).

Several tags can point at the same digest. Moving a tag does not change a digest.

---

#### 3. How does CI authenticate to ECR to push an image?

**Answer:** The build role calls `aws ecr get-login-password`, and that token is passed to `docker login` (or the equivalent in buildah, kaniko, or BuildKit). The token is short-lived. The role needs `ecr:GetAuthorizationToken` plus push actions (`BatchCheckLayerAvailability`, `InitiateLayerUpload`, `UploadLayerPart`, `CompleteLayerUpload`, `PutImage`) on the repository. Do not use long-lived access keys on the build machine.

---

#### 4. How does an ECS task or an EKS node pull a private image?

**Answer:** On ECS, the **task execution role** needs ECR pull permissions, and the task or node network must reach the registry. On EKS, the **node IAM role** usually pulls the image, unless the Pod uses an image pull secret. Private subnets need a NAT gateway or VPC endpoints for ECR API, ECR Docker, and S3 (layers are downloaded from S3).

---

#### 5. Why is `latest` a bad tag for production deploys?

**Answer:** `latest` is mutable. A deploy that “sets the image to latest” may not change the task definition or the Pod spec, so nothing rolls out. If it does move, you cannot tell from the manifest which git commit is running, and a rollback has no stable name to return to. Tag images with the git SHA or a release version, and prefer pinning the digest in the deploy spec.

---

#### 6. What is the difference between a private repository and a public ECR repository?

**Answer:** Private repositories stay in your account and require IAM to pull. Public repositories are world-readable and are meant for open-source images you publish. Do not put application images that contain internal code or config in the public registry. Pull-through cache (below) is how you consume Docker Hub or other upstream registries through ECR.

---

## Security and lifecycle

#### 7. What is image scanning in ECR, and when does it run?

**Answer:** ECR can scan images for known OS and language package vulnerabilities. **Basic scanning** uses a Clair-based database on push. **Enhanced scanning** uses Amazon Inspector, can scan continuously as new CVEs appear, and covers more package ecosystems. CI should fail or gate a deploy on a severity threshold you choose, not on “any finding”, because base images often have low or unfixed issues.

---

#### 8. What does a lifecycle policy do?

**Answer:** It expires images by rule so you do not pay for every build forever. Typical rules: keep the last 30 tagged release images, delete untagged images after a few days, and never expire tags that match `prod-*` or the current release. Untagged images appear when a tag is moved or a push fails after layers upload. Lifecycle policies are the cleanup tool, not a manual console purge.

---

#### 9. What is tag immutability, and when do you turn it on?

**Answer:** With immutability enabled, a tag cannot be overwritten. Pushing the same tag again fails. Turn it on for production repositories so CI cannot silently replace `1.4.2`. You can still add a new tag to an existing digest. Mutable tags are sometimes left on a sandbox repository where developers overwrite `dev`.

---

#### 10. How do you stop every principal in the account from pulling every repository?

**Answer:** Do not rely on a wide `ecr:*` policy. Grant `ecr:BatchGetImage` and related pull actions on specific repository ARNs to the execution role or node role that needs them. Optional repository policies can allow a **different account** to pull (cross-account), which identity policies in the other account cannot express alone.

---

#### 11. What is ECR replication, and why would you use it?

**Answer:** Replication copies images from a source registry to other regions or accounts. Use it so a disaster-recovery region can pull without depending on the original region, or so a shared-services account publishes images that application accounts replicate in. Replication follows the digest. You still deploy by pointing task definitions at the destination registry.

---

#### 12. How do you let ECS in account B pull an image that CI pushed in account A?

**Answer:** In account A, add a repository policy that allows account B’s task execution role (or the account root, narrowed by conditions) to pull. In account B, the execution role’s identity policy must also allow pull on that repository ARN. The image URI in the task definition uses account A’s registry hostname. Both sides are required.

---

## Images and operations

#### 13. What is a multi-architecture image, and why does it matter on AWS?

**Answer:** A manifest list (index) points at per-architecture manifests, usually `amd64` and `arm64`. Graviton (arm64) nodes pull the arm image; x86 nodes pull amd64. If CI only builds amd64 and you schedule onto Graviton, the pull or the start fails. Build both, or pin the cluster to one architecture.

---

#### 14. Why are image layers relevant to build time and pull time?

**Answer:** Unchanged layers are cached in CI and on the node. Put dependencies (package installs) in earlier layers and application code in the last layer so a one-line change does not rebuild the world. Large layers slow every scale-out because every new task pulls them. Slim base images and a `.dockerignore` that excludes `.git` and tests are the usual fixes.

---

#### 15. What is a pull-through cache?

**Answer:** An ECR pull-through cache rule mirrors an upstream registry (Docker Hub, public ECR, and others) into a private repository prefix on first pull. Nodes pull from ECR inside AWS instead of depending on Docker Hub rate limits and the public internet for every start. You still need a network path from the node to ECR.

---

#### 16. A push succeeds, but the cluster runs an old build. What do you verify?

**Answer:**

1. The tag in ECR actually moved (check the digest and push time).
2. The task definition or Deployment was updated to that tag or digest and a new revision was deployed.
3. Old tasks or Pods are gone, not still serving behind the load balancer.
4. You are looking at the same region and account the cluster pulls from.

A successful push does not deploy anything by itself.

---

#### 17. How large can images get, and what practical limit matters more?

**Answer:** ECR supports large images (well into the gigabytes), but the practical limit is pull time and disk on the node or Fargate ephemeral storage. A 2 GB image makes every scale-out and every cold start slower and more likely to hit timeouts. Multi-stage builds and distroless or Alpine-class bases, when compatible, keep images smaller. Lambda container images have a **10 GB** image limit, which is a hard cap for that consumer.

---

#### 18. What is the difference between deleting a tag and deleting an image?

**Answer:** Deleting a tag removes one pointer. If another tag still references the digest, the layers stay. Deleting the image (the digest) removes it once no tag points at it, subject to replication and to tasks that already pulled it. Running containers keep the local copy until the task stops. A lifecycle policy is the systematic version of this cleanup.

---

#### 19. How do you see who pushed or deleted an image?

**Answer:** **CloudTrail** records ECR control-plane calls such as `PutImage`, `BatchDeleteImage`, and `SetRepositoryPolicy`. That answers “who changed the registry”. It is not an application log. Enable a trail that includes management events in the region of the registry.

---

#### 20. What breaks if the base image in a Dockerfile uses a floating tag?

**Answer:** Today’s build and next month’s build of the same Dockerfile can contain different OS packages and different CVEs, even if your application code did not change. Pin the base image by digest in CI, and bump it on purpose when you want patches. Scanning then compares known builds instead of a moving target.

---

## Scenarios

#### 21. Production pulls fail with `403 Forbidden` after you tightened IAM. The image exists. What permission is usually missing?

**Answer:** Pull is several APIs, not one. The execution role or node role needs `ecr:GetAuthorizationToken` on `*` (the token API is not resource-scoped) and `BatchGetImage`, `GetDownloadUrlForLayer`, and `BatchCheckLayerAvailability` on the repository. A repository policy that `Deny`s the principal, or a VPC endpoint policy, can also produce a 403 even when the identity policy looks correct.

---

#### 22. Scans report critical CVEs in the base image the week after a clean release. The code did not change. What should the pipeline do?

**Answer:** Enhanced scanning re-evaluates images as the CVE database updates. The pipeline or a scheduled job should re-open a ticket or block the **next** promote when a new critical finding appears on the running digest. You rebuild on a patched base and roll forward. Deleting the running image in ECR does not patch the containers that already pulled it.

---

#### 23. Developers need to pull the service image to reproduce a bug locally. How do you allow that without giving them push rights?

**Answer:** Give the developer role pull actions only on that repository, plus `GetAuthorizationToken`. Keep `PutImage` and upload actions on the CI role. A repository policy is unnecessary for same-account human pulls if the identity policy is correct. Local Docker still needs `aws ecr get-login-password` against the right region.

---

#### 24. You must promote the exact image that passed staging into production in another region. How do you avoid rebuilding?

**Answer:** Do not rebuild and retag with a new digest. Either replicate the repository to the production region, or have the pipeline `docker pull` by digest and push that same digest to the production registry. Deploy production by digest so the bits match what staging ran. A rebuild can pick up a newer base layer and invalidate the test.

---

#### 25. A lifecycle policy deleted the image production is running. What is the impact, and how do you prevent it?

**Answer:** Running tasks keep their local layers, but the next scale-out or node replacement cannot pull, so new tasks fail with `ImagePullBackOff` or `CannotPullContainerError`. Exclude the tags or digests that are currently deployed, keep a minimum number of release tags, and do not run a rule that expires “everything older than 7 days” in a repository that production uses. Restore by re-pushing the digest from another region if replication kept it.

---

#### 26. How do you stop a compromised CI job from overwriting production tags?

**Answer:** Enable tag immutability, split CI credentials so only the promote role can push to the prod repository, and require a human or a protected branch for that role. Store prod images in a separate repository or account. CloudTrail alarms on `PutImage` to that repository. Immutability means the attacker must push a new tag, which your deploy pin will not follow until someone updates it.

---

#### 27. ECS says it cannot pull the image, but your laptop can. What is different?

**Answer:** Your laptop uses your IAM user and the public internet. The task uses the **execution role**, often from a **private subnet** with no NAT and no ECR endpoints. Check the task’s region, the image URI (account and region), the execution role, and the subnet route. A typo in the account id inside the URI fails the same way.

---

#### 28. How should a Dockerfile and ECR work for a Lambda container image?

**Answer:** The image must implement the Lambda Runtime API. The easiest path is a base image from the AWS runtime images (or a custom runtime). Push it to ECR in the same account and region. The function configuration points at the image URI. The Lambda execution role needs ECR pull permissions if the image is private. Cold starts include pulling a new image to an execution environment, so keep the image small.

---

#### 29. What is a reasonable retention setup for a busy microservice repository?

**Answer:** Immutable tags. A lifecycle rule that keeps the last 50 images tagged with the release prefix, deletes untagged images after 1 day, and does not touch tags starting with `release-`. Enhanced scanning on push. CI pushes only the git SHA. A separate promote step retags or copies the digest to `release-<version>` after tests pass. Production task definitions use the release tag’s digest.

---

#### 30. What would you alarm on for ECR in a production pipeline?

**Answer:** Pipeline push failures, scan findings at or above your severity bar on the image you are about to deploy, and cluster events for image pull failures. Optionally a CloudTrail alarm on unexpected `PutImage` or `BatchDeleteImage` in the production repository. ECR storage cost is worth a budget alert if lifecycle policies are missing and every build is retained forever.

---
