output "ecs_execution_role_arn" {
  value       = aws_iam_role.ecs_execution.arn
  description = "ECS execution role ARN"
}

output "api_task_role_arn" {
  value       = aws_iam_role.api_task.arn
  description = "API task role ARN"
}

output "worker_task_role_arn" {
  value       = aws_iam_role.worker_task.arn
  description = "Worker task role ARN"
}
