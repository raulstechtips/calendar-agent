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

variable "tenant_id" {
  description = "Azure AD tenant ID for the Key Vault"
  type        = string
}

variable "soft_delete_retention_days" {
  description = "Number of days to retain soft-deleted vaults"
  type        = number
  default     = 7

  validation {
    condition     = var.soft_delete_retention_days >= 7 && var.soft_delete_retention_days <= 90
    error_message = "soft_delete_retention_days must be between 7 and 90."
  }
}

variable "purge_protection_enabled" {
  description = "Whether purge protection is enabled on the Key Vault (default true for safety; override to false in dev)"
  type        = bool
  default     = true
}

variable "sku_name" {
  description = "SKU tier for the Key Vault"
  type        = string
  default     = "standard"

  validation {
    condition     = contains(["standard", "premium"], var.sku_name)
    error_message = "sku_name must be \"standard\" or \"premium\"."
  }
}
