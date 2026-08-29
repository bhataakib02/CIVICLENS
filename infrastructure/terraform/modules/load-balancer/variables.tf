variable "environment" {
  type        = string
  description = "Environment name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs"
}

variable "alb_security_group_id" {
  type        = string
  description = "ALB security group ID"
}

variable "certificate_arn" {
  type        = string
  default     = ""
  description = "ACM Certificate ARN for HTTPS"
}
