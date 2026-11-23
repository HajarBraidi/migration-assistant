# Base MySQL gérée. Le nom du serveur doit être unique dans tout Azure.
resource "azurerm_mysql_flexible_server" "base" {
  name                   = "${var.projet}-base"
  location               = azurerm_resource_group.projet.location
  resource_group_name    = azurerm_resource_group.projet.name
  version                = "8.0.21" # passer à "8.4" dès que votre région le propose
  administrator_login    = var.utilisateur_base
  administrator_password = var.mot_de_passe_base
  sku_name               = var.type_base
  backup_retention_days  = 7
  zone                   = "1"

  storage {
    size_gb = var.stockage_go
  }

  dynamic "high_availability" {
    for_each = var.haute_disponibilite ? [1] : []
    content {
      mode                      = "ZoneRedundant"
      standby_availability_zone = "2"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_mysql_flexible_database" "application" {
  name                = var.nom_base
  resource_group_name = azurerm_resource_group.projet.name
  server_name         = azurerm_mysql_flexible_server.base.name
  charset             = "utf8mb4"
  collation           = "utf8mb4_unicode_ci"
}

# Seuls les serveurs d'application peuvent se connecter à la base
resource "azurerm_mysql_flexible_server_firewall_rule" "app" {
  count               = var.nombre_serveurs
  name                = "serveur-${count.index + 1}"
  resource_group_name = azurerm_resource_group.projet.name
  server_name         = azurerm_mysql_flexible_server.base.name
  start_ip_address    = azurerm_public_ip.app[count.index].ip_address
  end_ip_address      = azurerm_public_ip.app[count.index].ip_address
}

output "adresse_base" {
  description = "Adresse de la base de données (DB_HOST dans le fichier .env)"
  value       = azurerm_mysql_flexible_server.base.fqdn
}
