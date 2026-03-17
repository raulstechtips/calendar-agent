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

# --- Networking ---

output "vnet_id" {
  description = "Resource ID of the virtual network"
  value       = module.networking.vnet_id
}

output "container_apps_subnet_id" {
  description = "Resource ID of the Container Apps Environment subnet"
  value       = module.networking.container_apps_subnet_id
}

output "private_endpoints_subnet_id" {
  description = "Resource ID of the Private Endpoints subnet"
  value       = module.networking.private_endpoints_subnet_id
}

output "dns_zone_ids" {
  description = "Map of service key to Private DNS zone resource ID"
  value       = module.networking.dns_zone_ids
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

# --- Container Apps ---

output "container_app_environment_id" {
  description = "Resource ID of the Container Apps Environment"
  value       = module.container_apps.container_app_environment_id
}

output "frontend_url" {
  description = "Full HTTPS URL of the frontend Container App"
  value       = module.container_apps.frontend_url
}

output "backend_url" {
  description = "Full HTTPS URL of the backend Container App (internal)"
  value       = module.container_apps.backend_url
}

output "acr_login_server" {
  description = "Login server URL of the Azure Container Registry"
  value       = module.container_apps.acr_login_server
}

# --- GitHub Actions ---

output "github_actions_client_id" {
  description = "Client ID for GitHub Actions OIDC (set as AZURE_CLIENT_ID in GitHub secrets)"
  value       = module.container_apps.github_actions_client_id
}

output "github_actions_tenant_id" {
  description = "Tenant ID for GitHub Actions OIDC (set as AZURE_TENANT_ID in GitHub secrets)"
  value       = module.container_apps.github_actions_tenant_id
}