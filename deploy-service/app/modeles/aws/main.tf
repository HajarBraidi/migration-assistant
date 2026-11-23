# Infrastructure AWS de «nom_projet» : serveurs d'application + base de données gérée (Amazon RDS).
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Réseau par défaut du compte (suffisant pour démarrer ; un réseau dédié est recommandé ensuite)
data "aws_vpc" "defaut" {
  default = true
}

data "aws_subnets" "defaut" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.defaut.id]
  }
}

# Image Ubuntu 24.04 LTS officielle (Canonical)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_key_pair" "deploiement" {
  key_name   = "${var.projet}-deploiement"
  public_key = var.cle_ssh_publique
}

# Pare-feu des serveurs : web pour tous, SSH seulement depuis l'adresse des administrateurs
resource "aws_security_group" "app" {
  name   = "${var.projet}-app"
  vpc_id = data.aws_vpc.defaut.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH administrateurs"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ip_administrateurs]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Pare-feu de la base : accessible uniquement depuis les serveurs d'application
resource "aws_security_group" "base" {
  name   = "${var.projet}-base"
  vpc_id = data.aws_vpc.defaut.id

  ingress {
    description     = "Base de données depuis les serveurs"
    from_port       = «port_base»
    to_port         = «port_base»
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

resource "aws_instance" "app" {
  count                  = var.nombre_serveurs
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.type_serveur
  key_name               = aws_key_pair.deploiement.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id              = element(data.aws_subnets.defaut.ids, count.index)
  user_data              = file("${path.module}/../commun/installer-serveur.sh")

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name   = "${var.projet}-app-${count.index + 1}"
    Projet = var.projet
  }
}

resource "aws_db_subnet_group" "base" {
  name       = "${var.projet}-base"
  subnet_ids = data.aws_subnets.defaut.ids
}

resource "aws_db_instance" "base" {
  identifier             = "${var.projet}-base"
  engine                 = "«moteur_aws»"
  engine_version         = "«version_aws»"
  instance_class         = var.type_base
  allocated_storage      = var.stockage_go
  storage_type           = "gp3"
  storage_encrypted      = true
  db_name                = var.nom_base
  username               = var.utilisateur_base
  password               = var.mot_de_passe_base
  multi_az               = var.haute_disponibilite
  db_subnet_group_name   = aws_db_subnet_group.base.name
  vpc_security_group_ids = [aws_security_group.base.id]
  publicly_accessible    = false

  # Sauvegardes quotidiennes conservées 7 jours, protection contre la suppression
  backup_retention_period   = 7
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.projet}-instantane-final"

  tags = {
    Projet = var.projet
  }
}
