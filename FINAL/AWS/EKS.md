# Amazon EKS — Interview Questions (1–3 years)

Interview questions and answers for a backend and cloud software engineer with 1–3 years of experience.

---

## Fundamentals

#### 1. What is Amazon EKS?

**Answer:** EKS (Elastic Kubernetes Service) is managed Kubernetes. AWS runs the control plane (API server, etcd, scheduler, controller manager) across multiple Availability Zones. You run workloads on managed node groups, self-managed nodes, or Fargate, and you deploy with normal Kubernetes objects: Pods, Deployments, Services, and Ingress.

---

#### 2. What do you operate, and what does AWS operate?

**Answer:** AWS patches, scales, and replaces the control plane. You still choose Kubernetes versions and upgrade on a schedule, because old versions are removed. You operate node AMIs unless you use managed node groups and Fargate, and you operate everything inside the cluster: manifests, requests and limits, RBAC, and add-ons.

---

#### 3. How is a Pod different from a Deployment?

**Answer:** A Pod is one or more containers that share a network namespace and volumes, and it is mortal. A Deployment declares a desired number of identical Pods and rolls them out. You almost never create a bare Pod for an application. Use a Job or CronJob for finite work, and a StatefulSet when each replica needs a stable identity and its own disk.

---

#### 4. When would you pick EKS instead of ECS?

**Answer:** Pick EKS when the team already uses Kubernetes, needs portable manifests, or depends on Kubernetes extensions (custom controllers, service mesh, operators). Pick ECS when the workload is AWS-only and you want fewer concepts. The application code does not care; the operational model does.

---

#### 5. What are managed node groups, self-managed nodes, and Fargate on EKS?

**Answer:**

* **Managed node group:** an Auto Scaling group AWS helps you patch and upgrade. Default choice.
* **Self-managed nodes:** you own the AMI and the ASG. Used for unusual bootstrap or compliance images.
* **Fargate profile:** matching Pods run on Fargate with no node to manage. Good for bursty or isolated workloads. No DaemonSets and no GPU on those Pods.

---

#### 6. What is a Kubernetes Service, and what types will you see on EKS?

**Answer:** A Service gives Pods a stable virtual IP and DNS name. Types you use:

* **ClusterIP:** only inside the cluster. Default for service-to-service calls.
* **NodePort:** opens a port on every node. Rarely the thing you expose publicly.
* **LoadBalancer:** on EKS this provisions an **NLB** or, with the AWS Load Balancer Controller, you more often use an **Ingress** or a `TargetGroupBinding` for an ALB.

---

## Networking and identity

#### 7. How does a Pod get an IP on EKS?

**Answer:** The **VPC CNI** plugin assigns each Pod a real IP from the subnet of its node (secondary IPs on the node’s ENI). Pods are first-class VPC citizens. That is why subnet size matters: nodes plus every Pod consume VPC addresses. Security groups for Pods can attach a security group to a Pod, not only to the node.

---

#### 8. Why do teams run out of IPs in an EKS subnet?

**Answer:** Every Pod takes an IP, and each node also reserves extra IPs for future Pods based on instance type. A `/24` subnet (about 250 addresses) fills up quickly. Use larger subnets, more subnets across AZs, prefix delegation on the VPC CNI, or a design that does not put huge DaemonSets on every node without a plan.

---

#### 9. How should a Pod call AWS APIs without access keys in the image?

**Answer:** Use **IAM Roles for Service Accounts (IRSA)** or **EKS Pod Identity**. The Pod’s service account is annotated or associated with an IAM role. The AWS SDK inside the container picks up temporary credentials. Do not attach a broad node IAM role and let every Pod inherit it.

---

#### 10. What is the difference between Kubernetes RBAC and AWS IAM on EKS?

**Answer:** **RBAC** controls who can call the Kubernetes API (get Pods, update Deployments). **IAM** controls AWS APIs (read S3, describe instances). A developer can be allowed to deploy via RBAC and still have no S3 access. IRSA bridges them: a Kubernetes service account maps to an IAM role for the workload.

