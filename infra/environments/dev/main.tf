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
