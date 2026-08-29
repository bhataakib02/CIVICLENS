resource "aws_db_subnet_group" "main" {
  name       = "civiclens-db-subnet-group-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "civiclens-db-subnet-group-${var.environment}"
  }
}

resource "aws_db_parameter_group" "pg16" {
  name   = "civiclens-pg16-params-${var.environment}"
  family = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }
}

resource "aws_db_instance" "main" {
  identifier             = "civiclens-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  max_allocated_storage  = 100
  storage_type           = "gp3"
  storage_encrypted      = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  parameter_group_name  = aws_db_parameter_group.pg16.name
  vpc_security_group_ids = [var.db_security_group_id]

  publicly_accessible = false
  skip_final_snapshot = var.environment == "dev" ? true : false
  final_snapshot_identifier = var.environment == "dev" ? null : "civiclens-db-final-snapshot-${var.environment}"

  backup_retention_period   = var.environment == "production" ? 30 : 7
  backup_window             = "03:00-04:00"
  maintenance_window        = "Mon:04:00-Mon:05:00"
  auto_minor_version_upgrade = true

  deletion_protection = var.environment == "production" ? true : false

  tags = {
    Name = "civiclens-db-${var.environment}"
  }
}
