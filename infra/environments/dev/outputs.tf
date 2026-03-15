output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.this.name
}

output "resource_group_id" {
  description = "Resource ID of the resource group"
  value       = azurerm_resource_group.this.id
}

output "location" {
  description = "Azure region of deployed resources"
  value       = azurerm_resource_group.this.location
}

output "name_suffix" {
  description = "Name suffix for CAF-compliant resource naming (project-environment-region)"
  value       = local.name_suffix
}

output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# AI Services outputs

output "openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  value       = module.ai_services.openai_endpoint
}

output "search_endpoint" {
  description = "Azure AI Search endpoint URL"
  value       = module.ai_services.search_endpoint
}

output "openai_deployment_name" {
  description = "Name of the GPT-4o model deployment"
  value       = module.ai_services.openai_deployment_name
}

output "openai_embed_deployment_name" {
  description = "Name of the text-embedding-3-small model deployment"
  value       = module.ai_services.openai_embed_deployment_name
}

output "content_safety_endpoint" {
  description = "Azure AI Content Safety endpoint URL"
  value       = module.ai_services.content_safety_endpoint
}

output "backend_identity_id" {
  description = "Resource ID of the backend User Assigned Managed Identity"
  value       = module.ai_services.backend_identity_id
}

output "backend_identity_client_id" {
  description = "Client ID of the backend User Assigned Managed Identity"
  value       = module.ai_services.backend_identity_client_id
}

output "backend_identity_principal_id" {
  description = "Principal ID of the backend User Assigned Managed Identity"
  value       = module.ai_services.backend_identity_principal_id
}

# --- Key Vault ---

output "key_vault_id" {
  description = "Resource ID of the Key Vault"
  value       = module.key_vault.key_vault_id
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = module.key_vault.key_vault_uri
}

# --- Shared Managed Identity ---

output "shared_identity_id" {
  description = "Resource ID of the shared User Assigned Managed Identity"
  value       = module.key_vault.identity_id
}

output "shared_identity_principal_id" {
  description = "Principal ID of the shared User Assigned Managed Identity"
  value       = module.key_vault.identity_principal_id
}

output "shared_identity_client_id" {
  description = "Client ID of the shared User Assigned Managed Identity"
  value       = module.key_vault.identity_client_id
}