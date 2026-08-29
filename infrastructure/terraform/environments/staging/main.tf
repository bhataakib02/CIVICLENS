module "networking" {
  source      = "../../modules/networking"
  environment = var.environment
}

module "storage" {
  source      = "../../modules/storage"
  environment = var.environment
  bucket_name = "civiclens-documents-${var.environment}"
}

module "iam" {
  source        = "../../modules/iam"
  environment   = var.environment
  s3_bucket_arn = module.storage.bucket_arn
}

module "database" {
  source               = "../../modules/database"
  environment          = var.environment
  private_subnet_ids   = module.networking.private_subnet_ids
  db_security_group_id = module.networking.db_security_group_id
  db_password          = var.db_password
}

module "redis" {
  source                  = "../../modules/redis"
  environment             = var.environment
  private_subnet_ids      = module.networking.private_subnet_ids
  redis_security_group_id = module.networking.redis_security_group_id
}

module "load_balancer" {
  source                = "../../modules/load-balancer"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  certificate_arn       = var.certificate_arn
}

module "secrets" {
  source      = "../../modules/secrets"
  environment = var.environment
}

module "monitoring" {
  source         = "../../modules/monitoring"
  environment    = var.environment
  alb_arn_suffix = module.load_balancer.alb_arn_suffix
}

module "ecs" {
  source                  = "../../modules/ecs"
  environment             = var.environment
  private_subnet_ids      = module.networking.private_subnet_ids
  ecs_security_group_id   = module.networking.ecs_security_group_id
  target_group_arn        = module.load_balancer.target_group_arn
  ecs_execution_role_arn  = module.iam.ecs_execution_role_arn
  api_task_role_arn       = module.iam.api_task_role_arn
  worker_task_role_arn    = module.iam.worker_task_role_arn
  api_image               = "civiclens-api:staging"
  worker_image            = "civiclens-worker:staging"
  api_desired_count       = 2
  secret_arn              = module.secrets.secret_arn
  log_group_api           = module.monitoring.api_log_group_name
  log_group_worker        = module.monitoring.worker_log_group_name
}
