# calendar-agent

AI Calendar Assistant — Next.js frontend + FastAPI backend + LangGraph agents, deployed on Azure Container Apps.

## Infrastructure (Terraform)

All infrastructure lives in `infra/` and is managed with Terraform.

### Prerequisites

- [Terraform >= 1.14](https://developer.hashicorp.com/terraform/install)
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) — logged in via `az login`
- An Azure subscription with the following resource providers registered:
  `Microsoft.CognitiveServices`, `Microsoft.Search`, `Microsoft.Network`, `Microsoft.App`

### Bootstrap (one-time)

Create the remote state storage account before your first `terraform init`:

```bash
az group create -n rg-tfstate-calendaragent -l eastus
az storage account create -n stcalendaragenttfstate -g rg-tfstate-calendaragent \
  -l eastus --sku Standard_LRS --encryption-services blob
az storage container create -n tfstate --account-name stcalendaragenttfstate
```

### Deploy

```bash
cd infra/environments/dev
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

After apply, grab the endpoints for your `.env` files:

```bash
terraform output
```

### Selective deployment for local development

If you only need AI services for local testing (no Key Vault, Redis, or Container Apps), you can comment out the unused modules in `infra/environments/dev/main.tf`. When doing this, you **must also**:

1. Comment out the corresponding outputs in `environments/dev/outputs.tf` — Terraform will fail if outputs reference modules that don't exist
2. Either comment out or add `default = null` to variables only used by the commented-out modules (e.g., `fernet_key`, `google_client_id`, etc. in `variables.tf`)

### Quotas

Azure OpenAI quotas are per-subscription, per-region, per-model-SKU. New subscriptions often start with **0 quota** for certain SKUs.

To check and adjust quotas:

1. Open your Azure OpenAI resource in the portal
2. Click **Go to Foundry portal**
3. Navigate to **Shared resources > Quota**
4. Find your model (e.g., `gpt-4o — Standard`) and request an increase

**Recommended dev quotas:** 30K TPM for both `gpt-4o` and `text-embedding-3-small`. No cost difference — Azure charges per token consumed, not per quota allocated.

If you see `InsufficientQuota` errors during `terraform apply`, this is why.

### Caveats

**Cognitive Services IP rules don't accept CIDR notation.** Azure AI Search `allowed_ips` accepts `1.2.3.4/32`, but `azurerm_cognitive_account` `network_acls.ip_rules` requires bare IPs (`1.2.3.4`). The Terraform modules handle this automatically by stripping the `/32` suffix.

**Private endpoint race condition.** On first deploy, the OpenAI cognitive account may still be in `Accepted` provisioning state when Terraform tries to create its private endpoint. If you see `AccountProvisioningStateInvalid`, just re-run `terraform apply` — the account will be ready on the second pass.

**Key Vault soft-delete.** Even with `purge_protection_enabled = false`, destroying a Key Vault puts it in soft-deleted state for 7 days. The name stays reserved. After `terraform destroy`, manually purge:

```bash
az keyvault purge --name "kv-calendaragent-dev-eus"
```

**AI Search deletion lag.** Azure AI Search can take 5-15 minutes to fully clean up after destroy. If you immediately re-apply and get a naming conflict, wait a few minutes.

### Teardown

```bash
cd infra/environments/dev
terraform destroy -var-file=terraform.tfvars

# Purge soft-deleted Key Vault (if it was deployed)
az keyvault purge --name "kv-calendaragent-dev-eus"
```

## Local development with Docker

### Azure credential forwarding

The backend uses `DefaultAzureCredential` to authenticate with Azure AI services. In Docker, this requires the Azure CLI to be available inside the container.

The backend Dockerfile has two build targets:

| Target | Use case | Includes |
|---|---|---|
| `development` | Local Docker Compose | Azure CLI, `--reload` |
| `production` | ACR / Container Apps | No dev tools, `--workers 4` |

Docker Compose defaults to the `development` target. For production builds:

```bash
docker build --target production -t your-acr.azurecr.io/backend:latest ./backend
```

### Setup

1. Log in to Azure on your host machine:

   ```bash
   az login
   ```

2. Copy `.env.example` to `.env` in both `frontend/` and `backend/`, then fill in values. Backend Azure endpoints come from `terraform output`.

3. Start everything:

   ```bash
   docker compose up -d --build
   ```

The `~/.azure` directory is mounted into the backend container so the Azure CLI inside can reuse your host login session. This mount is **read-write** — the CLI writes session files (`az.sess`) alongside your token cache.

### Verifying Azure connectivity

Once the backend is running, check the logs:

```bash
docker compose logs backend
```

If you see `DefaultAzureCredential failed to retrieve a token`, verify:

- `az login` is current on your host (`az account show`)
- Your IP is in the service firewall rules (`deployer_ip_cidrs` in your tfvars)
- RBAC role assignments have propagated (can take up to 10 minutes after first deploy)
