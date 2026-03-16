output "vnet_id" {
  description = "Resource ID of the virtual network"
  value       = azurerm_virtual_network.this.id
}

output "container_apps_subnet_id" {
  description = "Resource ID of the Container Apps Environment subnet"
  value       = azurerm_subnet.container_apps.id
}

output "private_endpoints_subnet_id" {
  description = "Resource ID of the Private Endpoints subnet"
  value       = azurerm_subnet.private_endpoints.id
}

output "dns_zone_ids" {
  description = "Map of service key to Private DNS zone resource ID"
  value       = { for k, z in azurerm_private_dns_zone.this : k => z.id }
}
