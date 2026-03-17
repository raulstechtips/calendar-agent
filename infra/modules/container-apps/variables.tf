# --- Standard ---

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
}

variable "name_suffix" {
  description = "CAF name suffix (project-environment-region)"
  type        = string
}

variable "common_tags" {
  description = "Tags applied to all resources"
  type        = map(string)
}

# --- Network ---

variable "container_apps_subnet_id" {
  description = "Resource ID of the subnet delegated to the Container Apps Environment"
  type        = string
}

# --- Identities ---

variable "shared_identity_id" {
  description = "Resource ID of the shared User Assigned Managed Identity (Key Vault + ACR access)"
  type        = string
}

variable "shared_identity_principal_id" {
  description = "Principal ID of the shared User Assigned Managed Identity (for role assignments)"
  type        = string
}

variable "backend_identity_id" {
  description = "Resource ID of the backend User Assigned Managed Identity (AI services access)"
  type        = string
}

variable "backend_identity_client_id" {
  description = "Client ID of the backend User Assigned Managed Identity (for AZURE_MANAGED_IDENTITY_CLIENT_ID env var)"
  type        = string
}

# --- Key Vault Secret URIs ---

variable "redis_connection_string_secret_id" {
  description = "Versionless Key Vault secret URI for the Redis connection string"
  type        = string
  sensitive   = true
}

variable "fernet_key_secret_id" {
  description = "Versionless Key Vault secret URI for the Fernet encryption key"
  type        = string
  sensitive   = true
}

variable "google_client_id_secret_id" {
  description = "Versionless Key Vault secret URI for the Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret_secret_id" {
  description = "Versionless Key Vault secret URI for the Google OAuth client secret"
  type        = string
  sensitive   = true
}

variable "auth_secret_secret_id" {
  description = "Versionless Key Vault secret URI for the Auth.js session secret"
  type        = string
  sensitive   = true
}

variable "canary_token_secret_id" {
  description = "Versionless Key Vault secret URI for the prompt injection canary token"
  type        = string
  sensitive   = true
}

# --- AI Service Config (plain env vars for backend) ---

variable "openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  type        = string
}

variable "openai_deployment_name" {
  description = "Name of the GPT-4o model deployment"
  type        = string
}

variable "openai_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = "2024-10-21"
}

variable "openai_embed_deployment_name" {
  description = "Name of the text-embedding-3-small model deployment"
  type        = string
}

variable "search_endpoint" {
  description = "Azure AI Search endpoint URL"
  type        = string
}

variable "search_index_name" {
  description = "Azure AI Search index name"
  type        = string
  default     = "calendar-context"
}

variable "content_safety_endpoint" {
  description = "Azure AI Content Safety endpoint URL"
  type        = string
}

# --- Container Settings ---

variable "frontend_image" {
  description = "Full image reference for the frontend container (overridden by CI once images are pushed to ACR)"
  type        = string
  default     = "mcr.microsoft.com/k8se/quickstart:latest"
}

variable "backend_image" {
  description = "Full image reference for the backend container (overridden by CI once images are pushed to ACR)"
  type        = string
  default     = "mcr.microsoft.com/k8se/quickstart:latest"
}

variable "frontend_cpu" {
  description = "CPU cores allocated to the frontend container"
  type        = number
  default     = 0.25
}

variable "frontend_memory" {
  description = "Memory allocated to the frontend container"
  type        = string
  default     = "0.5Gi"
}

variable "backend_cpu" {
  description = "CPU cores allocated to the backend container"
  type        = number
  default     = 0.25
}

variable "backend_memory" {
  description = "Memory allocated to the backend container"
  type        = string
  default     = "0.5Gi"
}

variable "frontend_min_replicas" {
  description = "Minimum number of frontend container replicas"
  type        = number
  default     = 0
}

variable "frontend_max_replicas" {
  description = "Maximum number of frontend container replicas"
  type        = number
  default     = 1
}

variable "backend_min_replicas" {
  description = "Minimum number of backend container replicas"
  type        = number
  default     = 0
}

variable "backend_max_replicas" {
  description = "Maximum number of backend container replicas"
  type        = number
  default     = 1
}

# --- Log Analytics ---

variable "log_retention_days" {
  description = "Number of days to retain logs in the Log Analytics workspace"
  type        = number
  default     = 30
}

# --- ACR ---

variable "acr_sku" {
  description = "SKU for the Azure Container Registry"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be one of: Basic, Standard, Premium."
  }
}

# --- GitHub Actions OIDC ---

variable "github_repo_name" {
  description = "GitHub repository in org/repo format for OIDC federated credentials"
  type        = string

  validation {
    condition = (
      length(split("/", var.github_repo_name)) == 2 &&
      can(regex("^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$", split("/", var.github_repo_name)[0])) &&
      can(regex("^[A-Za-z0-9._-]{1,100}$", split("/", var.github_repo_name)[1]))
    )
    error_message = "github_repo_name must be owner/repo: owner (alphanumeric + hyphens, max 39 chars), repo (alphanumeric + hyphen/underscore/dot, max 100 chars)."
  }
}
