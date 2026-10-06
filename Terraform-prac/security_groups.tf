# Security groups are the firewalls between the three tiers.
#
#   internet  --80-->  load balancer  --8000-->  Django task  --3306-->  MySQL
#
# Each group allows only the next hop. Cross-references in both directions
# (task egress points at the database group, and the database ingress points
# at the task group) make Terraform report a cycle. The task is therefore
# allowed to open MySQL toward the VPC address range, and the database group
# is the rule that actually decides who may connect.

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb"
  description = "Public HTTP entry point for the Asset Tracker load balancer"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP from the internet. This practice stack has no domain, so there is no ACM certificate to attach yet."
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Forward requests into the VPC on the Django port"
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${local.name}-alb"
  }
}

resource "aws_security_group" "ecs" {
  name        = "${local.name}-ecs"
  description = "Django tasks. Inbound only from the load balancer."
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "App port from the load balancer"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "HTTPS to ECR, Secrets Manager, and CloudWatch through the NAT Gateway"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "DNS to the Amazon resolver inside the VPC. Without this, the task cannot resolve the RDS hostname."
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "DNS over TCP, used when a DNS answer is too large for UDP"
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "MySQL to RDS. The database security group still limits who can connect."
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${local.name}-ecs"
  }
}

resource "aws_security_group" "rds" {
  name        = "${local.name}-rds"
  description = "MySQL. Accepts traffic only from Django tasks."
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "MySQL from Django tasks"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  # Inline egress replaces the AWS default "allow all outbound" rule.
  # MySQL does not open connections of its own.
  egress {
    description = "No outbound connections"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["127.0.0.1/32"]
  }

  tags = {
    Name = "${local.name}-rds"
  }
}
