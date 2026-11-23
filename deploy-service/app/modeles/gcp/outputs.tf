output "adresses_serveurs" {
  description = "Adresses IP publiques des serveurs (secret GitHub SERVEURS)"
  value       = google_compute_instance.app[*].network_interface[0].access_config[0].nat_ip
}

output "adresse_base" {
  description = "Adresse de la base de données (DB_HOST dans le fichier .env)"
  value       = google_sql_database_instance.base.public_ip_address
}
