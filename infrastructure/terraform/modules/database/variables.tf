variable "environment" {
  type        = string
  description = "Environment name"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for DB subnet group"
}

variable "db_security_group_id" {
  type        = string
  description = "DB security group ID"
}

variable "db_name" {
  type        = string
  default     = "civiclens"
  description = "Database name"
}

variable "db_username" {
  type        = string
  default     = "civiclens_admin"
  description = "Master database username"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Master database password"
}

variable "allocated_storage" {
  type        = number
  default     = 20
  description = "Allocated storage in GB"
}

variable "instance_class" {
  type        = string
  default     = "db.t4g.micro"
  description = "RDS instance class"
}
