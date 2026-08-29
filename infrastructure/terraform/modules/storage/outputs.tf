output "bucket_id" {
  value       = aws_s3_bucket.documents.id
  description = "S3 bucket ID"
}

output "bucket_arn" {
  value       = aws_s3_bucket.documents.arn
  description = "S3 bucket ARN"
}