---

#### 11. How do you grant a human access to `kubectl` against a private EKS API?

**Answer:** The cluster API should sit in private subnets or be reachable through a bastion, VPN, or AWS network path. Access is granted with **EKS access entries** (or the older `aws-auth` ConfigMap) mapping an IAM principal to a Kubernetes group, plus RBAC that binds that group to a role. IAM authentication alone is not enough; the principal also needs an RBAC binding.

---

#### 12. What is an Ingress on EKS, and which controller creates an ALB?

**Answer:** An Ingress describes HTTP host and path routing to Services. The **AWS Load Balancer Controller** watches Ingress objects and creates an ALB, target groups, and listener rules. Without that controller, an Ingress does nothing. NLB-per-Service is the older `type: LoadBalancer` path and is a worse fit for many HTTP services behind one hostname.

---

## Workloads

#### 13. What are requests and limits, and what happens if you skip them?

**Answer:** A **request** is what the scheduler reserves. A **limit** is the ceiling. The container is OOM-killed if it exceeds its memory limit. CPU limits throttle rather than kill. With no requests, the scheduler overpacks nodes and a noisy neighbor starves the rest. Set requests from measured usage and limits with some headroom.

---

#### 14. What is a liveness probe versus a readiness probe?

**Answer:**

* **Readiness:** when it fails, the Pod is removed from Service endpoints. Use it so a starting or overloaded app does not receive traffic.
* **Liveness:** when it fails, Kubernetes **restarts** the container. Use it only for a deadlock you cannot recover without a restart. A slow dependency should fail readiness, not liveness, or you restart healthy processes in a loop.

---

#### 15. What is a DaemonSet, and why does it not run on Fargate?

**Answer:** A DaemonSet runs one Pod on every matching node (log agents, CNI helpers, security sensors). Fargate has no node you control, so there is nowhere to pin that Pod. On Fargate you run a sidecar in the application Pod instead, or you keep a small EC2 node group just for daemon agents.

---

#### 16. When do you use a StatefulSet instead of a Deployment?

**Answer:** When each replica needs a stable name, stable storage, or ordered startup. Examples: a self-hosted database, Kafka, or anything that cannot share one volume. Most HTTP APIs are Deployments with stateless Pods and an external database (RDS, DynamoDB). Do not put the only copy of customer data on a StatefulSet volume unless you also have a backup story.

---

#### 17. How do ConfigMaps and Secrets reach a container?

**Answer:** As environment variables or as mounted files. Secrets are base64-encoded in etcd, not encrypted by default from the app’s point of view. For real credentials, prefer **Secrets Store CSI** or an external secrets operator backed by AWS Secrets Manager, or IRSA so the app fetches the secret at runtime. Rotating a Kubernetes Secret does not always restart the Pod; plan a rollout.

---

#### 18. What is a Horizontal Pod Autoscaler?

**Answer:** An HPA changes the replica count of a Deployment from a metric, usually CPU utilization against the request, or a custom metric such as requests per second. It needs metrics (Metrics Server, or Prometheus/adapter for custom metrics) and resource requests, because CPU utilization is computed from the request. It does not add nodes. The **Cluster Autoscaler** or **Karpenter** adds nodes when Pods are Pending.

---

## Operations

#### 19. Pods are `Pending` with `FailedScheduling` and insufficient cpu. The AWS account is not out of quota. What is wrong?

**Answer:** The scheduler cannot fit the Pod on any node given requests, taints, and affinity. Either lower the request, scale the node group, or check that a taint (for example `NoSchedule` on a GPU pool) is not excluding every node. If the Cluster Autoscaler is installed, confirm it is allowed to grow the group and that the subnet still has IPs.

---

#### 20. A node disappeared and several Pods vanished with it. What should have limited the blast radius?

**Answer:** A **PodDisruptionBudget** does not save you from a sudden node death, but multiple replicas, topology spread across AZs, and a Deployment (not a single Pod) do. Readiness probes stop traffic to dead Pods once the node is gone. For planned drains (upgrade), a PDB plus `kubectl drain` keeps a minimum number available.

