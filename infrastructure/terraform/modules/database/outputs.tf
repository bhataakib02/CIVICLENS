output "endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "Database connection endpoint"
}

output "address" {
  value       = aws_db_instance.main.address
  description = "Database address"
}

output "port" {
  value       = aws_db_instance.main.port
  description = "Database port"
}

output "db_name" {
  value       = aws_db_instance.main.db_name
  description = "Database name"
}

output "db_instance_id" {
  value       = aws_db_instance.main.id
  description = "RDS instance ID"
}
