# OpenAPI Contract

The canonical API contract will be maintained as `openapi.yaml` at the repository root.

This document defines the contract rules:
- OpenAPI 3.1
- `/api/v1`
- JSON request/response bodies
- OAuth2/JWT authentication
- consistent error envelope
- pagination
- request IDs
- object-level authorization
- idempotency for retry-sensitive commands

The YAML contract should be generated/maintained alongside Pydantic schemas and validated in CI.
