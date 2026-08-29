variable "environment" {
  type        = string
  description = "Environment name"
}

variable "alb_arn_suffix" {
  type        = string
  default     = ""
  description = "ALB ARN suffix for metric alarms"
}
