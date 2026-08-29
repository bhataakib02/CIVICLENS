resource "aws_kms_key" "secrets_key" {
  description             = "CivicLens Secrets Manager KMS Encryption Key (${var.environment})"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "civiclens-kms-secrets-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "secrets_key_alias" {
  name          = "alias/civiclens-secrets-${var.environment}"
  target_key_id = aws_kms_key.secrets_key.key_id
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "civiclens-secrets-${var.environment}"
  description             = "CivicLens application production secrets (JWT, DB credentials, API keys)"
  kms_key_id              = aws_kms_key.secrets_key.arn
  recovery_window_in_days = 30

  tags = {
    Name        = "civiclens-secrets-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "initial" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    JWT_SECRET_KEY        = random_password.jwt_secret.result
    DATABASE_URL          = "postgresql+psycopg://civiclens:${random_password.db_password.result}@db.${var.environment}.civiclens.internal:5432/civiclens"
    REDIS_URL             = "redis://cache.${var.environment}.civiclens.internal:6379/0"
    OTP_PROVIDER          = "aws_sns"
    SMS_PROVIDER          = "aws_sns"
    EMAIL_PROVIDER        = "aws_ses"
    PUSH_PROVIDER         = "fcm"
    OCR_PROVIDER          = "aws_textract"
    LLM_PROVIDER          = "aws_bedrock"
    SUBMISSION_PROVIDER   = "state_api"
  })

  lifecycle {
    ignore_changes = [
      secret_string,
    ]
  }
}

