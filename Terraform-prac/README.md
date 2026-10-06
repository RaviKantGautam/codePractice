# Asset Tracker on AWS

Practice infrastructure for [assettracker](https://github.com/RaviKantGautam/assettracker). Terraform creates the network, the database, the container service, and a pipeline that builds the Django app from GitHub and rolls it out.

This is a learning stack. It is sized for one person experimenting, then destroying it. It is not a production layout.

## What gets deployed

The pipeline deploys the Django app (assets, authentication, dashboard) against MySQL 8.

The Streamlit app under `streamlit-app/` stays out of this stack. It is a separate face-recognition UI, it redirects to `localhost`, and it is not the service the compose file runs as the web app.

## How a request moves

```text
browser
  |
  |  HTTP :80
  v
Application Load Balancer          public subnets
  |
  |  HTTP :8000
  v
ECS Fargate task (gunicorn)        private subnets
  |
  |  MySQL :3306
  v
RDS MySQL 8.0                      private subnets
```

A push to `master` takes a different path:

```text
GitHub master
  -> CodeConnections
  -> CodePipeline
       Source   zip of the repository
       Build    CodeBuild builds pipeline/Dockerfile, pushes to ECR
       Deploy   ECS starts a new task with that image
```

## Why this shape

| Piece | What it is | Why it is here |
| --- | --- | --- |
| VPC with public and private subnets | Your own network inside AWS | The load balancer needs a public address. Django and MySQL should not have one. |
| Two availability zones | Two data centers in the region | An RDS subnet group refuses to create with subnets in only one zone, even when the database instance runs in a single zone. |
| One NAT Gateway | Outbound internet for private subnets | Fargate has to pull the image, read secrets, and write logs. A private task has no public IP, so those calls leave through the NAT Gateway. |
| Application Load Balancer | HTTP entry point | It checks that gunicorn is answering, and it can later terminate HTTPS once you have a domain. |
| ECS on Fargate | Runs the container | Django is a long-running process. Fargate runs the container without an EC2 instance to patch. Lambda expects a short function call, which fights Django's process model. |
| ECR | Private Docker registry | CodeBuild pushes the image here. ECS pulls it from here. The image is not stored in git. |
| RDS MySQL 8, `db.t4g.micro`, one zone | Managed database | The app already uses MySQL 8: `mysqlclient`, a `mysql://` URL, and `mysql:8.0` in `local.yml`. |
| Secrets Manager | `DATABASE_URL` and `SECRET_KEY` | Those values are injected when the task starts. They are not baked into the image and they are not committed. |
| CloudWatch Logs | Task logs and build logs | `print` and gunicorn output go somewhere you can read after the container is gone. |
| S3 artifact bucket | Files passed between pipeline stages | CodePipeline stores the source zip and `imagedefinitions.json` here. The bucket is private and encrypted. |
| CodeConnections | GitHub authorization | AWS holds the GitHub app installation. You do not put a personal access token in Terraform. |
| CodePipeline V2, execution mode `QUEUED` | Orders the stages | A second push waits until the current run finishes, so two deploys do not migrate the same database at once. |
| CodeBuild | Docker build | The build runs in AWS, on x86_64, which matches the Fargate task. A build on an Apple Silicon laptop would produce an arm64 image the task cannot run. |
| ECS deploy action | Rolling container update | CodeBuild writes `imagedefinitions.json`. The deploy action registers a new task definition that keeps the same environment and secrets and swaps the image. |

### Choices that keep this a practice stack

- **HTTP only.** An HTTPS certificate from ACM needs a domain you control. The listener is port 80 so the stack can be applied without one. `drop_invalid_header_fields` is still on.
- **One NAT Gateway, one database zone, one task.** A second NAT and a Multi-AZ database are what you add when downtime has a cost.
- **Container Insights is off.** It is useful, and it adds a CloudWatch bill.
- **DEBUG is true.** `asset_tracker.settings.development` serves `/static/` only when `DEBUG` is true. The project has no WhiteNoise and no S3 static storage. With `DEBUG` false the HTML loads and the CSS does not.
- **RDS MySQL, not Aurora Serverless.** Aurora Serverless v2 scales on its own and is the usual production pick. It also costs money while idle. This app is already a MySQL 8 app, so a small RDS instance teaches the same connection path for less.
- **Rolling ECS deploy, not CodeDeploy blue/green.** Blue/green needs a second target group, a test listener, and an `appspec`. The rolling update is the smaller pipeline: start the new task, wait until it is healthy, stop the old one. `deployment_minimum_healthy_percent = 100` and `maximum_percent = 200` mean the new task is up before the old one stops. The deployment circuit breaker rolls back if the new task never becomes healthy.
- **CodeBuild is not inside the VPC.** The build only calls ECR and CloudWatch. Those are public AWS APIs. A CodeBuild project in a private subnet with no path out hangs on `DOWNLOAD_SOURCE` and looks stuck.

### What the pipeline does to the application repository

The repository's `docker/production/django/Dockerfile` still expects PostgreSQL, starts `jobportal.wsgi`, and listens on port 1998. The compose file that actually runs the app uses MySQL and port 8000.

`pipeline/Dockerfile` follows that working setup:

- Python 3.11, the same major version the repo Dockerfiles pin
- `requirements/production.txt`, which installs Django and `mysqlclient`
- `gunicorn` on port 8000
- `DJANGO_SETTINGS_MODULE=asset_tracker.settings.development`, which is what `manage.py` and `wsgi.py` already select
- `migrate` and `collectstatic` on startup

Terraform embeds that Dockerfile into the CodeBuild buildspec. You do not have to commit a Dockerfile to the GitHub repository for the pipeline to build.

`asset_tracker/settings/production.py` imports `common` instead of `.common`, so this stack does not use it. `development.py` writes a log file under `logs/`, and the image creates that directory. It also configures a Redis cache. Nothing in the Django apps reads that cache on a normal request, and ElastiCache is not part of this stack. A view that does touch the cache will fail until Redis exists.

Uploaded media stays on the container disk. A new task starts with an empty `media/` directory. Moving uploads to S3 means adding `django-storages` in the application, which this practice script does not change.

## What each file is for

| File | AWS resources |
| --- | --- |
| `versions.tf` | Terraform and provider versions. Default tags land on every resource. |
| `variables.tf` | Region, repository, task size, database name. |
| `locals.tf` | Name prefix and the container name shared by ECS and the pipeline. |
| `network.tf` | VPC, two public subnets, two private subnets, internet gateway, one NAT Gateway. |
| `security_groups.tf` | Who may talk to whom. See the next section. |
| `ecr.tf` | Private image repository. Keeps the last 10 images. `force_delete` lets `terraform destroy` remove it even when images are inside. |
| `rds.tf` | MySQL 8. Encrypted disk, no public access, skip the final snapshot so destroy does not ask you to name one. |
| `secrets.tf` | Generates the database password and Django secret key. Writes them as one JSON secret. |
| `alb.tf` | Public load balancer, target group, HTTP listener. Health check is `/admin/login/`. |
| `ecs.tf` | Cluster, task definition, service. |
| `iam.tf` | One role per service. No access keys. |
| `pipeline.tf` | Artifact bucket, GitHub connection, CodeBuild project, CodePipeline. |
| `pipeline/Dockerfile` | Image the build produces. |
| `pipeline/buildspec.yml` | Commands CodeBuild runs. |
| `outputs.tf` | URL, connection link, names you need for the AWS CLI. |

## Security groups

```text
internet --80--> alb --8000--> ecs task --3306--> rds
                     \--443, DNS--> NAT --> AWS APIs
```

- The load balancer accepts port 80 from the internet and may open port 8000 only toward the VPC.
- The task accepts port 8000 only from the load balancer security group.
- The task may open 443 to the internet (ECR, Secrets Manager, CloudWatch, all through the NAT Gateway), DNS to the VPC resolver, and MySQL to the VPC address range.
- The database accepts 3306 only from the task security group. Its outbound rule is a dead end. An empty outbound list is hard to express while Terraform is still replacing AWS's default "allow all outbound" rule, so the group allows outbound only to `127.0.0.1`.

DNS is its own rule on purpose. If the task can open 443 but cannot ask the VPC resolver on port 53, it cannot turn the RDS hostname into an IP, and the failure looks like a database bug.

## IAM, in one sentence each

- **ECS execution role** pulls the image, writes logs, and reads the one secret. The managed policy `AmazonECSTaskExecutionRolePolicy` covers pull and logs. A small extra policy covers the secret.
- **ECS task role** is what the Django process would use to call AWS. This app does not call AWS. The role only allows ECS Exec (`ssmmessages:*`), so you can open a shell in the container.
- **CodeBuild role** writes its own log stream, reads and writes the artifact bucket, logs in to ECR, and pushes to this one repository.
- **CodePipeline role** reads and writes the artifact bucket, starts this CodeBuild project, uses the GitHub connection for this one repository, and updates the ECS service. `iam:PassRole` is limited to the two task roles and only when the service being passed to is `ecs-tasks.amazonaws.com`.

`ecr:GetAuthorizationToken` and a few ECS describe calls are on `*`. Those APIs do not accept a single resource ARN. Everything that does accept an ARN is pinned to a resource in this stack.

## Approximate monthly cost if you leave it running

These are list-price ballparks for `ap-south-1`, so you can decide whether to apply. They are not a quote. The NAT Gateway is the line that surprises people.

| Piece | Ballpark |
| --- | --- |
| NAT Gateway, plus its public IPv4 address | about $45 |
| Application Load Balancer | about $20 |
| Fargate, 0.5 vCPU and 1 GB, always on | about $21 |
| RDS `db.t4g.micro`, 20 GB, one zone | about $15, less if the account still has RDS free tier |
| Secrets Manager, one secret | $0.40 |
| CodePipeline, one pipeline | $1 |
| CodeBuild | a few cents to a few dollars per build |
| ECR, S3, CloudWatch | usually a few dollars |

A stack left on all month lands around **$100**. CodeBuild and Fargate are not in the free tier. Run `terraform destroy` when you are done for the day.

## Before you apply

1. An AWS account, and credentials in the environment (`aws sts get-caller-identity` should succeed).
2. Terraform 1.5 or newer.
3. Permission to create the resources above, including IAM roles and a NAT Gateway.

```bash
cd Terraform-prac
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

`make init`, `make plan`, `make apply`, and `make destroy` wrap the same commands.

State is stored on this machine. `terraform.tfstate` contains the generated database password. It is gitignored. Do not copy it into chat or commit it.

Remote state (an S3 bucket and a DynamoDB lock table, or S3 with a lockfile) is the next step once more than one person applies this stack. A local state file is enough while you are the only person learning it.

## After apply: finish GitHub, then release

Terraform creates the GitHub connection in **PENDING**. There is no API that completes the GitHub consent screen. Until you finish it, the Source stage fails. That first failure is expected.

1. Open the `github_connection_console_url` output, or go to **Developer Tools → Settings → Connections** in the same region.
2. Select the pending connection → **Update pending connection**.
3. Install the AWS Connector GitHub app on `RaviKantGautam` and grant it `assettracker`.
4. Confirm the connection status is **Available**.
5. Open CodePipeline and choose **Release change** on `assettracker-dev-pipeline`.

The service is created before any image exists, so the first tasks fail with `CannotPullContainerError` for the `:bootstrap` tag. That stops once the pipeline's deploy stage succeeds. `wait_for_steady_state` is false so `terraform apply` does not sit there waiting for a healthy task that cannot exist yet.

Then open `http://<alb_dns_name>/admin/login/`.

The ECS service ignores later changes to `task_definition` and `desired_count`. That is deliberate: the pipeline owns the image, and a later `terraform apply` must not point the service back at `:bootstrap`. If you change environment variables or CPU in `ecs.tf`, apply still creates a new task definition revision, but the service keeps the revision the pipeline deployed. Force a new pipeline run after that apply, or update the service once to the new revision:

```bash
aws ecs update-service \
  --cluster assettracker-dev-cluster \
  --service assettracker-dev-service \
  --task-definition assettracker-dev \
  --region ap-south-1
```

## What to look at while it runs

Build logs:

```bash
aws logs tail /codebuild/assettracker-dev --follow --region ap-south-1
```

Application logs:

```bash
aws logs tail /ecs/assettracker-dev --follow --region ap-south-1
```

A shell in the container (requires the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)):

```bash
TASK_ID=$(aws ecs list-tasks \
  --cluster assettracker-dev-cluster \
  --service-name assettracker-dev-service \
  --query 'taskArns[0]' --output text --region ap-south-1)

aws ecs execute-command \
  --cluster assettracker-dev-cluster \
  --task "$TASK_ID" \
  --container django \
  --interactive \
  --command "/bin/sh" \
  --region ap-south-1
```

## Tear it down

```bash
terraform destroy
```

RDS is set to skip the final snapshot, the ECR repository force-deletes images, and the secret is deleted without the usual 7-day recovery wait (`recovery_window_in_days = 0`). Those settings are for a practice account. A database you care about would keep the snapshot and the recovery window.

## Where to go next

1. Add a domain and an ACM certificate, then redirect port 80 to 443.
2. Set `DEBUG` false and serve static files with WhiteNoise or with S3 and CloudFront.
3. Move `migrate` out of container startup and into a one-off task, then raise `desired_count`.
4. Swap the ECS deploy action for CodeDeploy blue/green when you want the old task to keep serving while the new one is tested.
5. Store Terraform state in S3.
