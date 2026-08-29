resource "aws_ecs_cluster" "main" {
  name = "civiclens-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Task Definition: API
resource "aws_ecs_task_definition" "api" {
  family                   = "civiclens-api-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.api_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.api_image
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "STORAGE_PROVIDER", value = "s3" }
      ]
      secrets = [
        { name = "DATABASE_URL", valueFrom = "${var.secret_arn}:DATABASE_URL::" },
        { name = "REDIS_URL", valueFrom = "${var.secret_arn}:REDIS_URL::" },
        { name = "JWT_SECRET_KEY", valueFrom = "${var.secret_arn}:JWT_SECRET_KEY::" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_api
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}

# Task Definition: Worker
resource "aws_ecs_task_definition" "worker" {
  family                   = "civiclens-worker-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.worker_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.worker_image
      essential = true
      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "STORAGE_PROVIDER", value = "s3" }
      ]
      secrets = [
        { name = "DATABASE_URL", valueFrom = "${var.secret_arn}:DATABASE_URL::" },
        { name = "REDIS_URL", valueFrom = "${var.secret_arn}:REDIS_URL::" },
        { name = "JWT_SECRET_KEY", valueFrom = "${var.secret_arn}:JWT_SECRET_KEY::" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group_worker
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}

# ECS Service: API (Rolling Deployment with Health Check Grace Period)
resource "aws_ecs_service" "api" {
  name                               = "civiclens-api-service-${var.environment}"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.api.arn
  desired_count                      = var.api_desired_count
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds = 60

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
}

# ECS Service: Worker
resource "aws_ecs_service" "worker" {
  name            = "civiclens-worker-service-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }
}
