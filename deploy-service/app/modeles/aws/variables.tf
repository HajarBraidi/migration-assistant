variable "projet" {
  description = "Nom court du projet (minuscules et tirets)"
  type        = string
  default     = "«nom_projet»"
}

variable "region" {
  description = "Région AWS"
  type        = string
  default     = "eu-west-3" # Paris
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
  description = "Base de données répliquée dans une deuxième zone"
  type        = bool
  default     = «haute_disponibilite»
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
  description = "Contenu de la clé SSH publique de déploiement"
  type        = string
}

variable "ip_administrateurs" {
  description = "Adresse autorisée en SSH, par exemple 196.12.34.56/32"
  type        = string
}
