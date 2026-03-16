output "container_app_environment_id" {
  description = "Resource ID of the Container Apps Environment"
  value       = azurerm_container_app_environment.this.id
}

output "container_app_environment_default_domain" {
  description = "Default domain of the Container Apps Environment"
  value       = azurerm_container_app_environment.this.default_domain
}

output "frontend_fqdn" {
  description = "FQDN of the frontend Container App (external ingress)"
  value       = azurerm_container_app.frontend.ingress[0].fqdn
}

output "backend_fqdn" {
  description = "FQDN of the backend Container App (internal ingress)"
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "frontend_url" {
  description = "Full HTTPS URL of the frontend Container App"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "backend_url" {
  description = "Full HTTPS URL of the backend Container App (internal)"
  value       = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
}

output "acr_login_server" {
  description = "Login server URL of the Azure Container Registry"
  value       = azurerm_container_registry.this.login_server
}

output "acr_id" {
  description = "Resource ID of the Azure Container Registry"
  value       = azurerm_container_registry.this.id
}

output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics workspace"
  value       = azurerm_log_analytics_workspace.this.id
}
