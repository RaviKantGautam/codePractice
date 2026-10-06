# Secrets Manager stores the two values Django must not have in the image
# or in git: the database URL and SECRET_KEY.
#
# ECS injects them as environment variables when the task starts. The image
# stays the same across environments. Only the secret changes.
#
# The password uses letters and digits so it can sit inside a mysql:// URL
# without extra encoding. Terraform state stores this password too, which is
# why terraform.tfstate is gitignored.

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "random_password" "django_secret" {
  length  = 50
  special = false
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${local.name}/django"
  description             = "DATABASE_URL and SECRET_KEY for the Asset Tracker Django task"
  recovery_window_in_days = 0

  tags = {
    Name = "${local.name}-django"
  }
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id

  secret_string = jsonencode({
    DATABASE_URL = "mysql://${var.db_username}:${random_password.db.result}@${aws_db_instance.this.address}:3306/${var.db_name}"
    SECRET_KEY   = random_password.django_secret.result
  })
}
