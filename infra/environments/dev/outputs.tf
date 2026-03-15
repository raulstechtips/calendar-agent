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
