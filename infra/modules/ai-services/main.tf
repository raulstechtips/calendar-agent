# -----------------------------------------------------------------------------
# Azure OpenAI
# -----------------------------------------------------------------------------

resource "azurerm_cognitive_account" "openai" {
  name                          = "openai-${var.name_suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  kind                          = "OpenAI"
  sku_name                      = var.openai_sku
  custom_subdomain_name         = "openai-${var.name_suffix}"
  local_auth_enabled            = false
  public_network_access_enabled = true

  network_acls {
    default_action = "Deny"
    ip_rules       = var.deployer_ip_cidrs
  }

  tags = var.common_tags
}

resource "azurerm_cognitive_deployment" "gpt_4o" {
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-11-20"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 10
  }
}

resource "azurerm_cognitive_deployment" "text_embedding_3_small" {
  name                 = "text-embedding-3-small"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-small"
    version = "1"
  }

  sku {
    name     = "Standard"
    capacity = 10
  }
}

# -----------------------------------------------------------------------------
# Azure AI Search
# -----------------------------------------------------------------------------

resource "azurerm_search_service" "this" {
  name                          = "search-${var.name_suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  sku                           = var.search_sku
  local_authentication_enabled  = false
  authentication_failure_mode   = "http403"
  public_network_access_enabled = false

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# Azure AI Content Safety
# -----------------------------------------------------------------------------

resource "azurerm_cognitive_account" "content_safety" {
  name                          = "contentsafety-${var.name_suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  kind                          = "ContentSafety"
  sku_name                      = var.content_safety_sku
  custom_subdomain_name         = "contentsafety-${var.name_suffix}"
  local_auth_enabled            = false
  public_network_access_enabled = true

  network_acls {
    default_action = "Deny"
    ip_rules       = var.deployer_ip_cidrs
  }

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# Backend User Assigned Managed Identity
# -----------------------------------------------------------------------------

resource "azurerm_user_assigned_identity" "backend" {
  name                = "id-backend-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# RBAC Role Assignments — backend identity → AI services
# -----------------------------------------------------------------------------

resource "azurerm_role_assignment" "backend_openai" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

resource "azurerm_role_assignment" "backend_search" {
  scope                = azurerm_search_service.this.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

resource "azurerm_role_assignment" "backend_content_safety" {
  scope                = azurerm_cognitive_account.content_safety.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_user_assigned_identity.backend.principal_id
}

# -----------------------------------------------------------------------------
# Private Endpoints
# -----------------------------------------------------------------------------

resource "azurerm_private_endpoint" "openai" {
  name                = "pe-openai-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_endpoints_subnet_id

  private_service_connection {
    name                           = "psc-openai-${var.name_suffix}"
    private_connection_resource_id = azurerm_cognitive_account.openai.id
    is_manual_connection           = false
    subresource_names              = ["account"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.openai_dns_zone_id]
  }

  tags = var.common_tags
}

resource "azurerm_private_endpoint" "search" {
  name                = "pe-search-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_endpoints_subnet_id

  private_service_connection {
    name                           = "psc-search-${var.name_suffix}"
    private_connection_resource_id = azurerm_search_service.this.id
    is_manual_connection           = false
    subresource_names              = ["searchService"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.search_dns_zone_id]
  }

  tags = var.common_tags
}

resource "azurerm_private_endpoint" "content_safety" {
  name                = "pe-contentsafety-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  subnet_id           = var.private_endpoints_subnet_id

  private_service_connection {
    name                           = "psc-contentsafety-${var.name_suffix}"
    private_connection_resource_id = azurerm_cognitive_account.content_safety.id
    is_manual_connection           = false
    subresource_names              = ["account"]
  }

  private_dns_zone_group {
    name                 = "default"
    private_dns_zone_ids = [var.content_safety_dns_zone_id]
  }

  tags = var.common_tags
}
