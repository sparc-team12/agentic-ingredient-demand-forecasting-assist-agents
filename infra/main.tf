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
    key          = "terraform/prod/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true # S3 native locking (Terraform >= 1.10) — replaces the deprecated dynamodb_table param, no DynamoDB table needed
    encrypt      = true
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

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
    Owner       = "sparc-team12"
    CostCenter  = "unassigned"
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
  description = "AMI ID for the instance. Ubuntu Server 26.04 LTS, x86_64, us-east-1 (matches t3.micro's architecture — the Arm variant of this AMI would not boot on a t3 instance family)."
  type        = string
  default     = "ami-0b6d9d3d33ba97d99"
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
# GitHub Actions OIDC — NOT managed by this Terraform config (DEC-019). The
# GitHub Actions IAM role (github-terraform-role) and its trust policy were
# created manually in the IAM console instead. Terraform does not define an
# aws_iam_openid_connect_provider or aws_iam_role for this here on purpose —
# AWS allows only one OIDC provider per URL per account, so a Terraform-owned
# one would conflict with the manually-created setup. If you ever want this
# brought under Terraform management, the manually-created role/provider
# would need to be imported (`terraform import`), not recreated from scratch.
# =============================================================================

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

# CKV2_AWS_11: VPC Flow Logs — no record of network traffic existed before
# this. Uses the same CMK as the app log group (aws_kms_key.logs, defined
# below under Logging + IAM).
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/vpc/${var.vpc_name}/flow-logs"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.logs.arn

  tags = var.tags
}

resource "aws_iam_role" "vpc_flow_logs" {
  name = "${var.vpc_name}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "VPCFlowLogsAssumeRole"
      Effect    = "Allow"
      Principal = { Service = "vpc-flow-logs.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "vpc_flow_logs" {
  name = "${var.vpc_name}-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "WriteFlowLogs"
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
      ]
      Resource = "${aws_cloudwatch_log_group.vpc_flow_logs.arn}:*"
    }]
  })
}

resource "aws_flow_log" "vpc" {
  vpc_id               = aws_vpc.this.id
  traffic_type         = "ALL"
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs.arn
  iam_role_arn         = aws_iam_role.vpc_flow_logs.arn

  tags = merge(var.tags, { Name = "${var.vpc_name}-flow-logs" })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.vpc_name}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr_block
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false # CKV_AWS_130: no behavior change — aws_instance.app already sets associate_public_ip_address=false and gets its public address from the dedicated aws_eip.app instead

  tags = merge(var.tags, { Name = var.public_subnet_name })
}

# CKV2_AWS_12: lock down the auto-created default security group every VPC
# gets — nothing in this stack references it (aws_security_group.app is used
# explicitly instead), so emptying its rules has no functional effect.
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.vpc_name}-default-sg-locked-down" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.public_subnet_name}-rt" })
}

resource "aws_route" "igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# =============================================================================
# Security group
# Inbound HTTP only (no TLS in v1, security-architecture.md §7). Outbound is
# scoped to HTTPS only (CKV_AWS_382 — resolves security-architecture.md §8's
# open egress-scoping question, marker 9): the Gemini API is HTTPS-only, and
# it's the only outbound dependency this app has (DEC-009/DEC-010). If OS
# package installs during boot need plain HTTP (port 80) too, add a second
# egress rule for it — most current apt/yum mirrors are HTTPS-only already.
# =============================================================================

resource "aws_security_group" "app" {
  name        = "${var.app_name}-sg"
  description = "Application instance - inbound HTTP from the internet; outbound HTTPS only (Gemini API)"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "HTTPS (Gemini API)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
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

# CKV_AWS_158: customer-managed key so log groups aren't left on the default
# AWS-owned key. One key, shared by both log groups below (app + VPC flow logs).
resource "aws_kms_key" "logs" {
  description             = "CMK for CloudWatch Logs encryption (application + VPC flow logs)"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowRootAccountAdmin"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudWatchLogsUse"
        Effect    = "Allow"
        Principal = { Service = "logs.${var.region}.amazonaws.com" }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*",
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
          }
        }
      },
    ]
  })

  tags = var.tags
}

resource "aws_kms_alias" "logs" {
  name          = "alias/${var.app_name}-logs"
  target_key_id = aws_kms_key.logs.key_id
}

resource "aws_cloudwatch_log_group" "app" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days # CKV_AWS_338 wants >=365; 30 days is tf-coding-inputs.md assumption #10 (approved) — no compliance driver found (security-architecture.md §11), low-cost default for a low-traffic internal tool
  kms_key_id        = aws_kms_key.logs.arn

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
  # CKV_AWS_8 (root volume unencrypted) is intentional — security-architecture.md
  # §7 marker 4 (RESOLVED): explicit human decision, "no at-rest encryption
  # required for v1." Suppressed via the pipeline's Checkov skip_check input
  # (.github/workflows/terraform.yml), not an inline comment, since the inline
  # form did not reliably take effect in CI.
  ami                         = var.app_ami_id
  instance_type               = var.app_instance_type
  ebs_optimized               = true # CKV_AWS_135 — always true for t3/current-gen (Nitro) instances regardless; set explicitly rather than relying on the implicit default
  monitoring                  = true # CKV_AWS_126 — 1-minute metrics instead of the 5-minute default; small added cost, real value for spotting t3.micro CPU-credit exhaustion early
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = false # a dedicated Elastic IP is associated below instead
  user_data                   = var.app_user_data

  metadata_options {
    http_tokens   = "required" # CKV_AWS_79: require IMDSv2 — pure hardening, no functional impact for well-behaved instance metadata calls
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_size = var.app_root_volume_size_gb
    volume_type = var.app_root_volume_type
    encrypted   = false # security-architecture.md §7: no at-rest encryption required for v1 (marker 4) — see CKV_AWS_8 note above

    tags = merge(var.tags, { Name = "${var.app_name}-root" })
  }

  tags = merge(var.tags, { Name = var.app_name })

  lifecycle {
    ignore_changes = [ami] # allows an operational AMI refresh without forcing a Terraform-driven replace on every plan
  }
}

resource "aws_ebs_volume" "data" {
  # CKV2_AWS_2 / CKV_AWS_3 / CKV_AWS_189 (unencrypted EBS) are intentional —
  # security-architecture.md §7 marker 4 (RESOLVED): explicit human decision,
  # "no at-rest encryption required for v1." Suppressed via the pipeline's
  # Checkov skip_check input (.github/workflows/terraform.yml), not an inline
  # comment, since the inline form did not reliably take effect in CI.
  availability_zone = aws_instance.app.availability_zone
  size              = var.data_volume_size_gb
  type              = var.data_volume_type
  encrypted         = false # security-architecture.md §7: no at-rest encryption required for v1 (marker 4)

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
