output "openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "search_endpoint" {
  description = "Azure AI Search endpoint URL"
  value       = "https://${azurerm_search_service.this.name}.search.windows.net"
}

output "openai_deployment_name" {
  description = "Name of the GPT-4o model deployment"
  value       = azurerm_cognitive_deployment.gpt_4o.name
}

output "openai_embed_deployment_name" {
  description = "Name of the text-embedding-3-small model deployment"
  value       = azurerm_cognitive_deployment.text_embedding_3_small.name
}

output "content_safety_endpoint" {
  description = "Azure AI Content Safety endpoint URL"
  value       = azurerm_cognitive_account.content_safety.endpoint
}

output "backend_identity_id" {
  description = "Resource ID of the backend User Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.backend.id
}

output "backend_identity_client_id" {
  description = "Client ID of the backend User Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.backend.client_id
}

output "backend_identity_principal_id" {
  description = "Principal ID of the backend User Assigned Managed Identity"
  value       = azurerm_user_assigned_identity.backend.principal_id
}