---

#### 21. How do you upgrade an EKS cluster safely?

**Answer:** Upgrade the control plane one minor version at a time, then node groups, then add-ons (VPC CNI, CoreDNS, kube-proxy, the load balancer controller). Drain nodes so Pods move before the old AMI is replaced. Check deprecated APIs in manifests before the jump. Do not skip versions. Test in a non-production cluster first.

---

#### 22. Where do control plane logs go, and are they on by default?

**Answer:** EKS can send API, audit, authenticator, controller manager, and scheduler logs to **CloudWatch Logs**. They are **off** until you enable them. Turn on at least the API and audit logs in production so you can see who deleted a Deployment. Application stdout is separate: the container runtime writes it, and a log agent or Fluent Bit DaemonSet ships it.

---

#### 23. What is a common cause of `ImagePullBackOff` on EKS?

**Answer:** The node or the Pod cannot pull from ECR. Private nodes need a NAT gateway or VPC endpoints for ECR and S3. The node role (or a pull secret) needs ECR read permissions. The image name, tag, and architecture (amd64 vs arm64) must exist. `ErrImagePull` events in `kubectl describe pod` usually include the registry error.

---

#### 24. How do you expose only an internal service to other VPCs and not the public internet?

**Answer:** Use a ClusterIP Service plus an **internal** ALB (Ingress annotation `scheme: internal`) in private subnets, or AWS PrivateLink. Security groups on the load balancer allow the other VPC’s CIDR or a peered security group. Do not create an internet-facing load balancer and then try to hide it with a security group you might forget.

---

## Scenarios

#### 25. After a deploy, the new Pods are Running but users still hit the old version. What do you check?

**Answer:** Readiness may be passing on old Pods that have not been terminated, or the Deployment did not actually roll (image tag `latest` did not change, so the spec was identical). Check `kubectl rollout status`, the Pod image **digest**, and Service endpoints. A horizontal pod autoscaler or a second Deployment behind the same Service can also keep old Pods in rotation.

---

#### 26. One bad Pod restart loop is taking down the node. What is happening?

**Answer:** A container that crash-loops without a memory limit can pressure the node, or a very low memory limit plus a tight liveness probe causes constant restarts and churn. Set memory limits, fix the probe so startup is covered by **startupProbe**, and use a PDB so voluntary disruption is controlled. Look at `OOMKilled` in the previous container state.

---

#### 27. You need a cron job every night that talks to RDS and exits. Which object do you use?

**Answer:** A **CronJob** that creates a Job, which creates a Pod. The Pod’s service account uses IRSA to reach any AWS API, and the RDS security group allows the Pod security group or the node subnet. Set `concurrencyPolicy: Forbid` if two runs must not overlap, and a `backoffLimit` so a failure does not retry forever. The container command should exit non-zero on failure so the Job is marked failed.

---

#### 28. How would you keep production manifests and application code in sync?

**Answer:** Store manifests or a Helm chart / Kustomize overlay in git. CI builds the image, pushes it to ECR, then updates the image tag in the deploy repo or renders the chart with that tag. A pipeline or GitOps controller (Argo CD, Flux) applies it to the cluster. Production should not be changed by a laptop `kubectl apply` except in an incident.

---

#### 29. A Service has endpoints, but calls from another Pod time out. DNS works. What is a likely network cause on EKS?

**Answer:** Security groups. With the VPC CNI, traffic is normal VPC traffic. The node or Pod security group must allow the Service port between the two workloads. Network policies (if you installed a policy engine) can also drop the packet. CoreDNS being healthy only proves the name resolved, not that the path is open.

---

#### 30. What would you monitor on an EKS-backed API in the first month?

**Answer:** ALB 5xx and latency, Deployment unavailable replicas, Pod restart count, CPU and memory against requests, node NotReady, pending Pods, and control-plane API errors. Alert on user symptoms and on “replicas available below desired”, not on every single Pod restart. Keep a dashboard for HPA desired versus current replicas so a stuck autoscaler is obvious.

---
