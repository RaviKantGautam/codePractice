output "alb_dns_name" {
  description = "Open http:// this hostname after the first pipeline run is green. There is no HTTPS listener in this practice stack."
  value       = aws_lb.this.dns_name
}

output "github_connection_arn" {
  description = "Finish this connection in the AWS console before the pipeline can read GitHub. Status stays PENDING until you do."
  value       = aws_codestarconnections_connection.github.arn
}

output "github_connection_console_url" {
  description = "Console page where you authorize the GitHub connection."
  value       = "https://${var.aws_region}.console.aws.amazon.com/codesuite/settings/connections"
}

output "pipeline_name" {
  description = "CodePipeline name. After the GitHub connection is AVAILABLE, release a change to build and deploy."
  value       = aws_codepipeline.app.name
}

output "ecr_repository_url" {
  description = "Private registry that stores the Django image."
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "Cluster name, used with aws ecs execute-command."
  value       = aws_ecs_cluster.this.name
}

output "ecs_service_name" {
  description = "Service name. The pipeline updates this service."
  value       = aws_ecs_service.app.name
}

output "rds_endpoint" {
  description = "Private MySQL hostname. It resolves inside the VPC. It is not reachable from your laptop."
  value       = aws_db_instance.this.address
}

output "ecs_log_group" {
  description = "CloudWatch log group for the Django container."
  value       = aws_cloudwatch_log_group.ecs.name
}

output "codebuild_log_group" {
  description = "CloudWatch log group for image builds."
  value       = aws_cloudwatch_log_group.codebuild.name
}
