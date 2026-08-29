variable "environment" {
  type        = string
  description = "Environment name"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs"
}

variable "ecs_security_group_id" {
  type        = string
  description = "ECS security group ID"
}

variable "target_group_arn" {
  type        = string
  description = "ALB target group ARN for API service"
}

variable "ecs_execution_role_arn" {
  type        = string
  description = "ECS execution role ARN"
}

variable "api_task_role_arn" {
  type        = string
  description = "API task role ARN"
}

variable "worker_task_role_arn" {
  type        = string
  description = "Worker task role ARN"
}

variable "api_image" {
  type        = string
  description = "API container ECR image URL"
}

variable "worker_image" {
  type        = string
  description = "Worker container ECR image URL"
}

variable "api_desired_count" {
  type        = number
  default     = 2
  description = "Desired API replica count"
}

variable "worker_desired_count" {
  type        = number
  default     = 1
  description = "Desired worker replica count"
}

variable "api_cpu" {
  type        = number
  default     = 512
  description = "API Fargate task CPU units"
}

variable "api_memory" {
  type        = number
  default     = 1024
  description = "API Fargate task memory (MB)"
}

variable "secret_arn" {
  type        = string
  description = "AWS Secrets Manager secret ARN"
}

variable "log_group_api" {
  type        = string
  description = "CloudWatch log group for API"
}

variable "log_group_worker" {
  type        = string
  description = "CloudWatch log group for Worker"
}

variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS region"
}
