variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "certificate_arn" {
  type        = string
  description = "Production ACM SSL Certificate ARN"
}
