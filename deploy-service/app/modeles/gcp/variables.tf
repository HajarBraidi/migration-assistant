variable "projet" {
  description = "Nom court du projet (minuscules et tirets)"
  type        = string
  default     = "«nom_projet»"
}

variable "projet_gcp" {
  description = "Identifiant du projet Google Cloud"
  type        = string
}

variable "region" {
  type    = string
  default = "europe-west1" # Belgique
}

variable "zone" {
  type    = string
  default = "europe-west1-b"
}

variable "nombre_serveurs" {
  type    = number
  default = «nombre_serveurs»
}

variable "type_serveur" {
  type    = string
  default = "«type_serveur»"
}

variable "type_base" {
  type    = string
  default = "«type_base»"
}

variable "stockage_go" {
  type    = number
  default = «stockage_go»
}

variable "haute_disponibilite" {
  type    = bool
  default = «haute_disponibilite»
}

variable "nom_base" {
  type    = string
  default = "«nom_base»"
}

variable "utilisateur_base" {
  type    = string
  default = "«utilisateur_base»"
}

variable "mot_de_passe_base" {
  description = "À fournir par la variable d'environnement TF_VAR_mot_de_passe_base (jamais dans un fichier)"
  type        = string
  sensitive   = true
}

variable "cle_ssh_publique" {
  type = string
}

variable "ip_administrateurs" {
  description = "Adresse autorisée en SSH, par exemple 196.12.34.56/32"
  type        = string
}
