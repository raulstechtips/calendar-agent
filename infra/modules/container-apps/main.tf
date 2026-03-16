locals {
  acr_name      = replace(var.name_suffix, "-", "")
  frontend_name = "ca-frontend-${var.name_suffix}"
  backend_name  = "ca-backend-${var.name_suffix}"

  # Derive FQDNs from CAE default_domain + deterministic app names.
  # This avoids a circular dependency between the two Container Apps:
  # frontend needs backend FQDN (NEXT_PUBLIC_API_URL) and backend needs
  # frontend FQDN (CORS_ORIGINS). Both depend only on the CAE resource.
  frontend_fqdn = "${local.frontend_name}.${azurerm_container_app_environment.this.default_domain}"
  backend_fqdn  = "${local.backend_name}.internal.${azurerm_container_app_environment.this.default_domain}"
}

# -----------------------------------------------------------------------------
# Log Analytics Workspace
# -----------------------------------------------------------------------------

resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${var.name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# Azure Container Registry
# -----------------------------------------------------------------------------

resource "azurerm_container_registry" "this" {
  name                          = "acr${local.acr_name}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  sku                           = var.acr_sku
  admin_enabled                 = false
  public_network_access_enabled = true # Required for CI image push; Basic SKU has no PE support

  tags = var.common_tags
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPull"
  principal_id         = var.shared_identity_principal_id
}

# -----------------------------------------------------------------------------
# Container Apps Environment (VNet-integrated, workload profiles)
# -----------------------------------------------------------------------------

resource "azurerm_container_app_environment" "this" {
  name                           = "cae-${var.name_suffix}"
  resource_group_name            = var.resource_group_name
  location                       = var.location
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.this.id
  infrastructure_subnet_id       = var.container_apps_subnet_id
  internal_load_balancer_enabled = false

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }

  tags = var.common_tags
}

# -----------------------------------------------------------------------------
# Frontend Container App — external ingress, port 3000, shared identity only
# -----------------------------------------------------------------------------

resource "azurerm_container_app" "frontend" {
  name                         = local.frontend_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [var.shared_identity_id]
  }

  registry {
    server   = azurerm_container_registry.this.login_server
    identity = var.shared_identity_id
  }

  # --- Key Vault secret references ---

  secret {
    name                = "auth-secret"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.auth_secret_secret_id
  }

  secret {
    name                = "google-client-id"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.google_client_id_secret_id
  }

  secret {
    name                = "google-client-secret"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.google_client_secret_secret_id
  }

  template {
    min_replicas = var.frontend_min_replicas
    max_replicas = var.frontend_max_replicas

    container {
      name   = "frontend"
      image  = var.frontend_image
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      env {
        name        = "AUTH_SECRET"
        secret_name = "auth-secret"
      }

      env {
        name        = "AUTH_GOOGLE_ID"
        secret_name = "google-client-id"
      }

      env {
        name        = "AUTH_GOOGLE_SECRET"
        secret_name = "google-client-secret"
      }

      env {
        name  = "AUTH_TRUST_HOST"
        value = "true"
      }

      # Server-side proxy reads this at runtime to forward API calls to the
      # internal backend. Client-side code uses relative URLs via api.ts and
      # proxy.ts — the browser never contacts the backend directly.
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = "https://${local.backend_fqdn}"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = var.common_tags

  depends_on = [azurerm_role_assignment.acr_pull]
}

# -----------------------------------------------------------------------------
# Backend Container App — internal ingress, port 8000, shared + backend identity
# -----------------------------------------------------------------------------

resource "azurerm_container_app" "backend" {
  name                         = local.backend_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [var.shared_identity_id, var.backend_identity_id]
  }

  registry {
    server   = azurerm_container_registry.this.login_server
    identity = var.shared_identity_id
  }

  # --- Key Vault secret references ---

  secret {
    name                = "redis-connection-string"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.redis_connection_string_secret_id
  }

  secret {
    name                = "fernet-key"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.fernet_key_secret_id
  }

  secret {
    name                = "google-client-id"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.google_client_id_secret_id
  }

  secret {
    name                = "google-client-secret"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.google_client_secret_secret_id
  }

  secret {
    name                = "canary-token"
    identity            = var.shared_identity_id
    key_vault_secret_id = var.canary_token_secret_id
  }

  template {
    min_replicas = var.backend_min_replicas
    max_replicas = var.backend_max_replicas

    container {
      name   = "backend"
      image  = var.backend_image
      cpu    = var.backend_cpu
      memory = var.backend_memory

      env {
        name        = "REDIS_URL"
        secret_name = "redis-connection-string"
      }

      env {
        name        = "FERNET_KEY"
        secret_name = "fernet-key"
      }

      env {
        name        = "GOOGLE_CLIENT_ID"
        secret_name = "google-client-id"
      }

      env {
        name        = "GOOGLE_CLIENT_SECRET"
        secret_name = "google-client-secret"
      }

      env {
        name        = "CANARY_TOKEN"
        secret_name = "canary-token"
      }

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = var.openai_endpoint
      }

      env {
        name  = "AZURE_OPENAI_DEPLOYMENT"
        value = var.openai_deployment_name
      }

      env {
        name  = "AZURE_OPENAI_API_VERSION"
        value = var.openai_api_version
      }

      env {
        name  = "AZURE_OPENAI_EMBED_DEPLOYMENT"
        value = var.openai_embed_deployment_name
      }

      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = var.search_endpoint
      }

      env {
        name  = "AZURE_SEARCH_INDEX"
        value = var.search_index_name
      }

      env {
        name  = "AZURE_CONTENT_SAFETY_ENDPOINT"
        value = var.content_safety_endpoint
      }

      env {
        name  = "AZURE_MANAGED_IDENTITY_CLIENT_ID"
        value = var.backend_identity_client_id
      }

      env {
        name  = "CORS_ORIGINS"
        value = "https://${local.frontend_fqdn}"
      }
    }
  }

  ingress {
    external_enabled = false
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = var.common_tags

  depends_on = [azurerm_role_assignment.acr_pull]
}
