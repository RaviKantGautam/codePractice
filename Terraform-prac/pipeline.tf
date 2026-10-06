# CI/CD pipeline
#
#   GitHub (master)
#        |
#        |  CodeConnections  (you finish the GitHub login in the console)
#        v
#   Source stage          zip of the repository
#        |
#        v
#   Build stage           CodeBuild builds pipeline/Dockerfile, pushes to ECR
#        |
#        v
#   Deploy stage          ECS rolling update, using imagedefinitions.json
#
# V2 + QUEUED means a second push waits until the current run finishes.
# That matters because each run migrates the same database. Two deploys
# at once would race.
#
# CodeBuild stays outside the VPC. It only talks to ECR and CloudWatch,
# which are public AWS APIs. A CodeBuild project placed in a private subnet
# with no NAT path hangs forever while downloading source.

resource "aws_s3_bucket" "artifacts" {
  bucket        = "${local.name}-pipeline-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Name = "${local.name}-pipeline-artifacts"
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-old-artifacts"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

data "aws_iam_policy_document" "artifacts_bucket" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.artifacts.arn,
      "${aws_s3_bucket.artifacts.arn}/*"
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  policy = data.aws_iam_policy_document.artifacts_bucket.json
}

resource "aws_cloudwatch_log_group" "codebuild" {
  name              = "/codebuild/${local.name}"
  retention_in_days = 7

  tags = {
    Name = "${local.name}-codebuild"
  }
}

# The connection is created in PENDING state. Terraform cannot click the
# GitHub consent screen for you. After apply, open the console link from
# the output and finish the handshake. Until the status is AVAILABLE, the
# Source stage fails.
resource "aws_codestarconnections_connection" "github" {
  name          = "${local.name}-github"
  provider_type = "GitHub"

  tags = {
    Name = "${local.name}-github"
  }
}

resource "aws_codebuild_project" "app" {
  name           = "${local.name}-build"
  description    = "Build the Asset Tracker image and push it to ECR"
  service_role   = aws_iam_role.codebuild.arn
  build_timeout  = 30
  queued_timeout = 30

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_MEDIUM"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
    privileged_mode             = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "ECR_REGISTRY"
      value = split("/", aws_ecr_repository.app.repository_url)[0]
    }

    environment_variable {
      name  = "ECR_REPOSITORY_URI"
      value = aws_ecr_repository.app.repository_url
    }

    environment_variable {
      name  = "CONTAINER_NAME"
      value = local.container_name
    }
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.codebuild.name
      status     = "ENABLED"
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = local.buildspec
  }

  tags = {
    Name = "${local.name}-build"
  }
}

locals {
  # pipeline/buildspec.yml is the readable script. The token is replaced
  # with the base64 of pipeline/Dockerfile so CodeBuild can recreate that
  # file inside the GitHub checkout. The application repository does not
  # have to contain a deploy Dockerfile.
  buildspec = replace(
    file("${path.module}/pipeline/buildspec.yml"),
    "__DOCKERFILE_B64__",
    base64encode(file("${path.module}/pipeline/Dockerfile"))
  )
}

resource "aws_codepipeline" "app" {
  name           = "${local.name}-pipeline"
  role_arn       = aws_iam_role.codepipeline.arn
  pipeline_type  = "V2"
  execution_mode = "QUEUED"

  artifact_store {
    type     = "S3"
    location = aws_s3_bucket.artifacts.bucket
  }

  trigger {
    provider_type = "CodeStarSourceConnection"

    git_configuration {
      source_action_name = "Source"

      push {
        branches {
          includes = [var.github_branch]
        }
      }
    }
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["SourceOutput"]
      namespace        = "SourceVariables"

      configuration = {
        ConnectionArn        = aws_codestarconnections_connection.github.arn
        FullRepositoryId     = var.github_repository
        BranchName           = var.github_branch
        OutputArtifactFormat = "CODE_ZIP"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["SourceOutput"]
      output_artifacts = ["BuildOutput"]
      namespace        = "BuildVariables"

      configuration = {
        ProjectName = aws_codebuild_project.app.name
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      version         = "1"
      input_artifacts = ["BuildOutput"]

      configuration = {
        ClusterName = aws_ecs_cluster.this.name
        ServiceName = aws_ecs_service.app.name
        FileName    = "imagedefinitions.json"
      }
    }
  }

  tags = {
    Name = "${local.name}-pipeline"
  }
}
