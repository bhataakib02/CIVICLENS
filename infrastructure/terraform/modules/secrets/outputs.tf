output "secret_arn" {
  value       = aws_secretsmanager_secret.app_secrets.arn
  description = "AWS Secrets Manager secret ARN"
}
