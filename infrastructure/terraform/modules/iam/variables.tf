variable "environment" {
  type        = string
  description = "Environment name"
}

variable "s3_bucket_arn" {
  type        = string
  description = "S3 bucket ARN for document access"
}
