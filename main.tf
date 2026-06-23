terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }
}

# DynamoDB Token Vault for Ephemeral Token Mapping
resource "aws_dynamodb_table" "token_vault" {
  name         = "${var.project_name}-token-vault-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "SessionId"

  attribute {
    name = "SessionId"
    type = "S"
  }

  # Strict security requirement for financial data: Auto-deletion after 5 minutes
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false # Disabled for a transient, temporary caching vault to optimize cost
  }
}