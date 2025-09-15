variable "project_name" { type = string default = "fraud" }
variable "aws_region" { type = string default = "us-east-1" }

# Networking (use existing VPC/Subnets)
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }

# S3 lifecycle
variable "image_ttl_days" { type = number default = 30 }

# Dynamo tables
variable "cases_table_name" { type = string default = "fraud_cases" }
variable "events_table_name" { type = string default = "fraud_events" }

# ECR repos
variable "api_ecr_repo" { type = string default = "fraud-api" }
variable "worker_ecr_repo" { type = string default = "fraud-worker" }

# ECS images (tags provided by CI)
variable "api_image" { type = string default = "" }
variable "worker_image" { type = string default = "" }

# Secrets
variable "api_key_secret_name" { type = string default = "fraud_api_key" }

