output "redis_id" {
  description = "Resource ID of the Azure Cache for Redis instance"
  value       = azurerm_redis_cache.this.id
}

output "redis_hostname" {
  description = "Hostname of the Redis instance"
  value       = azurerm_redis_cache.this.hostname
}

output "redis_ssl_port" {
  description = "TLS port of the Redis instance"
  value       = azurerm_redis_cache.this.ssl_port
}

output "redis_access_key_secret_id" {
  description = "Versionless Key Vault secret URI for the Redis primary access key"
  value       = azurerm_key_vault_secret.redis_access_key.versionless_id
}

output "redis_connection_string_secret_id" {
  description = "Versionless Key Vault secret URI for the Redis connection string"
  value       = azurerm_key_vault_secret.redis_connection_string.versionless_id
}
