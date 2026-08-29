output "cluster_id" {
  value       = aws_ecs_cluster.main.id
  description = "ECS cluster ID"
}

output "api_service_name" {
  value       = aws_ecs_service.api.name
  description = "API ECS service name"
}

output "worker_service_name" {
  value       = aws_ecs_service.worker.name
  description = "Worker ECS service name"
}
