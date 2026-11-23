# Répartiteur de charge : distribue le trafic entre les machines et écarte une machine en panne.
resource "azurerm_public_ip" "repartiteur" {
  name                = "${var.projet}-ip-repartiteur"
  location            = azurerm_resource_group.projet.location
  resource_group_name = azurerm_resource_group.projet.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_lb" "app" {
  name                = "${var.projet}-lb"
  location            = azurerm_resource_group.projet.location
  resource_group_name = azurerm_resource_group.projet.name
  sku                 = "Standard"

  frontend_ip_configuration {
    name                 = "public"
    public_ip_address_id = azurerm_public_ip.repartiteur.id
  }
}

resource "azurerm_lb_backend_address_pool" "app" {
  name            = "serveurs"
  loadbalancer_id = azurerm_lb.app.id
}

resource "azurerm_network_interface_backend_address_pool_association" "app" {
  count                   = var.nombre_serveurs
  network_interface_id    = azurerm_network_interface.app[count.index].id
  ip_configuration_name   = "principale"
  backend_address_pool_id = azurerm_lb_backend_address_pool.app.id
}

resource "azurerm_lb_probe" "http" {
  name            = "http"
  loadbalancer_id = azurerm_lb.app.id
  protocol        = "Http"
  port            = 80
  request_path    = "/"
}

resource "azurerm_lb_rule" "http" {
  name                           = "http"
  loadbalancer_id                = azurerm_lb.app.id
  protocol                       = "Tcp"
  frontend_port                  = 80
  backend_port                   = 80
  frontend_ip_configuration_name = "public"
  backend_address_pool_ids       = [azurerm_lb_backend_address_pool.app.id]
  probe_id                       = azurerm_lb_probe.http.id
  disable_outbound_snat          = true
}

output "adresse_repartiteur" {
  description = "Adresse publique de l'application (à utiliser dans le DNS)"
  value       = azurerm_public_ip.repartiteur.ip_address
}
