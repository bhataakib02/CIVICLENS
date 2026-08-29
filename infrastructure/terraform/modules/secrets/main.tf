resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "civiclens-secrets-${var.environment}"
  description = "CivicLens application production secrets (JWT, DB credentials, API keys)"

  tags = {
    Name = "civiclens-secrets-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "initial" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    JWT_SECRET_KEY = "CHANGE_ME_IN_AWS_SECRETS_MANAGER_CONSOLE"
    DATABASE_URL   = "postgresql+psycopg://user:pass@host:5432/civiclens"
    REDIS_URL      = "redis://host:6379/0"
  })
}
