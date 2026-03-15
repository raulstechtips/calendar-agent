# Bootstrap (one-time): create the storage account for remote state:
#   az group create -n rg-tfstate-calendaragent -l eastus
#   az storage account create -n stcalendaragenttfstate -g rg-tfstate-calendaragent \
#     -l eastus --sku Standard_LRS --encryption-services blob
#   az storage container create -n tfstate --account-name stcalendaragenttfstate

terraform {
  backend "azurerm" {
    resource_group_name  = "rg-tfstate-calendaragent"
    storage_account_name = "stcalendaragenttfstate"
    container_name       = "tfstate"
    key                  = "dev/foundation.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

locals {
  location_short = {
    eastus    = "eus"
    westus2   = "wus2"
    centralus = "cus"
  }

  name_suffix = "${var.project_name}-${var.environment}-${local.location_short[var.location]}"

  common_tags = {
    environment = var.environment
    project     = var.project_name
    managed-by  = "terraform"
  }
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.name_suffix}"
  location = var.location

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# AI Services — OpenAI, AI Search, Content Safety + backend identity
# -----------------------------------------------------------------------------

module "ai_services" {
  source = "../../modules/ai-services"

  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  name_suffix         = local.name_suffix
  common_tags         = local.common_tags
}
