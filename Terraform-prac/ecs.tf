# ECS on Fargate runs the Django container without an EC2 instance to patch.
#
# Django is a long-running web process. Fargate is a fit for that: you give
# it a container image, CPU, and memory, and AWS runs the task in the private
# subnets. Lambda would need an adapter around the request cycle and would
# fight Django's process model.
#
# Two IAM roles:
#   execution role - used by the ECS agent to pull the image, write logs,
#                    and read Secrets Manager before your process starts
#   task role      - used by the application itself. This app does not call
#                    AWS APIs. The only permissions here are for ECS Exec,
#                    so you can open a shell in the container while learning.

resource "aws_ecs_cluster" "this" {
  name = "${local.name}-cluster"

  # Container Insights adds a CloudWatch bill. Leave it off for practice.
  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = {
    Name = "${local.name}-cluster"
  }
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name}"
  retention_in_days = 7

  tags = {
    Name = "${local.name}-ecs"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = local.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    # CodeBuild's standard image is x86_64, so the image it pushes is x86_64.
    # The task architecture has to match the image.
    cpu_architecture = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = local.container_name
      image     = "${aws_ecr_repository.app.repository_url}:bootstrap"
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "DJANGO_SETTINGS_MODULE", value = "asset_tracker.settings.development" },
        # development settings serve /static/ when DEBUG is true.
        # The app has no WhiteNoise or S3 static storage configured.
        { name = "DEBUG", value = "True" }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.app.arn}:DATABASE_URL::"
        },
        {
          name      = "SECRET_KEY"
          valueFrom = "${aws_secretsmanager_secret.app.arn}:SECRET_KEY::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "django"
        }
      }
    }
  ])

  # The container definition references the secret ARN, not the version.
  # This dependency makes sure the JSON values exist before any task starts.
  depends_on = [aws_secretsmanager_secret_version.app]

  tags = {
    Name = local.name
  }
}

resource "aws_ecs_service" "app" {
  name                               = "${local.name}-service"
  cluster                            = aws_ecs_cluster.this.id
  task_definition                    = aws_ecs_task_definition.app.arn
  desired_count                      = var.desired_count
  launch_type                        = "FARGATE"
  platform_version                   = "LATEST"
  enable_execute_command             = true
  health_check_grace_period_seconds  = 180
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  wait_for_steady_state              = false

  # A bad image rolls back to the previous task definition instead of
  # staying in a crash loop as the "current" deployment.
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = local.container_name
    container_port   = var.container_port
  }

  # The listener must exist before ECS registers targets.
  depends_on = [aws_lb_listener.http]

  lifecycle {
    # The pipeline registers a new task definition on every deploy.
    # Without this, the next terraform apply would point the service
    # back at the :bootstrap image from this file.
    ignore_changes = [task_definition, desired_count]
  }

  tags = {
    Name = "${local.name}-service"
  }
}
