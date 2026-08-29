output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "ALB DNS name"
}

output "alb_arn" {
  value       = aws_lb.main.arn
  description = "ALB ARN"
}

output "alb_arn_suffix" {
  value       = aws_lb.main.arn_suffix
  description = "ALB ARN suffix"
}

output "target_group_arn" {
  value       = aws_lb_target_group.api.arn
  description = "API target group ARN"
}
