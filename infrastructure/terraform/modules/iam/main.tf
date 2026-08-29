# ECS Task Execution Role (Pulling image from ECR, writing logs to CloudWatch, fetching secrets)
resource "aws_iam_role" "ecs_execution" {
  name = "civiclens-ecs-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_standard" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# API Task Role (Least Privilege: S3 object read/write, Secrets Manager read)
resource "aws_iam_role" "api_task" {
  name = "civiclens-api-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "api_s3_access" {
  name        = "civiclens-api-s3-policy-${var.environment}"
  description = "Allows API task to read and write objects in document bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_s3" {
  role       = aws_iam_role.api_task.name
  policy_arn = aws_iam_policy.api_s3_access.arn
}

# Worker Task Role (Least Privilege: S3 object read/write)
resource "aws_iam_role" "worker_task" {
  name = "civiclens-worker-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_s3" {
  role       = aws_iam_role.worker_task.name
  policy_arn = aws_iam_policy.api_s3_access.arn
}
