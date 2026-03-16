# Bootstrap (one-time): create the storage account for remote state:
#   az group create -n rg-tfstate-calendaragent -l eastus
#   az storage account create -n stcalendaragenttfstate -g rg-tfstate-calendaragent \
#     -l eastus --sku Standard_LRS --encryption-services blob
#   az storage container create -n tfstate --account-name stcalendaragenttfstate

terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-calendaragent"
    storage_account_name = "stcalendaragenttfstate"
    container_name       = "tfstate"
    key                  = "dev/foundation.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

locals {
  location_short = {
    eastus    = "eus"
    westus2   = "wus2"
    centralus = "cus"
  }

  name_suffix = "${var.project_name}-${var.environment}-${local.location_short[var.location]}"

  common_tags = {
    environment = var.environment
    project     = var.project_name
    managed-by  = "terraform"
  }
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.name_suffix}"
  location = var.location

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Networking — VNet, subnets, Private DNS zones
# -----------------------------------------------------------------------------

module "networking" {
  source = "../../modules/networking"

  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  name_suffix         = local.name_suffix
  common_tags         = local.common_tags
}

# -----------------------------------------------------------------------------
# AI Services — OpenAI, AI Search, Content Safety + backend identity
# -----------------------------------------------------------------------------

module "ai_services" {
  source = "../../modules/ai-services"

  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  name_suffix         = local.name_suffix
  common_tags         = local.common_tags

  private_endpoints_subnet_id = module.networking.private_endpoints_subnet_id
  openai_dns_zone_id          = module.networking.dns_zone_ids["openai"]
  search_dns_zone_id          = module.networking.dns_zone_ids["search"]
  content_safety_dns_zone_id  = module.networking.dns_zone_ids["content_safety"]
  deployer_ip_cidrs           = var.deployer_ip_cidrs
}

# --- Data Sources ---

data "azurerm_client_config" "current" {}

# --- Key Vault + Shared Managed Identity ---

module "key_vault" {
  source = "../../modules/key-vault"

  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  name_suffix         = local.name_suffix
  common_tags         = local.common_tags
  tenant_id           = data.azurerm_client_config.current.tenant_id

  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  private_endpoints_subnet_id = module.networking.private_endpoints_subnet_id
  key_vault_dns_zone_id       = module.networking.dns_zone_ids["key_vault"]
  deployer_ip_cidrs           = var.deployer_ip_cidrs
}

# --- App Secrets (Key Vault) ---

resource "azurerm_key_vault_secret" "fernet_key" {
  name         = "fernet-key"
  value        = var.fernet_key
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

resource "azurerm_key_vault_secret" "google_client_id" {
  name         = "google-client-id"
  value        = var.google_client_id
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

resource "azurerm_key_vault_secret" "google_client_secret" {
  name         = "google-client-secret"
  value        = var.google_client_secret
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

resource "azurerm_key_vault_secret" "auth_secret" {
  name         = "auth-secret"
  value        = var.auth_secret
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

resource "azurerm_key_vault_secret" "canary_token" {
  name         = "canary-token"
  value        = var.canary_token
  key_vault_id = module.key_vault.key_vault_id

  tags = local.common_tags

  depends_on = [module.key_vault]
}

# -----------------------------------------------------------------------------
# Redis — Azure Cache for Redis (token + session storage)
# -----------------------------------------------------------------------------

module "redis" {
  source = "../../modules/redis"

  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  name_suffix         = local.name_suffix
  common_tags         = local.common_tags

  key_vault_id                = module.key_vault.key_vault_id
  private_endpoints_subnet_id = module.networking.private_endpoints_subnet_id
  redis_dns_zone_id           = module.networking.dns_zone_ids["redis"]

  depends_on = [module.key_vault]
}
