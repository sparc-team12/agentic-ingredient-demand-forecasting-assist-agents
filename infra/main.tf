terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # bucket is deliberately not set here — {{TFSTATE_BUCKET_NAME}} is still an
  # unresolved organizational fact (DEC-007). Pass it at init time instead:
  #   terraform init -backend-config="bucket=<final-bucket-name>"
  backend "s3" {
    key            = "terraform/prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ingredient-forecast-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}

# =============================================================================
# Variables (defaults below match prod — the only environment that exists —
# so `terraform apply` needs no -var-file; override with -var if ever needed)
# =============================================================================

variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Mandatory tags applied to every resource (cloud_platform_standards.tagging.mandatory)."
  type        = map(string)
  default = {
    Project     = "agentic-ingredient-demand-forecasting-assist-agents"
    Environment = "prod"
    ManagedBy   = "terraform"
    Owner       = "{{OWNER}}"
    CostCenter  = "{{COST_CENTER}}"
  }
}

# ---- Networking ----

variable "vpc_name" {
  description = "Name applied to the VPC."
  type        = string
  default     = "ingredient-forecast-vpc-prod"
}

variable "vpc_cidr_block" {
  description = "IPv4 CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_name" {
  description = "Name applied to the (sole) subnet."
  type        = string
  default     = "ingredient-forecast-subnet-public-prod"
}

variable "public_subnet_cidr_block" {
  description = "IPv4 CIDR block for the subnet."
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "Availability zone for the subnet."
  type        = string
  default     = "us-east-1a"
}

# ---- Application instance ----

variable "app_name" {
  description = "Name applied to the instance and derived resources (SG, IAM role, log group defaults)."
  type        = string
  default     = "ingredient-forecast-app-prod"
}

variable "app_ami_id" {
  description = "AMI ID for the instance. No safe default — placeholder {{APP_AMI_ID}} (not stated in any input artifact; region/architecture/OS-patch-level specific)."
  type        = string
  default     = "{{APP_AMI_ID}}"
}

variable "app_instance_type" {
  description = "EC2 instance type. DEC-009: t3.micro — the LLM is now the external Gemini API (a Python process calling out over the internet), not a self-hosted model, so heavy local compute is no longer needed."
  type        = string
  default     = "t3.micro"
}

variable "app_root_volume_size_gb" {
  description = "Root EBS volume size, GiB."
  type        = number
  default     = 20
}

variable "app_root_volume_type" {
  description = "Root EBS volume type."
  type        = string
  default     = "gp3"
}

variable "app_user_data" {
  description = "Optional bootstrap script for the instance (e.g. installing the app and the Python/Gemini-API integration). Application/service bootstrapping content itself is out of scope of this Terraform generation."
  type        = string
  default     = null
}

# ---- Persistent data volume (SQLite) ----

variable "data_volume_name" {
  description = "Name applied to the SQLite persistent data volume."
  type        = string
  default     = "ingredient-forecast-sqlite-vol-prod"
}

variable "data_volume_size_gb" {
  description = "SQLite data volume size, GiB."
  type        = number
  default     = 20
}

variable "data_volume_type" {
  description = "SQLite data volume type."
  type        = string
  default     = "gp3"
}

variable "data_volume_device_name" {
  description = "Device name to expose the data volume as on the instance."
  type        = string
  default     = "/dev/xvdf"
}

# ---- Logging ----

variable "log_group_name" {
  description = "CloudWatch Log Group name."
  type        = string
  default     = "ingredient-forecast-logs-prod"
}

variable "log_retention_days" {
  description = "CloudWatch log retention period, in days."
  type        = number
  default     = 30
}

# =============================================================================
# Networking
# One VPC, one public subnet. No private subnet: per DEC-008/DEC-009 there is
# only one instance and the LLM is now the Gemini API (external, called over
# the internet — not self-hosted), so nothing needs network isolation.
# =============================================================================

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, { Name = var.vpc_name })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.vpc_name}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr_block
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(var.tags, { Name = var.public_subnet_name })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.public_subnet_name}-rt" })
}

resource "aws_route" "igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id              = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# =============================================================================
# Security group
# Inbound HTTP only (no TLS in v1, security-architecture.md §7). Outbound is
# open — the app now calls the Gemini API over the internet (DEC-009/DEC-010),
# so egress can't be locked down to VPC-only the way the old self-hosted-LLM
# design was. [TBD — security-architecture.md marker 9: consider scoping
# egress to Gemini's actual endpoint(s) once that review clears.]
# =============================================================================

resource "aws_security_group" "app" {
  name        = "${var.app_name}-sg"
  description = "Application instance — inbound HTTP from the internet; outbound open for Gemini API calls"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound (includes Gemini API calls)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.app_name}-sg" })

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# Logging + IAM
# =============================================================================

resource "aws_cloudwatch_log_group" "app" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_iam_role" "app" {
  name = "${var.app_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "EC2AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "app_logs" {
  name = "${var.app_name}-cloudwatch-logs"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "WriteApplicationLogs"
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
      ]
      Resource = "${aws_cloudwatch_log_group.app.arn}:*"
    }]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.app_name}-instance-profile"
  role = aws_iam_role.app.name

  tags = var.tags
}

# =============================================================================
# Application instance
# One instance (t3.micro, per DEC-009). It runs the app AND calls the Gemini
# API for AI functionality (a Python process using a Gemini API key stored in
# the .env file — security-architecture.md §6) instead of self-hosting an
# LLM, which is why this no longer needs the heavier sizing DEC-008 carried
# over from the old self-hosted-Gemma instance.
# =============================================================================

resource "aws_instance" "app" {
  ami                         = var.app_ami_id
  instance_type               = var.app_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = false # a dedicated Elastic IP is associated below instead
  user_data                   = var.app_user_data

  root_block_device {
    volume_size = var.app_root_volume_size_gb
    volume_type = var.app_root_volume_type
    encrypted   = false # security-architecture.md §7: no at-rest encryption required for v1

    tags = merge(var.tags, { Name = "${var.app_name}-root" })
  }

  tags = merge(var.tags, { Name = var.app_name })

  lifecycle {
    ignore_changes = [ami] # allows an operational AMI refresh without forcing a Terraform-driven replace on every plan
  }
}

resource "aws_ebs_volume" "data" {
  availability_zone = aws_instance.app.availability_zone
  size              = var.data_volume_size_gb
  type              = var.data_volume_type
  encrypted         = false # security-architecture.md §7: no at-rest encryption required for v1

  tags = merge(var.tags, { Name = var.data_volume_name })
}

resource "aws_volume_attachment" "data" {
  device_name = var.data_volume_device_name
  volume_id   = aws_ebs_volume.data.id
  instance_id = aws_instance.app.id
}

resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id

  tags = merge(var.tags, { Name = "${var.app_name}-eip" })
}

# =============================================================================
# Outputs
# =============================================================================

output "instance_id" {
  description = "Application instance ID."
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "Elastic IP address of the instance (browser ingress point)."
  value       = aws_eip.app.public_ip
}

output "log_group_name" {
  description = "CloudWatch Log Group name."
  value       = aws_cloudwatch_log_group.app.name
}

output "data_volume_id" {
  description = "SQLite persistent data volume ID."
  value       = aws_ebs_volume.data.id
}
