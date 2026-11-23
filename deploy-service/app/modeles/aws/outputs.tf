output "adresses_serveurs" {
  description = "Adresses IP publiques des serveurs (secret GitHub SERVEURS)"
  value       = aws_instance.app[*].public_ip
}

output "adresse_base" {
  description = "Adresse de la base de données (DB_HOST dans le fichier .env)"
  value       = aws_db_instance.base.address
}
