output "adresses_serveurs" {
  description = "Adresses IP publiques des serveurs (secret GitHub SERVEURS)"
  value       = azurerm_public_ip.app[*].ip_address
}
