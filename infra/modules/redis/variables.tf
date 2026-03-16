variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
}

variable "name_suffix" {
  description = "CAF name suffix (e.g. calendaragent-dev-eus)"
  type        = string
}

variable "common_tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
}

variable "key_vault_id" {
  description = "Resource ID of the Key Vault to store Redis secrets in"
  type        = string
}

# --- Redis settings ---

variable "sku_name" {
  description = "Redis SKU tier"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku_name)
    error_message = "sku_name must be one of: Basic, Standard, Premium."
  }
}

variable "family" {
  description = "Redis SKU family (C for Basic/Standard, P for Premium)"
  type        = string
  default     = "C"

  validation {
    condition     = contains(["C", "P"], var.family)
    error_message = "family must be \"C\" (Basic/Standard) or \"P\" (Premium)."
  }
}

variable "capacity" {
  description = "Redis cache size (0–6 for C-family, 1–5 for P-family)"
  type        = number
  default     = 0

  validation {
    condition     = var.capacity >= 0 && var.capacity <= 6
    error_message = "capacity must be between 0 and 6."
  }
}

variable "redis_version" {
  description = "Major version of Redis to deploy"
  type        = string
  default     = "6"

  validation {
    condition     = contains(["6"], var.redis_version)
    error_message = "redis_version must be \"6\"."
  }
}

variable "minimum_tls_version" {
  description = "Minimum TLS version for client connections"
  type        = string
  default     = "1.2"

  validation {
    condition     = contains(["1.0", "1.1", "1.2"], var.minimum_tls_version)
    error_message = "minimum_tls_version must be \"1.0\", \"1.1\", or \"1.2\"."
  }
}

# --- Network hardening ---

variable "private_endpoints_subnet_id" {
  description = "Resource ID of the Private Endpoints subnet"
  type        = string
}

variable "redis_dns_zone_id" {
  description = "Resource ID of the privatelink.redis.cache.windows.net DNS zone"
  type        = string
}
