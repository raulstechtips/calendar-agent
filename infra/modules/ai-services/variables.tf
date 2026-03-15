variable "resource_group_name" {
  description = "Name of the resource group to deploy into"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
}

variable "name_suffix" {
  description = "CAF naming suffix (project-environment-region), e.g. calendaragent-dev-eus"
  type        = string
}

variable "common_tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
}

variable "openai_sku" {
  description = "SKU for Azure OpenAI Cognitive Account"
  type        = string
  default     = "S0"

  validation {
    condition     = var.openai_sku == "S0"
    error_message = "Azure OpenAI only supports SKU \"S0\"."
  }
}

variable "search_sku" {
  description = "SKU for Azure AI Search service"
  type        = string
  default     = "basic"

  validation {
    condition     = contains(["basic", "standard", "standard2", "standard3"], var.search_sku)
    error_message = "Search SKU must be one of: basic, standard, standard2, standard3. Free tier does not support disabling local auth."
  }
}

variable "content_safety_sku" {
  description = "SKU for Azure AI Content Safety Cognitive Account"
  type        = string
  default     = "S0"

  validation {
    condition     = contains(["F0", "S0"], var.content_safety_sku)
    error_message = "Content Safety SKU must be \"F0\" or \"S0\"."
  }
}
