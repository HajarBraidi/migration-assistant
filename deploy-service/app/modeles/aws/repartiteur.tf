# Répartiteur de charge : distribue le trafic entre les serveurs et écarte un serveur en panne.
resource "aws_lb" "app" {
  name               = "${var.projet}-lb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.app.id]
  subnets            = data.aws_subnets.defaut.ids
}

resource "aws_lb_target_group" "app" {
  name     = "${var.projet}-app"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.defaut.id

  health_check {
    path    = "/"
    matcher = "200-399"
  }
}

resource "aws_lb_target_group_attachment" "app" {
  count            = var.nombre_serveurs
  target_group_arn = aws_lb_target_group.app.arn
  target_id        = aws_instance.app[count.index].id
  port             = 80
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

output "adresse_repartiteur" {
  description = "Adresse publique de l'application (à utiliser dans le DNS)"
  value       = aws_lb.app.dns_name
}
