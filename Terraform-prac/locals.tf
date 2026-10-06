locals {
  # One prefix for every resource name, so a console search for
  # "assettracker-dev" finds the whole stack.
  name = "${var.project_name}-${var.environment}"

  # Must match the "name" field inside imagedefinitions.json.
  # CodePipeline's ECS deploy action looks up the container by this name
  # and swaps only its image.
  container_name = "django"

  # First two availability zones in the chosen region.
  # RDS subnet groups require subnets in at least two zones even when
  # the database instance itself runs in a single zone.
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
