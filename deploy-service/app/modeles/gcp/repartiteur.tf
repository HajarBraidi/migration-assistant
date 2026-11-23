# Répartiteur de charge HTTP : distribue le trafic entre les machines et écarte une machine en panne.
resource "google_compute_instance_group" "app" {
  name      = "${var.projet}-app"
  zone      = var.zone
  instances = google_compute_instance.app[*].self_link

  named_port {
    name = "http"
    port = 80
  }
}

resource "google_compute_health_check" "http" {
  name = "${var.projet}-sante"

  http_health_check {
    port         = 80
    request_path = "/"
  }
}

resource "google_compute_backend_service" "app" {
  name                  = "${var.projet}-app"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  health_checks         = [google_compute_health_check.http.id]

  backend {
    group = google_compute_instance_group.app.id
  }
}

resource "google_compute_url_map" "app" {
  name            = "${var.projet}-routes"
  default_service = google_compute_backend_service.app.id
}

resource "google_compute_target_http_proxy" "app" {
  name    = "${var.projet}-proxy"
  url_map = google_compute_url_map.app.id
}

resource "google_compute_global_address" "app" {
  name = "${var.projet}-ip"
}

resource "google_compute_global_forwarding_rule" "http" {
  name                  = "${var.projet}-http"
  target                = google_compute_target_http_proxy.app.id
  port_range            = "80"
  ip_address            = google_compute_global_address.app.address
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

output "adresse_repartiteur" {
  description = "Adresse publique de l'application (à utiliser dans le DNS)"
  value       = google_compute_global_address.app.address
}
