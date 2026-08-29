provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CivicLens"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
