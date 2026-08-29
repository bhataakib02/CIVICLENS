# Networking

Status: v1.0 draft
Related: aws-architecture.md, security/security-architecture.md

## 1. VPC Layout

A dedicated VPC per environment, with public subnets (ALB, NAT gateways
only) and private subnets (ECS tasks, RDS, ElastiCache) across multiple
Availability Zones for the Multi-AZ requirements in
architecture/reliability.md.

## 2. Traffic Flow

```
Internet → CloudFront/ALB (public subnet) → ECS tasks (private subnet)
   → RDS / ElastiCache (private subnet, no public route)
```

No database, cache, or worker resource has a public IP or is reachable
directly from the internet — all inbound traffic passes through the ALB,
all outbound third-party calls (LLM, OCR, SMS providers) go through a NAT
gateway.

## 3. Security Groups

Least-privilege security group rules: the ALB security group only accepts
443 from the internet; the ECS task security group only accepts traffic
from the ALB security group (not from the internet directly); the RDS/
Redis security groups only accept traffic from the ECS task security
group (not from each other, not from the internet).

## 4. Isolation from Malicious Uploads (threat-model.md #5)

The OCR worker's network path to third-party OCR providers is outbound-only
through the NAT gateway; it has no inbound listener and no direct route to
the database beyond what its service-account IAM/DB role permits, limiting
blast radius if a crafted malicious file were ever to exploit the OCR
pipeline itself.

## 5. Environment Isolation

Staging and production VPCs have no peering or shared route tables — fully
network-isolated, consistent with environments.md's account/environment
separation policy.
