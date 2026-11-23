# Infrastructure Google Cloud de «nom_projet» : machines virtuelles + base de données gérée (Cloud SQL).
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.projet_gcp
  region  = var.region
  zone    = var.zone
}

# Pare-feu : web pour tous, SSH seulement depuis l'adresse des administrateurs
resource "google_compute_firewall" "web" {
  name          = "${var.projet}-web"
  network       = "default"
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.projet}-app"]

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
}

resource "google_compute_firewall" "ssh" {
  name          = "${var.projet}-ssh"
  network       = "default"
  source_ranges = [var.ip_administrateurs]
  target_tags   = ["${var.projet}-app"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_instance" "app" {
  count        = var.nombre_serveurs
  name         = "${var.projet}-app-${count.index + 1}"
  machine_type = var.type_serveur
  tags         = ["${var.projet}-app"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 30
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata = {
    ssh-keys = "deploiement:${var.cle_ssh_publique}"
  }

  metadata_startup_script = file("${path.module}/../commun/installer-serveur.sh")
}

resource "google_sql_database_instance" "base" {
  name                = "${var.projet}-base"
  database_version    = "«version_gcp»"
  region              = var.region
  deletion_protection = true

  settings {
    tier              = var.type_base
    availability_type = var.haute_disponibilite ? "REGIONAL" : "ZONAL"
    disk_size         = var.stockage_go
    disk_type         = "PD_SSD"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = «pitr_postgresql»
      binary_log_enabled             = «binlog_mysql»
    }

    # Connexions chiffrées, uniquement depuis les serveurs d'application
    ip_configuration {
      ipv4_enabled = true
      ssl_mode     = "ENCRYPTED_ONLY"

      dynamic "authorized_networks" {
        for_each = google_compute_instance.app
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.network_interface[0].access_config[0].nat_ip
        }
      }
    }
  }
}

resource "google_sql_database" "application" {
  name     = var.nom_base
  instance = google_sql_database_instance.base.name
}

resource "google_sql_user" "application" {
  name     = var.utilisateur_base
  instance = google_sql_database_instance.base.name
  password = var.mot_de_passe_base
}
