# Base PostgreSQL gérée. Le nom du serveur doit être unique dans tout Azure.
resource "azurerm_postgresql_flexible_server" "base" {
  name                          = "${var.projet}-base"
  location                      = azurerm_resource_group.projet.location
  resource_group_name           = azurerm_resource_group.projet.name
  version                       = "16"
  administrator_login           = var.utilisateur_base
  administrator_password        = var.mot_de_passe_base
  sku_name                      = var.type_base
  storage_mb                    = «stockage_mb»
  backup_retention_days         = 7
  zone                          = "1"
  public_network_access_enabled = true

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

resource "azurerm_postgresql_flexible_server_database" "application" {
  name      = var.nom_base
  server_id = azurerm_postgresql_flexible_server.base.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Seuls les serveurs d'application peuvent se connecter à la base
resource "azurerm_postgresql_flexible_server_firewall_rule" "app" {
  count            = var.nombre_serveurs
  name             = "serveur-${count.index + 1}"
  server_id        = azurerm_postgresql_flexible_server.base.id
  start_ip_address = azurerm_public_ip.app[count.index].ip_address
  end_ip_address   = azurerm_public_ip.app[count.index].ip_address
}

output "adresse_base" {
  description = "Adresse de la base de données (DB_HOST dans le fichier .env)"
  value       = azurerm_postgresql_flexible_server.base.fqdn
}
