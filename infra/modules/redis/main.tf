# --- Azure Cache for Redis ---

resource "azurerm_redis_cache" "this" {
  name                          = "redis-${var.name_suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  sku_name                      = var.sku_name
  family                        = var.family
  capacity                      = var.capacity
  redis_version                 = var.redis_version
  minimum_tls_version           = var.minimum_tls_version
  non_ssl_port_enabled          = false
  public_network_access_enabled = false

  redis_configuration {}

  tags = var.common_tags
}

# --- Key Vault Secrets ---

resource "azurerm_key_vault_secret" "redis_access_key" {
  name         = "redis-access-key"
  value        = azurerm_redis_cache.this.primary_access_key
  key_vault_id = var.key_vault_id

  tags = var.common_tags
}

resource "azurerm_key_vault_secret" "redis_connection_string" {
  name         = "redis-connection-string"
  value        = "rediss://:${azurerm_redis_cache.this.primary_access_key}@${azurerm_redis_cache.this.hostname}:${azurerm_redis_cache.this.ssl_port}/0"
  key_vault_id = var.key_vault_id

  tags = var.common_tags
}

# --- Private Endpoint ---

resource "azurerm_private_endpoint" "redis" {
  name                = "pe-redis-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_endpoints_subnet_id

  private_service_connection {
    name                           = "psc-redis-${var.name_suffix}"
    private_connection_resource_id = azurerm_redis_cache.this.id
    is_manual_connection           = false
    subresource_names              = ["redisCache"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.redis_dns_zone_id]
  }

  tags = var.common_tags
}
