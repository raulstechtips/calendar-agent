data "azurerm_client_config" "current" {}

# --- Key Vault (RBAC mode) ---

resource "azurerm_key_vault" "this" {
  name                = "kv-${var.name_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = var.tenant_id
  sku_name            = var.sku_name

  rbac_authorization_enabled = true
  soft_delete_retention_days = var.soft_delete_retention_days
  purge_protection_enabled   = var.purge_protection_enabled

  tags = var.common_tags
}

# --- Shared User Assigned Managed Identity ---

resource "azurerm_user_assigned_identity" "this" {
  name                = "id-${var.name_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name

  tags = var.common_tags
}

# --- Role Assignments ---

resource "azurerm_role_assignment" "identity_secrets_user" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

resource "azurerm_role_assignment" "deployer_secrets_officer" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}
