output "key_vault_id" {
  description = "Resource ID of the Key Vault"
  value       = azurerm_key_vault.this.id
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.this.vault_uri
}

output "identity_id" {
  description = "Resource ID of the shared User Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.this.id
}

output "identity_principal_id" {
  description = "Principal ID of the shared User Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.this.principal_id
}

output "identity_client_id" {
  description = "Client ID of the shared User Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.this.client_id
}
