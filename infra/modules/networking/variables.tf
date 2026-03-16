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

variable "address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "container_apps_subnet_cidr" {
  description = "CIDR for the Container Apps Environment subnet (min /23 for CAE delegation)"
  type        = string
  default     = "10.0.0.0/23"
}

variable "private_endpoints_subnet_cidr" {
  description = "CIDR for the Private Endpoints subnet"
  type        = string
  default     = "10.0.2.0/27"
}
