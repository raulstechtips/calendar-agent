variable "project_name" {
  description = "Project name used in resource naming (CAF convention)"
  type        = string
  default     = "calendaragent"

  validation {
    condition     = can(regex("^[a-z0-9]+$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric only."
  }
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"

  validation {
    condition     = var.environment == "dev"
    error_message = "This stack only supports environment = \"dev\"."
  }
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"

  validation {
    condition     = contains(["eastus", "westus2", "centralus"], var.location)
    error_message = "Location must be one of: eastus, westus2, centralus."
  }
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "Subscription ID must be a valid GUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)."
  }
}

# --- Developer access ---

variable "developer_object_id" {
  description = "Entra ID object ID of the developer. Used to grant data-plane RBAC on AI services for local development with DefaultAzureCredential. Get it with: az ad signed-in-user show --query id -o tsv"
  type        = string
  sensitive   = true
  default     = null

  validation {
    condition     = var.developer_object_id == null || can(regex("(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.developer_object_id))
    error_message = "developer_object_id must be a valid GUID format."
  }
}

# --- Network ---

variable "deployer_ip_cidrs" {
  description = "List of CIDR strings for Terraform deployer IP allowlisting on service firewalls"
  type        = list(string)
  default     = []
}

# --- App secrets (stored in Key Vault) ---

variable "fernet_key" {
  description = "Fernet encryption key for token storage"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.fernet_key)) > 0 && var.fernet_key != "CHANGE_ME"
    error_message = "fernet_key must be set to a real secret value, not a placeholder."
  }
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.google_client_id)) > 0 && var.google_client_id != "CHANGE_ME"
    error_message = "google_client_id must be set to a real secret value, not a placeholder."
  }
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.google_client_secret)) > 0 && var.google_client_secret != "CHANGE_ME"
    error_message = "google_client_secret must be set to a real secret value, not a placeholder."
  }
}

variable "auth_secret" {
  description = "Auth.js session secret"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.auth_secret)) > 0 && var.auth_secret != "CHANGE_ME"
    error_message = "auth_secret must be set to a real secret value, not a placeholder."
  }
}

variable "canary_token" {
  description = "Canary token for prompt injection detection"
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.canary_token)) > 0 && var.canary_token != "CHANGE_ME"
    error_message = "canary_token must be set to a real secret value, not a placeholder."
  }
}

# --- GitHub Actions ---

variable "github_repo_name" {
  description = "GitHub repository in org/repo format for OIDC federated credentials"
  type        = string
}
