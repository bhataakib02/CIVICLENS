output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs"
}

output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "ALB security group ID"
}

output "ecs_security_group_id" {
  value       = aws_security_group.ecs.id
  description = "ECS tasks security group ID"
}

output "db_security_group_id" {
  value       = aws_security_group.db.id
  description = "Database security group ID"
}

output "redis_security_group_id" {
  value       = aws_security_group.redis.id
  description = "Redis security group ID"
}
