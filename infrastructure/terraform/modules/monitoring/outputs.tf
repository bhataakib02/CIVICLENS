output "api_log_group_name" {
  value       = aws_cloudwatch_log_group.api.name
  description = "API CloudWatch log group name"
}

output "worker_log_group_name" {
  value       = aws_cloudwatch_log_group.worker.name
  description = "Worker CloudWatch log group name"
}
