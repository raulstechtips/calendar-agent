---
description: Terraform and infrastructure conventions
paths:
  - "infra/**"
---

# Infrastructure Rules (Terraform + Azure)

## Module Structure

- One module per logical resource group: `container-apps/`, `redis/`, `ai-services/`
- Each module has: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`
- Root modules (in `environments/`) compose modules — minimal resource blocks directly
- Use relative paths for local modules: `source = "../../modules/redis"`

## Naming Conventions

- `snake_case` for all Terraform identifiers (variables, resources, outputs)
- Use `this` as the resource name when a module contains a single resource of that type
- Azure resource names follow CAF pattern: `{type-abbrev}-{workload}-{environment}-{region}-{instance}`
- Examples: `rg-calendaragent-dev-eus`, `ca-frontend-dev-eus`, `redis-calendaragent-dev-eus`

## Variable Rules

- Include `description` for every variable
- Block ordering: `description`, `type`, `default`, `validation`
- Mark sensitive variables with `sensitive = true`
- Use plural names for `list(...)` and `map(...)` types
- No double negatives: `encryption_enabled` not `encryption_disabled`

## Resource Block Ordering

1. `count` or `for_each` (first, blank line after)
2. Regular arguments
3. `tags` (last argument)
4. `depends_on` and `lifecycle` (separated by blank lines)

## Security

- NEVER hardcode secrets in `.tf` files — use variables with `sensitive = true` or Key Vault references
- Use Managed Identity (Entra ID) over API keys where Azure supports it
- Pin provider versions explicitly: `~> 4.64`, never `>= 4.0`
- Tag all resources: `environment`, `project`, `managed-by = "terraform"`

## Validation Before Commit

- `terraform fmt -check` must pass
- `terraform validate` must pass
- Review `terraform plan` output — flag any unexpected resource deletions
- Never commit `terraform.tfstate` or `*.tfvars` with real values

## State

- Remote backend only (Azure Storage with encryption, versioning, locking)
- Separate state keys per environment
- Never commit state files to git
