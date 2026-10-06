# RDS MySQL 8 is the managed database.
#
# The application already talks to MySQL 8. The local compose file runs
# mysql:8.0, requirements pin mysqlclient, and .env.example uses a mysql:// URL.
# A single-AZ db.t4g.micro instance matches that, at practice size.
#
# Aurora Serverless v2 is the usual production choice when you want the
# database to scale on its own. It costs more while idle, so it is the wrong
# default for a stack whose job is to teach the pipeline.

resource "aws_db_subnet_group" "this" {
  name        = "${local.name}-db"
  description = "Private subnets for Asset Tracker MySQL"
  subnet_ids  = aws_subnet.private[*].id

  tags = {
    Name = "${local.name}-db"
  }
}

resource "aws_db_instance" "this" {
  identifier     = "${local.name}-mysql"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = false
  apply_immediately       = true

  enabled_cloudwatch_logs_exports = ["error"]

  # AWS returns a full minor version such as 8.0.40 after create.
  # Ignoring it keeps later plans quiet when AWS ships a new minor.
  lifecycle {
    ignore_changes = [engine_version]
  }

  tags = {
    Name = "${local.name}-mysql"
  }
}
