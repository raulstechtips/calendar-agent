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

# --- Network hardening ---

variable "private_endpoints_subnet_id" {
  description = "Resource ID of the Private Endpoints subnet"
  type        = string
}

variable "openai_dns_zone_id" {
  description = "Resource ID of the privatelink.openai.azure.com DNS zone"
  type        = string
}

variable "search_dns_zone_id" {
  description = "Resource ID of the privatelink.search.windows.net DNS zone"
  type        = string
}

variable "content_safety_dns_zone_id" {
  description = "Resource ID of the privatelink.cognitiveservices.azure.com DNS zone"
  type        = string
}

variable "deployer_ip_cidrs" {
  description = "List of CIDR strings allowed through service firewalls (Terraform deployer IPs)"
  type        = list(string)
}

# --- Developer access (dev environment only) ---

variable "environment" {
  description = "Deployment environment name. Used to guard developer-only resources (e.g. RBAC role assignments for local development)."
  type        = string
}

variable "developer_object_id" {
  description = "Entra ID object ID of the developer running the app locally. Grants data-plane RBAC roles so DefaultAzureCredential (az login) can access AI services during local development. Get it with: az ad signed-in-user show --query id -o tsv"
  type        = string
  sensitive   = true
  default     = null
}
