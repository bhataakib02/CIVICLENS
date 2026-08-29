variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "certificate_arn" {
  type    = string
  default = ""
}
