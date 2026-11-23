# Infrastructure Azure de «nom_projet» : machines virtuelles + base de données gérée (Flexible Server).
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.abonnement_azure
}

resource "azurerm_resource_group" "projet" {
  name     = "${var.projet}-rg"
  location = var.region
}

resource "azurerm_virtual_network" "projet" {
  name                = "${var.projet}-reseau"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.projet.location
  resource_group_name = azurerm_resource_group.projet.name
}

resource "azurerm_subnet" "app" {
  name                 = "app"
  resource_group_name  = azurerm_resource_group.projet.name
  virtual_network_name = azurerm_virtual_network.projet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Pare-feu : web pour tous, SSH seulement depuis l'adresse des administrateurs
resource "azurerm_network_security_group" "app" {
  name                = "${var.projet}-app"
  location            = azurerm_resource_group.projet.location
  resource_group_name = azurerm_resource_group.projet.name

  security_rule {
    name                       = "web"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["80", "443"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "ssh-administrateurs"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.ip_administrateurs
    destination_address_prefix = "*"
  }
}

resource "azurerm_public_ip" "app" {
  count               = var.nombre_serveurs
  name                = "${var.projet}-ip-${count.index + 1}"
  location            = azurerm_resource_group.projet.location
  resource_group_name = azurerm_resource_group.projet.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_interface" "app" {
  count               = var.nombre_serveurs
  name                = "${var.projet}-nic-${count.index + 1}"
  location            = azurerm_resource_group.projet.location
  resource_group_name = azurerm_resource_group.projet.name

  ip_configuration {
    name                          = "principale"
    subnet_id                     = azurerm_subnet.app.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.app[count.index].id
  }
}

resource "azurerm_network_interface_security_group_association" "app" {
  count                     = var.nombre_serveurs
  network_interface_id      = azurerm_network_interface.app[count.index].id
  network_security_group_id = azurerm_network_security_group.app.id
}

resource "azurerm_linux_virtual_machine" "app" {
  count                 = var.nombre_serveurs
  name                  = "${var.projet}-app-${count.index + 1}"
  location              = azurerm_resource_group.projet.location
  resource_group_name   = azurerm_resource_group.projet.name
  size                  = var.type_serveur
  admin_username        = "deploiement"
  network_interface_ids = [azurerm_network_interface.app[count.index].id]
  custom_data           = base64encode(file("${path.module}/../commun/installer-serveur.sh"))

  admin_ssh_key {
    username   = "deploiement"
    public_key = var.cle_ssh_publique
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 30
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }
}
