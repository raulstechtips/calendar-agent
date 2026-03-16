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

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
    ip_rules       = var.deployer_ip_cidrs
  }

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

# --- Private Endpoint ---

resource "azurerm_private_endpoint" "key_vault" {
  name                = "pe-kv-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_endpoints_subnet_id

  private_service_connection {
    name                           = "psc-kv-${var.name_suffix}"
    private_connection_resource_id = azurerm_key_vault.this.id
    is_manual_connection           = false
    subresource_names              = ["vault"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.key_vault_dns_zone_id]
  }

  tags = var.common_tags
}
