# CivicLens Terraform IaC Architecture

This directory defines all production and staging AWS infrastructure for CivicLens using modular Terraform files.

## Module Structure

```text
infrastructure/terraform/
├── versions.tf                   # Provider & Terraform constraints
├── providers.tf                  # AWS provider and global tags
├── modules/
│   ├── networking/               # VPC, public/private subnets, NAT, SGs
│   ├── database/                 # RDS PostgreSQL 16 + pgvector (Private)
│   ├── redis/                    # ElastiCache Redis Replication Group (Private)
│   ├── storage/                  # S3 Private Bucket + Encryption + Public Access Block
│   ├── ecs/                      # Fargate Cluster + API & Worker Task/Service Definitions
│   ├── load-balancer/            # ALB + Target Groups + ACM SSL Listener
│   ├── iam/                      # Least-Privilege IAM Roles (ECS Execution, API, Worker)
│   ├── secrets/                  # AWS Secrets Manager
│   └── monitoring/               # CloudWatch Log Groups & Alarms
└── environments/
    ├── dev/                      # Local/Scratch environment configuration
    ├── staging/                  # Staging environment topology
    └── production/               # Production high-availability topology
```

## Running Terraform Locally (Validation & Planning)

```bash
# Navigate to desired environment
cd infrastructure/terraform/environments/staging

# Initialize without remote backend for local linting/validation
terraform init -backend=false

# Validate syntax & semantics
terraform validate

# Plan against target credentials (when AWS credentials configured)
terraform plan
```
