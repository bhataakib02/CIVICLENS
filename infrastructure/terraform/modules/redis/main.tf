resource "aws_elasticache_subnet_group" "main" {
  name       = "civiclens-redis-subnet-group-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "civiclens-redis-${var.environment}"
  description          = "CivicLens Redis ElastiCache Replication Group"
  node_type            = var.node_type
  num_cache_clusters   = var.environment == "production" ? 2 : 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [var.redis_security_group_id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  automatic_failover_enabled = var.environment == "production" ? true : false

  tags = {
    Name = "civiclens-redis-${var.environment}"
  }
}
